#!/usr/bin/env python3
"""数据库修复脚本 - 检查和修复常见问题"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_db_path():
    """获取数据库路径"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'data', 'rural_revitalization.db')


def check_integrity(db_path):
    """检查数据库完整性"""
    logger.info("检查数据库完整性...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()
    logger.info(f"完整性检查结果: {result[0]}")
    conn.close()
    return result[0] == 'ok'


def check_foreign_keys(db_path):
    """检查外键约束"""
    logger.info("检查外键约束...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check")
    violations = cursor.fetchall()
    if violations:
        logger.warning(f"发现 {len(violations)} 个外键违规")
        for v in violations[:10]:
            logger.warning(f"  {v}")
    else:
        logger.info("外键检查通过")
    conn.close()
    return len(violations) == 0


def vacuum_database(db_path):
    """压缩数据库"""
    logger.info("压缩数据库...")
    conn = sqlite3.connect(db_path)
    conn.execute("VACUUM")
    conn.close()
    logger.info("数据库压缩完成")


def main():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return

    logger.info(f"数据库路径: {db_path}")
    logger.info(f"文件大小: {os.path.getsize(db_path)} bytes")

    check_integrity(db_path)
    check_foreign_keys(db_path)
    vacuum_database(db_path)

    logger.info("数据库修复脚本执行完成")


if __name__ == "__main__":
    main()
