#!/usr/bin/env python3
"""
数据库优化脚本
执行 VACUUM 和 ANALYZE 优化数据库性能
"""

import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, event
from app.core.config import settings


def _configure_sqlite_pragmas(dbapi_conn, connection_record):
    """配置 SQLite PRAGMA 优化参数"""
    cursor = dbapi_conn.cursor()
    try:
        # WAL 模式：允许并发读 + 单写，提升并发性能
        cursor.execute("PRAGMA journal_mode=WAL")
        # NORMAL 同步模式：平衡性能与安全性（单机版推荐）
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 增大缓存：~64MB（单机版可用更多内存）
        cursor.execute("PRAGMA cache_size=-65536")
        # 临时表存内存：加速临时查询
        cursor.execute("PRAGMA temp_store=MEMORY")
        # 启用外键约束：确保数据完整性
        cursor.execute("PRAGMA foreign_keys=ON")
        # 设置 busy_timeout：避免 SQLITE_BUSY 错误（5秒超时）
        cursor.execute("PRAGMA busy_timeout=5000")
        # 优化 mmap_size：使用内存映射 I/O（256MB）
        cursor.execute("PRAGMA mmap_size=268435456")
    finally:
        cursor.close()


def optimize_database():
    """优化数据库"""
    print("=" * 60)
    print("数据库优化工具")
    print("=" * 60)
    print()

    # 创建 engine 并应用 PRAGMA 配置
    engine = create_engine(settings.DATABASE_URL)

    # 只对 SQLite 数据库应用 PRAGMA 配置
    if settings.DATABASE_URL.startswith("sqlite"):
        event.listens_for(engine, "connect")(_configure_sqlite_pragmas)

    with engine.connect() as conn:
        # 1. 获取优化前的数据库大小
        print("1. 获取当前数据库大小...")
        result = conn.execute(text('PRAGMA page_count'))
        page_count_before = result.scalar()
        result = conn.execute(text('PRAGMA page_size'))
        page_size = result.scalar()
        size_before_mb = round(page_count_before * page_size / (1024 * 1024), 2)
        print(f"   当前大小: {size_before_mb} MB")
        print()

        # 2. 执行 ANALYZE (更新查询优化器统计信息)
        print("2. 执行 ANALYZE (更新统计信息)...")
        start_time = datetime.now()
        conn.execute(text("ANALYZE"))
        conn.commit()
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"   ANALYZE 完成 (耗时: {elapsed:.2f}秒)")
        print()

        # 3. 执行 VACUUM (回收空间并整理碎片)
        print("3. 执行 VACUUM (回收空间并整理碎片)...")
        print("   此操作可能需要较长时间,请耐心等待...")
        start_time = datetime.now()
        conn.execute(text("VACUUM"))
        conn.commit()
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"   VACUUM 完成 (耗时: {elapsed:.2f}秒)")
        print()

        # 4. 获取优化后的数据库大小
        print("4. 获取优化后的数据库大小...")
        result = conn.execute(text('PRAGMA page_count'))
        page_count_after = result.scalar()
        size_after_mb = round(page_count_after * page_size / (1024 * 1024), 2)
        print(f"   优化后大小: {size_after_mb} MB")
        print()

        # 5. 显示优化效果
        saved_mb = size_before_mb - size_after_mb
        saved_percent = (saved_mb / size_before_mb * 100) if size_before_mb > 0 else 0
        print("=" * 60)
        print("优化结果:")
        print(f"  优化前: {size_before_mb} MB")
        print(f"  优化后: {size_after_mb} MB")
        print(f"  节省空间: {saved_mb:.2f} MB ({saved_percent:.1f}%)")
        print("=" * 60)
        print()
        print("数据库优化完成!")


if __name__ == "__main__":
    # 设置 UTF-8 输出编码
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    try:
        # 确认操作
        print("警告: 此操作将锁定数据库,请确保没有其他程序正在使用数据库")
        print()
        response = input("是否继续? (y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            sys.exit(0)
        print()

        optimize_database()

    except Exception as e:
        print(f"优化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
