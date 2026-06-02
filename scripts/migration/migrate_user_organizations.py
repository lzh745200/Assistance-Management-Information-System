"""
创建 user_organizations 表和相关索引
"""
import sys
import os

# 添加项目根目录到路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, backend_path)

from app.core.database import engine
from app.models.user_organization import UserOrganization
from app.models.base import Base

print("=" * 60)
print("��建 user_organizations 表")
print("=" * 60)
print()

try:
    # 创建表
    Base.metadata.create_all(bind=engine, tables=[UserOrganization.__table__])
    print("[OK] user_organizations table created successfully")
    print()
    print("Table structure:")
    print("  - id: INTEGER PRIMARY KEY")
    print("  - user_id: INTEGER NOT NULL (FK to users.id)")
    print("  - organization_id: INTEGER NOT NULL (FK to organizations.id)")
    print("  - role: VARCHAR(20)")
    print("  - created_at: DATETIME NOT NULL")
    print("  - updated_at: DATETIME NOT NULL")
    print()
    print("Indexes:")
    print("  - idx_user_org (user_id, organization_id)")
    print("  - idx_user_organizations_user (user_id)")
    print("  - idx_user_organizations_org (organization_id)")
    print()
    print("Constraints:")
    print("  - uq_user_org UNIQUE (user_id, organization_id)")
    print()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)

except Exception as e:
    print(f"[FAIL] Failed to create table: {e}")
    sys.exit(1)
