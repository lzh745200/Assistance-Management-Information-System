#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志清理脚本
功能：
- 清理超过指定天数的日志文件
- 压缩旧日志文件
- 显示日志目录统计信息
"""

import argparse
import gzip
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_log_files(log_dir: Path) -> List[Path]:
    """获取所有日志文件"""
    log_files = []
    for pattern in ["*.log", "*.log.*", "*.gz"]:
        log_files.extend(log_dir.glob(pattern))
    return sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)


def get_file_age(file_path: Path) -> timedelta:
    """获取文件年龄"""
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    return datetime.now() - mtime


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def compress_file(file_path: Path) -> Path:
    """压缩文件为 .gz 格式"""
    compressed_path = file_path.with_suffix(file_path.suffix + ".gz")

    with open(file_path, "rb") as f_in:
        with gzip.open(compressed_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # 删除原文件
    file_path.unlink()
    logger.info(f"已压缩: {file_path.name} -> {compressed_path.name}")
    return compressed_path


def cleanup_old_logs(log_dir: Path, days: int, compress: bool = True, dry_run: bool = False) -> Tuple[int, int]:
    """
    清理旧日志文件

    Args:
        log_dir: 日志目录
        days: 保留天数
        compress: 是否压缩旧日志
        dry_run: 试运行模式（不实际删除）

    Returns:
        (删除文件数, 释放空间字节数)
    """
    if not log_dir.exists():
        logger.warning(f"日志目录不存在: {log_dir}")
        return 0, 0

    cutoff_date = datetime.now() - timedelta(days=days)
    logger.info(f"清理 {cutoff_date.strftime('%Y-%m-%d')} 之前的日志文件...")

    deleted_count = 0
    freed_space = 0

    for log_file in get_log_files(log_dir):
        file_age = get_file_age(log_file)
        file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

        if file_mtime < cutoff_date:
            file_size = log_file.stat().st_size

            if dry_run:
                logger.info(f"[试运行] 将删除: {log_file.name} ({format_size(file_size)}, {file_age.days} 天前)")
            else:
                if compress and not log_file.suffix == ".gz":
                    # 压缩未压缩的文件
                    compressed_file = compress_file(log_file)
                    freed_space += file_size - compressed_file.stat().st_size
                else:
                    # 删除文件
                    log_file.unlink()
                    freed_space += file_size
                    logger.info(f"已删除: {log_file.name} ({format_size(file_size)}, {file_age.days} 天前)")

            deleted_count += 1

    return deleted_count, freed_space


def show_log_stats(log_dir: Path):
    """显示日志目录统计信息"""
    if not log_dir.exists():
        logger.warning(f"日志目录不存在: {log_dir}")
        return

    log_files = get_log_files(log_dir)

    if not log_files:
        logger.info("日志目录为空")
        return

    total_size = sum(f.stat().st_size for f in log_files)
    oldest_file = log_files[-1] if log_files else None
    newest_file = log_files[0] if log_files else None

    logger.info("=" * 60)
    logger.info("日志目录统计信息")
    logger.info("=" * 60)
    logger.info(f"目录: {log_dir}")
    logger.info(f"文件数量: {len(log_files)}")
    logger.info(f"总大小: {format_size(total_size)}")

    if oldest_file:
        age = get_file_age(oldest_file)
        logger.info(f"最旧文件: {oldest_file.name} ({age.days} 天前)")

    if newest_file:
        age = get_file_age(newest_file)
        logger.info(f"最新文件: {newest_file.name} ({age.days} 天前)")

    # 显示按日期分组的统计
    logger.info("\n按大小排序的前10个文件:")
    for i, log_file in enumerate(log_files[:10], 1):
        size = log_file.stat().st_size
        age = get_file_age(log_file)
        logger.info(f"{i:2d}. {log_file.name:40s} {format_size(size):>12s} ({age.days:3d} 天前)")

    logger.info("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="日志清理工具")
    parser.add_argument(
        "--log-dir",
        type=str,
        default="./logs",
        help="日志目录路径（默认: ./logs）"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="保留最近N天的日志（默认: 30天）"
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="不压缩旧日志，直接删除"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式，只显示将要删除的文件"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="仅显示统计信息，不执行清理"
    )

    args = parser.parse_args()
    log_dir = Path(args.log_dir)

    # 显示统计信息
    show_log_stats(log_dir)

    if args.stats:
        return

    # 执行清理
    logger.info("")
    deleted_count, freed_space = cleanup_old_logs(
        log_dir=log_dir,
        days=args.days,
        compress=not args.no_compress,
        dry_run=args.dry_run
    )

    if deleted_count > 0:
        logger.info(f"\n清理完成:")
        logger.info(f"  处理文件数: {deleted_count}")
        logger.info(f"  释放空间: {format_size(freed_space)}")
    else:
        logger.info("\n没有需要清理的文件")

    # 再次显示统计
    if not args.dry_run and deleted_count > 0:
        logger.info("\n清理后的统计:")
        show_log_stats(log_dir)


if __name__ == "__main__":
    main()
