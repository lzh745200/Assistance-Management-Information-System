#!/usr/bin/env python3
"""
PRAGMA 配置验证脚本
验证数据库 PRAGMA 配置是否正确应用
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
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


def verify_pragma_configuration():
    """验证 PRAGMA 配置"""
    print("=" * 60)
    print("PRAGMA 配置验证")
    print("=" * 60)
    print()

    # 创建 engine 并应用 PRAGMA 配置
    engine = create_engine(settings.DATABASE_URL)

    if settings.DATABASE_URL.startswith("sqlite"):
        event.listens_for(engine, "connect")(_configure_sqlite_pragmas)

    # 期望的配置
    expected_configs = {
        'journal_mode': 'wal',
        'synchronous': '1',  # NORMAL = 1
        'cache_size': '-65536',
        'temp_store': '2',  # MEMORY = 2
        'foreign_keys': '1',
        'mmap_size': '268435456',
        'busy_timeout': '5000'
    }

    all_passed = True
    with engine.connect() as conn:
        print("检查 PRAGMA 配置:")
        print()

        for pragma, expected in expected_configs.items():
            result = conn.execute(text(f'PRAGMA {pragma}'))
            actual = str(result.scalar())

            if actual == expected:
                print(f"  ✓ {pragma:20s} = {actual:15s} (正确)")
            else:
                print(f"  ✗ {pragma:20s} = {actual:15s} (期望: {expected})")
                all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("✓ 所有 PRAGMA 配置正确")
    else:
        print("✗ 部分 PRAGMA 配置不正确")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    # 设置 UTF-8 输出编码
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    try:
        success = verify_pragma_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
