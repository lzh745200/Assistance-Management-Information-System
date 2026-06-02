"""
修复 sort_order 字段的 None 值
将所有 organizations 表中 sort_order 为 NULL 的记录更新为 0
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import SessionLocal


def fix_sort_order_null_values():
    """修复 sort_order 的 NULL 值"""
    db = SessionLocal()
    try:
        # 更新所有 sort_order 为 NULL 的记录
        result = db.execute(
            text("UPDATE organizations SET sort_order = 0 WHERE sort_order IS NULL")
        )
        db.commit()

        affected_rows = result.rowcount
        print(f"✓ 已修复 {affected_rows} 条记录的 sort_order 字段")

        # 验证修复结果
        check_result = db.execute(
            text("SELECT COUNT(*) FROM organizations WHERE sort_order IS NULL")
        )
        null_count = check_result.scalar()

        if null_count == 0:
            print("✓ 验证通过：所有 sort_order 字段均已设置为非 NULL 值")
        else:
            print(f"⚠ 警告：仍有 {null_count} 条记录的 sort_order 为 NULL")

    except Exception as e:
        db.rollback()
        print(f"✗ 修复失败: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("开始修复 organizations 表的 sort_order 字段...")
    fix_sort_order_null_values()
    print("修复完成！")
