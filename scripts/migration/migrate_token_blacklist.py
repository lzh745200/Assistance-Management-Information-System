"""
创建 token_blacklist 表的数据库迁移
"""
import sys
import os

# 添加项目根目录到路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, backend_path)

from app.core.database import engine
from app.models.token_blacklist import TokenBlacklist
from app.models.base import Base

print("=" * 60)
print("创建 token_blacklist 表")
print("=" * 60)
print()

try:
    # 创建表
    Base.metadata.create_all(bind=engine, tables=[TokenBlacklist.__table__])
    print("[OK] token_blacklist 表创建成功")
    print()
    print("表结构:")
    print("  - id: INTEGER PRIMARY KEY")
    print("  - token_jti: VARCHAR(255) UNIQUE NOT NULL")
    print("  - user_id: INTEGER NOT NULL (FK to users.id)")
    print("  - blacklisted_at: DATETIME NOT NULL")
    print("  - expires_at: DATETIME NOT NULL")
    print("  - reason: VARCHAR(100)")
    print()
    print("索引:")
    print("  - idx_token_blacklist_user_time (user_id, blacklisted_at)")
    print("  - idx_token_blacklist_expires (expires_at)")
    print()
    print("=" * 60)
    print("迁移完成！")
    print("=" * 60)

except Exception as e:
    print(f"[FAIL] 创建表失败: {e}")
    sys.exit(1)
