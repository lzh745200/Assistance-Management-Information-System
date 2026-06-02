#!/usr/bin/env python3
"""
权限问题全面检测脚本
检测系统中所有可能存在的权限相关问题
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# 问题模式定义
PATTERNS = [
    {
        "name": "未检查超级管理员的组织权限判断",
        "pattern": r"if\s+.*organization_id\s+is\s+None:.*\n.*(?!is_superuser|super_admin)",
        "severity": "HIGH",
        "description": "当 organization_id 为 None 时，未检查用户是否为超级管理员"
    },
    {
        "name": "直接使用 organization_id 而不检查 None",
        "pattern": r"current_user\.organization_id(?!\s+is\s+None|\s+or)",
        "severity": "MEDIUM",
        "description": "直接使用 organization_id 可能导致 None 值错误"
    },
    {
        "name": "权限错误提示不友好",
        "pattern": r'HTTPException.*403.*detail\s*=\s*["\'](?!.*请|.*联系)',
        "severity": "LOW",
        "description": "403 错误提示不够友好，缺少解决方案指引"
    },
    {
        "name": "未处理未绑定组织的用户",
        "pattern": r"getattr\(current_user,\s*['\"]org(?:anization)?_id['\"].*\)(?!\s+or\s+getattr)",
        "severity": "MEDIUM",
        "description": "获取组织ID时未提供回退机制"
    }
]

def scan_file(file_path: Path) -> List[Tuple[str, int, str, str]]:
    """
    扫描单个文件

    Returns:
        List of (pattern_name, line_number, line_content, severity)
    """
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

            for pattern_def in PATTERNS:
                pattern = pattern_def["pattern"]
                name = pattern_def["name"]
                severity = pattern_def["severity"]

                # 多行匹配
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    # 找到匹配的行号
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1].strip()

                    issues.append((name, line_num, line_content, severity))

    except Exception as e:
        print(f"  ⚠ 扫描文件失败: {e}")

    return issues

def scan_directory(directory: Path, extensions: List[str] = ['.py']) -> dict:
    """
    扫描目录

    Returns:
        Dict of {file_path: [(pattern_name, line_number, line_content, severity), ...]}
    """
    results = {}

    for ext in extensions:
        for file_path in directory.rglob(f'*{ext}'):
            # 跳过虚拟环境和测试文件
            if '.venv' in str(file_path) or '__pycache__' in str(file_path):
                continue

            issues = scan_file(file_path)
            if issues:
                results[file_path] = issues

    return results

def print_results(results: dict):
    """打印扫描结果"""
    if not results:
        print("\n[OK] 未发现权限相关问题")
        return

    print(f"\n[WARNING] 发现 {len(results)} 个文件存在潜在问题:\n")

    total_high = 0
    total_medium = 0
    total_low = 0

    for file_path, issues in results.items():
        print(f"\n[FILE] {file_path}")
        print("=" * 80)

        for name, line_num, line_content, severity in issues:
            if severity == "HIGH":
                icon = "[HIGH]"
                total_high += 1
            elif severity == "MEDIUM":
                icon = "[MEDIUM]"
                total_medium += 1
            else:
                icon = "[LOW]"
                total_low += 1

            print(f"{icon} {name}")
            print(f"   Line {line_num}: {line_content[:100]}")
            print()

    print("\n" + "=" * 80)
    print(f"Summary: HIGH {total_high} | MEDIUM {total_medium} | LOW {total_low}")
    print("=" * 80)

def main():
    print("=" * 80)
    print("Permission Issues Detection")
    print("=" * 80)

    # 扫描后端代码
    backend_dir = Path("backend/app")
    if not backend_dir.exists():
        print(f"[ERROR] Directory not found: {backend_dir}")
        return

    print(f"\n[SCAN] Scanning directory: {backend_dir}")
    results = scan_directory(backend_dir)

    print_results(results)

    # 生成修复建议
    if results:
        print("\n[SUGGESTIONS]:")
        print("1. Check all organization_id == None cases, ensure superuser check")
        print("2. Provide friendly error messages with solutions")
        print("3. Add fallback mechanisms for organization_id retrieval")
        print("4. Guide unbound users with clear instructions")

if __name__ == "__main__":
    main()
