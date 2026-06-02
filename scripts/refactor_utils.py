#!/usr/bin/env python3
"""
共享的重构工具模块
提供通用的文件处理、输出格式化和错误处理功能
"""

import sys
import io
from pathlib import Path
from typing import Callable, List, Tuple, Optional


def setup_utf8_output():
    """配置 stdout 为 UTF-8 编码"""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def process_files(
    files: List[Path],
    processor: Callable[[Path], Tuple[bool, str]],
    title: str,
    base_dir: Optional[Path] = None
) -> Tuple[int, int]:
    """
    使用给定的处理器函数处理多个文件

    Args:
        files: 要处理的文件列表
        processor: 处理函数，返回 (是否更新, 消息)
        title: 任务标题
        base_dir: 基础目录，用于显示相对路径

    Returns:
        (更新数量, 错误数量)
    """
    setup_utf8_output()

    if base_dir is None:
        base_dir = Path.cwd()

    print(f"开始{title}...")
    print("=" * 60)

    updated_count = 0
    error_count = 0
    skipped_count = 0

    for filepath in files:
        if not filepath.exists():
            print(f"[SKIP] 文件不存在: {filepath.relative_to(base_dir)}")
            skipped_count += 1
            continue

        try:
            updated, message = processor(filepath)

            if updated:
                print(f"[OK] {filepath.relative_to(base_dir)}: {message}")
                updated_count += 1
            elif "错误" in message:
                print(f"[ERROR] {filepath.relative_to(base_dir)}: {message}")
                error_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"[ERROR] {filepath.relative_to(base_dir)}: {str(e)}")
            error_count += 1

    print("=" * 60)
    print(f"完成！更新了 {updated_count} 个文件")
    if skipped_count > 0:
        print(f"跳过了 {skipped_count} 个文件")
    if error_count > 0:
        print(f"错误: {error_count} 个文件")

    return updated_count, error_count


def read_file_safe(filepath: Path) -> Optional[str]:
    """安全地读取文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件失败 {filepath}: {e}")
        return None


def write_file_safe(filepath: Path, content: str) -> bool:
    """安全地写入文件内容"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"写入文件失败 {filepath}: {e}")
        return False
