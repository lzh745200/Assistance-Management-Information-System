#!/usr/bin/env python3
"""
检查 rural_works 表数据
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, event
from app.core.config import settings


def _configure_sqlite_pragmas(dbapi_conn, connection_record):
    """配置 SQLite PRAGMA 优化参数"""
    cursor = dbapi_conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-65536")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA mmap_size=268435456")
    finally:
        cursor.close()


def check_rural_works():
    """检查 rural_works 表"""
    print("=" * 60)
    print("检查 rural_works 表")
    print("=" * 60)
    print()

    engine = create_engine(settings.DATABASE_URL)

    if settings.DATABASE_URL.startswith("sqlite"):
        event.listens_for(engine, "connect")(_configure_sqlite_pragmas)

    with engine.connect() as conn:
        # 检查表是否存在
        result = conn.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='rural_works'
        """))
        table_exists = result.fetchone()

        if not table_exists:
            print("❌ rural_works 表不存在")
            return

        print("✓ rural_works 表存在")
        print()

        # 获取记录数
        result = conn.execute(text("SELECT COUNT(*) FROM rural_works"))
        count = result.scalar()
        print(f"总记录数: {count}")
        print()

        if count == 0:
            print("表中没有数据")
            return

        # 获取前10条记录
        result = conn.execute(text("""
            SELECT id, name, status, type, village_id, created_at
            FROM rural_works
            ORDER BY id
            LIMIT 10
        """))

        print("前10条记录:")
        print(f"{'ID':<5} {'名称':<30} {'状态':<15} {'类型':<15} {'村庄ID':<10}")
        print("-" * 80)

        for row in result:
            id_val = row[0]
            name = row[1][:28] if row[1] else ""
            status = row[2] or ""
            type_val = row[3] or ""
            village_id = row[4] or ""

            print(f"{id_val:<5} {name:<30} {status:<15} {type_val:<15} {village_id:<10}")

        print()

        # 检查状态分布
        result = conn.execute(text("""
            SELECT status, COUNT(*) as count
            FROM rural_works
            GROUP BY status
            ORDER BY count DESC
        """))

        print("状态分布:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")


if __name__ == "__main__":
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    try:
        check_rural_works()
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
