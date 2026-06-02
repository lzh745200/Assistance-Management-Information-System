"""创建默认管理员账户"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from datetime import datetime, timezone

def create_default_admin():
    """创建默认管理员账户"""

    db = SessionLocal()
    try:
        # 检查是否已有admin用户
        existing_admin = db.query(User).filter(User.username == "admin").first()

        if existing_admin:
            print("admin 用户已存在，重置密码...")
            existing_admin.hashed_password = hash_password("Admin123!")
            existing_admin.is_active = True
            existing_admin.failed_login_count = 0
            existing_admin.locked_until = None
            db.commit()
            print("✓ admin 密码已重置")
        else:
            print("创建新的 admin 用户...")
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("Admin123!"),
                full_name="系统管理员",
                role="super_admin",
                is_active=True,
                is_superuser=True,
                failed_login_count=0,
                locked_until=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(admin)
            db.commit()
            print("✓ admin 用户创建成功")

        # 检查是否有其他用户
        all_users = db.query(User).all()

        print("\n" + "=" * 80)
        print("系统用户列表:")
        print("=" * 80)
        for user in all_users:
            print(f"用户名: {user.username:15} 角色: {user.role:15} 激活: {user.is_active}")
        print("=" * 80)

        print("\n✓ 默认管理员账户信息:")
        print("  用户名: admin")
        print("  密码: Admin123!")
        print("  角色: super_admin")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_default_admin()
