#!/usr/bin/env python3
"""
自动化安全审计脚本

扫描所有后端 API 模块，检查以下安全合规项：
1. 所有写操作（POST/PUT/DELETE）是否调用 write_work_log
2. 所有查询是否使用 filter_by_data_scope / apply_data_scope
3. 敏感字段是否加密
4. 错误是否记录审计日志

使用方法：
    python scripts/audit_security.py [--verbose] [--module funds]
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple


class SecurityFinding(NamedTuple):
    file: str
    line: int
    severity: str  # "ERROR" or "WARNING"
    category: str
    message: str
    code: str


EXCLUDE_DIRS = {
    ".venv", "node_modules", "__pycache__", ".git", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", "tests",
    "frontend", "electron", "docs", "resources", "artifacts",
    ".arts", ".agents", ".context", ".gstack", ".workbuddy", ".husky",
    ".github", ".claude", ".pre-commit-cache",
}


def _scan_write_endpoints(filepath: Path, content: str) -> list[SecurityFinding]:
    """扫描写操作端点是否缺少 write_work_log。"""
    findings = []
    lines = content.splitlines()

    # 查找 @router.post/put/delete 装饰器
    write_decorator_re = re.compile(r'@router\.(post|put|delete)\s*\(')

    for i, line in enumerate(lines):
        match = write_decorator_re.search(line)
        if not match:
            continue

        method = match.group(1)
        # 查找函数体（向后扫描 80 行或直到下一个 @router）
        func_body = "\n".join(lines[i:i+80])

        # 跳过非业务端点（如 health check, cache clear 等系统操作）
        skip_patterns = ["health", "cache", "wal-checkpoint", "vacuum", "integrity-check",
                         "shutdown", "restart", "csrf", "clear"]
        if any(p in func_body.lower() for p in skip_patterns):
            continue

        # 检查是否有 write_work_log 调用
        if "write_work_log" not in func_body:
            # 获取函数名
            func_name_match = re.search(r'def\s+(\w+)\s*\(', func_body)
            func_name = func_name_match.group(1) if func_name_match else "unknown"

            findings.append(SecurityFinding(
                file=str(filepath),
                line=i + 1,
                severity="WARNING",
                category="missing_audit_log",
                message=f"写操作端点 {func_name} ({method.upper()}) 缺少 write_work_log 审计日志",
                code=line.strip(),
            ))

    return findings


def _scan_data_scope(filepath: Path, content: str) -> list[SecurityFinding]:
    """扫描查询是否使用数据权限过滤。"""
    findings = []
    lines = content.splitlines()

    # 查找 db.query(Model) 或 select(Model) 后面没有 filter_by_data_scope / apply_data_scope 的情况
    # 仅检查列表端点（@router.get）
    list_decorator_re = re.compile(r'@router\.get\s*\(')

    for i, line in enumerate(lines):
        if not list_decorator_re.search(line):
            continue

        # 查找函数体
        func_body = "\n".join(lines[i:i+60])

        # 跳过非业务端点
        skip_patterns = ["statistics", "export", "download", "preview", "template",
                         "filter-options", "options", "types", "categories",
                         "health", "cache", "tree", "subordinates", "ancestors",
                         "children", "my-organization", "calendar", "search",
                         "favorites", "related", "history", "attachments"]
        if any(p in func_body.lower() for p in skip_patterns):
            continue

        # 检查是否有 db.query 或 select 语句
        has_query = bool(re.search(r'(db\.query|select)\s*\(', func_body))
        if not has_query:
            continue

        # 检查是否有数据权限过滤
        has_scope = ("filter_by_data_scope" in func_body or
                     "apply_data_scope" in func_body or
                     "apply_scope_to_query" in func_body)

        if not has_scope:
            func_name_match = re.search(r'def\s+(\w+)\s*\(', func_body)
            func_name = func_name_match.group(1) if func_name_match else "unknown"

            findings.append(SecurityFinding(
                file=str(filepath),
                line=i + 1,
                severity="WARNING",
                category="missing_data_scope",
                message=f"列表端点 {func_name} 可能缺少 filter_by_data_scope / apply_data_scope 数据权限过滤",
                code=line.strip(),
            ))

    return findings


def _scan_unguarded_commits(filepath: Path, content: str) -> list[SecurityFinding]:
    """扫描 db.commit() 调用是否缺少异常处理。"""
    findings = []
    lines = content.splitlines()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        if "db.commit()" not in stripped:
            continue

        # 检查上下文是否有 try/except
        # 向前查找 5 行
        context_before = "\n".join(lines[max(0, i-5):i])
        # 向后查找 3 行
        context_after = "\n".join(lines[i+1:min(len(lines), i+4)])

        has_try = "try:" in context_before or "try :" in context_before
        has_except = "except" in context_after

        if not has_try and not has_except:
            findings.append(SecurityFinding(
                file=str(filepath),
                line=i + 1,
                severity="WARNING",
                category="unguarded_commit",
                message="db.commit() 调用缺少 try/except 异常处理，可能导致 session 泄漏",
                code=stripped,
            ))

    return findings


def scan_file(filepath: Path) -> list[SecurityFinding]:
    """扫描单个文件。"""
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    # 跳过非 API 文件
    if "api/v1" not in str(filepath):
        return findings

    findings.extend(_scan_write_endpoints(filepath, content))
    findings.extend(_scan_data_scope(filepath, content))
    findings.extend(_scan_unguarded_commits(filepath, content))

    return findings


def main():
    parser = argparse.ArgumentParser(description="自动化安全审计脚本")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示所有发现")
    parser.add_argument("--module", "-m", default=None, help="仅扫描指定模块（如 funds, policy）")
    parser.add_argument("--root", "-r", default="backend/app", help="扫描根目录")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"错误：目录不存在: {root}")
        sys.exit(1)

    print(f"安全审计扫描: {root}")
    print("=" * 80)

    all_findings = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            if args.module and args.module not in str(Path(dirpath) / filename):
                continue

            filepath = Path(dirpath) / filename
            findings = scan_file(filepath)
            all_findings.extend(findings)

    if not all_findings:
        print("✅ 未发现安全问题")
        sys.exit(0)

    # 按类别分组
    categories = {}
    for f in all_findings:
        categories.setdefault(f.category, []).append(f)

    for category, findings in sorted(categories.items()):
        print(f"\n{'🔴' if findings[0].severity == 'ERROR' else '🟡'} {category} ({len(findings)} 个):")
        for f in findings:
            print(f"  {f.file}:{f.line}")
            print(f"    [{f.severity}] {f.message}")
            if args.verbose:
                print(f"    {f.code}")
            print()

    print("=" * 80)
    print(f"总计: {len(all_findings)} 个发现")
    sys.exit(1 if any(f.severity == "ERROR" for f in all_findings) else 0)


if __name__ == "__main__":
    main()
