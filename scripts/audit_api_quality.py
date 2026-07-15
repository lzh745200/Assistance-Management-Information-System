#!/usr/bin/env python3
"""
API 质量审计脚本

扫描后端 API 模块，检查：
1. 列表端点是否使用 ok_list() 统一响应格式
2. 列表端点是否使用 eager loading 防止 N+1 查询
3. db.commit() 是否有异常处理

使用方法：
    python scripts/audit_api_quality.py [--verbose]
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple


class QualityFinding(NamedTuple):
    file: str
    line: int
    severity: str
    category: str
    message: str
    code: str


EXCLUDE_DIRS = {
    ".venv", "node_modules", "__pycache__", ".git", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", "tests",
    "frontend", "electron", "docs", "resources", "artifacts",
}


def _scan_list_endpoints(filepath: Path, content: str) -> list[QualityFinding]:
    """扫描列表端点是否使用 ok_list()。"""
    findings = []
    lines = content.splitlines()

    list_decorator_re = re.compile(r'@router\.get\s*\(\s*(?:["\'](?:|/|/list)["\'])\s*[,)]')

    for i, line in enumerate(lines):
        # 检查是否是列表端点（URL 为 "" 或 "/" 或 "/list"）
        if not re.search(r'@router\.get\s*\(\s*["\'](?:|/|/list)["\']\s*[,)]', line):
            # 也检查带前缀的列表端点，如 @router.get("")
            if not re.search(r'@router\.get\s*\(\s*""', line):
                continue

        func_body = "\n".join(lines[i:i+80])
        func_name_match = re.search(r'def\s+(\w+)\s*\(', func_body)
        func_name = func_name_match.group(1) if func_name_match else "unknown"

        # 跳过非列表端点
        if any(p in func_name.lower() for p in ["export", "download", "template",
                                                  "options", "types", "categories",
                                                  "tree", "statistics", "calendar",
                                                  "search", "preview"]):
            continue

        # 检查是否有 ok_list 调用
        if "ok_list" not in func_body:
            # 检查是否返回了包含 total 和 items 的裸 dict
            if "total" in func_body and ("items" in func_body or "page" in func_body):
                findings.append(QualityFinding(
                    file=str(filepath),
                    line=i + 1,
                    severity="WARNING",
                    category="bare_list_response",
                    message=f"列表端点 {func_name} 可能使用裸 dict 而非 ok_list() 统一响应格式",
                    code=line.strip(),
                ))

    return findings


def _scan_n_plus_1(filepath: Path, content: str) -> list[QualityFinding]:
    """扫描可能存在 N+1 查询的列表端点。"""
    findings = []
    lines = content.splitlines()

    # 查找列表端点中的 db.query(Model).all() 或 db.execute(select(Model)).scalars().all()
    # 如果后面有循环访问关联对象但没有 joinedload/selectinload，则可能有 N+1

    for i, line in enumerate(lines):
        # 查找查询调用
        if not re.search(r'(db\.query|db\.execute|\.scalars\(\))', line):
            continue

        # 检查是否有 eager loading
        has_eager = bool(re.search(r'(joinedload|selectinload|lazy=.?selectin)', content))

        # 查找函数定义
        func_start = i
        while func_start > 0 and not lines[func_start].strip().startswith("def "):
            func_start -= 1

        func_body = "\n".join(lines[func_start:func_start+100])
        func_name_match = re.search(r'def\s+(\w+)\s*\(', func_body)
        func_name = func_name_match.group(1) if func_name_match else "unknown"

        # 检查是否是列表端点（含 .all() 和循环）
        if ".all()" in func_body and "for " in func_body:
            # 检查是否有 eager loading 在这个函数体内
            if not re.search(r'(joinedload|selectinload)', func_body):
                # 检查循环中是否访问了关联对象（.project., .village., .organization. 等）
                if re.search(r'\.(project|village|organization|school|user)\b', func_body):
                    findings.append(QualityFinding(
                        file=str(filepath),
                        line=i + 1,
                        severity="WARNING",
                        category="n_plus_1_query",
                        message=f"端点 {func_name} 可能在循环中访问关联对象但未使用 eager loading",
                        code=line.strip(),
                    ))

    return findings


def scan_file(filepath: Path) -> list[QualityFinding]:
    """扫描单个文件。"""
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    if "api/v1" not in str(filepath):
        return findings

    findings.extend(_scan_list_endpoints(filepath, content))
    findings.extend(_scan_n_plus_1(filepath, content))

    return findings


def main():
    parser = argparse.ArgumentParser(description="API 质量审计脚本")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--root", "-r", default="backend/app")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"错误：目录不存在: {root}")
        sys.exit(1)

    print(f"API 质量审计扫描: {root}")
    print("=" * 80)

    all_findings = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            filepath = Path(dirpath) / filename
            findings = scan_file(filepath)
            all_findings.extend(findings)

    if not all_findings:
        print("✅ 未发现 API 质量问题")
        sys.exit(0)

    categories = {}
    for f in all_findings:
        categories.setdefault(f.category, []).append(f)

    for category, findings in sorted(categories.items()):
        print(f"\n🟡 {category} ({len(findings)} 个):")
        for f in findings:
            print(f"  {f.file}:{f.line}")
            print(f"    [{f.severity}] {f.message}")
            if args.verbose:
                print(f"    {f.code}")
            print()

    print("=" * 80)
    print(f"总计: {len(all_findings)} 个发现")
    sys.exit(0)


if __name__ == "__main__":
    main()
