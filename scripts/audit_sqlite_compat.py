#!/usr/bin/env python3
"""
SQLite 兼容性审计脚本

扫描所有 .py 文件，检测可能不兼容低版本 SQLite 的 SQLAlchemy API 用法：

1. .returning() — SQLite 3.35+ 才支持
2. func.row_number() / func.rank() / func.dense_rank() — SQLite 3.25+ 才支持（窗口函数）
3. over() — 窗口函数语法
4. INSERT ... ON CONFLICT — SQLite 3.24+ 才支持 (UPSERT)

使用方法：
    python scripts/audit_sqlite_compat.py [--verbose]
"""

import argparse
import os
import re
import sys
import tokenize
import io
from pathlib import Path
from typing import NamedTuple


class Finding(NamedTuple):
    file: str
    line: int
    column: int
    pattern: str
    code: str
    severity: str  # "ERROR" or "WARNING"


# 需要检测的模式列表
# 注意：对于 .returning() 等 SQLAlchemy API，使用更严格的正则确保不在字符串内匹配
PATTERNS = [
    # .returning() — SQLite 3.35+ 才支持（仅匹配方法调用，不匹配字符串中的文本）
    (
        re.compile(r"(?<!['\"#])\.returning\s*\("),
        "ERROR",
        ".returning() — SQLite 3.35+ 才支持 RETURNING 子句，低版本会抛 SyntaxError",
    ),
    # 窗口函数
    (
        re.compile(r"func\.(row_number|rank|dense_rank|ntile|lead|lag|first_value|last_value|nth_value)\s*\("),
        "WARNING",
        "func.row_number()/rank()/etc — SQLite 3.25+ 才支持窗口函数",
    ),
    # .over() — 窗口函数语法（排除字符串中的用法）
    (
        re.compile(r"(?<!['\"#])\.over\s*\("),
        "WARNING",
        ".over() — 窗口函数语法，SQLite 3.25+ 才支持",
    ),
    # ON CONFLICT (upsert)
    (
        re.compile(r"on_conflict\s*\("),
        "WARNING",
        "on_conflict() — SQLite 3.24+ 才支持 UPSERT",
    ),
    # 原始 SQL 中的 RETURNING（仅匹配 SQL 上下文：text() 或 execute() 中）
    (
        re.compile(r'text\s*\(\s*["\'].*?\bRETURNING\s+', re.IGNORECASE | re.DOTALL),
        "WARNING",
        "原始 SQL text() 中的 RETURNING 子句 — SQLite 3.35+ 才支持",
    ),
    # 原始 SQL 中的窗口函数
    (
        re.compile(r'\b(ROW_NUMBER|RANK|DENSE_RANK)\s*\(\s*\)\s+OVER\b', re.IGNORECASE),
        "WARNING",
        "原始 SQL 窗口函数 — SQLite 3.25+ 才支持",
    ),
    # JSON 函数 (SQLite 3.9+)
    (
        re.compile(r"func\.json_extract\s*\("),
        "INFO",
        "func.json_extract() — SQLite 3.9+ 才支持 JSON 函数",
    ),
]

# 排除的目录
EXCLUDE_DIRS = {
    ".venv", "node_modules", "__pycache__", ".git", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", "tests",
    "frontend", "electron", "docs", "resources", "artifacts",
    ".arts", ".agents", ".context", ".gstack", ".workbuddy", ".husky",
    ".github", ".claude", ".pre-commit-cache",
}

# 排除的文件
EXCLUDE_FILES = {
    "audit_sqlite_compat.py",  # 自身
}


def _get_string_ranges(content: str) -> list[tuple[int, int, int]]:
    """使用 tokenize 模块获取所有字符串字面量的位置范围。
    返回 [(start_line, start_col, end_line), ...]
    """
    string_ranges = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
        for tok in tokens:
            if tok.type == tokenize.STRING:
                string_ranges.append((tok.start[0], tok.start[1], tok.end[0]))
    except (tokenize.TokenizeError, IndentationError, SyntaxError):
        pass
    return string_ranges


def _is_in_string(line_no: int, col: int, string_ranges: list[tuple[int, int, int]]) -> bool:
    """检查指定位置是否在字符串字面量内。"""
    for start_line, start_col, end_line in string_ranges:
        if start_line == line_no and col >= start_col:
            if end_line > line_no or (end_line == line_no):
                return True
        elif start_line < line_no <= end_line:
            return True
    return False


def scan_file(filepath: Path) -> list[Finding]:
    """扫描单个文件，返回所有发现。"""
    findings: list[Finding] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    # 获取所有字符串字面量的位置范围，用于排除字符串内的误匹配
    string_ranges = _get_string_ranges(content)

    for line_no, line in enumerate(content.splitlines(), 1):
        # 跳过注释行
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        for pattern, severity, description in PATTERNS:
            for match in pattern.finditer(line):
                col = match.start() + 1

                # 检查是否在字符串字面量内
                if _is_in_string(line_no, col, string_ranges):
                    continue

                # 获取匹配的代码片段
                code_snippet = line.strip()
                if len(code_snippet) > 120:
                    code_snippet = code_snippet[:120] + "..."
                findings.append(Finding(
                    file=str(filepath),
                    line=line_no,
                    column=col,
                    pattern=description,
                    code=code_snippet,
                    severity=severity,
                ))

    return findings


def scan_directory(root_dir: Path) -> list[Finding]:
    """递归扫描目录，返回所有发现。"""
    all_findings: list[Finding] = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 过滤排除目录
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for filename in filenames:
            if filename in EXCLUDE_FILES:
                continue
            if not filename.endswith(".py"):
                continue

            filepath = Path(dirpath) / filename
            findings = scan_file(filepath)
            all_findings.extend(findings)

    return all_findings


def main():
    parser = argparse.ArgumentParser(description="SQLite 兼容性审计脚本")
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="显示所有发现（包括 INFO 级别）"
    )
    parser.add_argument(
        "--root", "-r", default=".",
        help="扫描根目录（默认当前目录）"
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"错误：目录不存在: {root}")
        sys.exit(1)

    print(f"扫描目录: {root}")
    print("-" * 80)

    findings = scan_directory(root)

    # 按严重度过滤
    severity_order = {"ERROR": 0, "WARNING": 1, "INFO": 2}
    if not args.verbose:
        findings = [f for f in findings if f.severity in ("ERROR", "WARNING")]

    # 按文件、行号排序
    findings.sort(key=lambda f: (f.file, f.line))

    if not findings:
        print("✅ 未发现 SQLite 兼容性问题")
        sys.exit(0)

    # 按严重度分组输出
    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARNING"]
    infos = [f for f in findings if f.severity == "INFO"]

    if errors:
        print(f"\n🔴 ERROR ({len(errors)} 个) — 低版本 SQLite 必定报错:")
        for f in errors:
            print(f"  {f.file}:{f.line}:{f.column}")
            print(f"    {f.pattern}")
            print(f"    {f.code}")
            print()

    if warnings:
        print(f"\n🟡 WARNING ({len(warnings)} 个) — 可能不兼容低版本 SQLite:")
        for f in warnings:
            print(f"  {f.file}:{f.line}:{f.column}")
            print(f"    {f.pattern}")
            print(f"    {f.code}")
            print()

    if args.verbose and infos:
        print(f"\n🔵 INFO ({len(infos)} 个) — 需要注意的 API:")
        for f in infos:
            print(f"  {f.file}:{f.line}:{f.column}")
            print(f"    {f.pattern}")
            print(f"    {f.code}")
            print()

    print("-" * 80)
    print(f"总计: {len(errors)} 错误, {len(warnings)} 警告" +
          (f", {len(infos)} 信息" if args.verbose else ""))

    # 有 ERROR 则退出码 1
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
