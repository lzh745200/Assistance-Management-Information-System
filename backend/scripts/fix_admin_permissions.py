#!/usr/bin/env python3
"""修复管理员权限 - 重置密码并确保角色正确"""

import sys
import os

# 添加项目根目录到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from sqlalchemy import text

def fix_admin_user():
    """修复管理员用户权限"""
    db = SessionLocal()
    try:
        from app.models.user import User

        admin = db.query(User).filter(User.username == "admin").first()

        if not admin:
            print("[X] 未找到管理员用户，创建新管理员...")
            # 创建新管理员（密码需在首次登录时修改）
            import secrets
            temp_password = secrets.token_urlsafe(12)
            admin = User(
                username="admin",
                email="admin@assistance-management.gov.cn",
                full_name="系统管理员",
                hashed_password=get_password_hash(temp_password),
                role="super_admin",
                is_active=True,
                is_superuser=True,
                must_change_password=True,
                permissions="admin:all,system:config,user:manage,role:manage,audit:view,backup:manage,data:import,data:export",
            )
            db.add(admin)
            db.flush()
            print(f"[OK] 已创建新管理员，ID: {admin.id}，临时密码: {temp_password}")
        else:
            print(f"[INFO] 找到管理员用户，当前状态:")
            print(f"   - ID: {admin.id}")
            print(f"   - 用户名: {admin.username}")
            print(f"   - 当前角色: {admin.role}")
            print(f"   - 是否激活: {admin.is_active}")
            print(f"   - 是否超级用户: {admin.is_superuser}")
            print(f"   - 权限列表: {admin.permissions}")

            # 修复角色 - 强制设置为 super_admin
            old_role = admin.role
            if admin.role not in ["admin", "super_admin"]:
                admin.role = "super_admin"
                print(f"[OK] 角色已修复: {old_role} -> super_admin")

            # 强制设置 is_superuser 为 True
            if not admin.is_superuser:
                admin.is_superuser = True
                print(f"[OK] is_superuser 已设置为 True")

            # 确保 is_superuser 标志正确
            if admin.role in ["admin", "super_admin"] and not admin.is_superuser:
                admin.is_superuser = True
                print(f"[OK] is_superuser 标志已设置为 True")

            # 修复权限
            admin_permissions = [
                "admin:all",
                "system:config",
                "user:manage",
                "role:manage",
                "audit:view",
                "backup:manage",
                "data:import",
                "data:export",
            ]
            if not admin.permissions or admin.permissions == "":
                admin.permissions = ",".join(admin_permissions)
                print(f"[OK] 权限已重置为完整管理员权限")

            # 确保用户已激活
            if not admin.is_active:
                admin.is_active = True
                print(f"[OK] 用户已激活")

            # 重置登录失败次数
            if getattr(admin, "failed_login_count", 0) > 0:
                admin.failed_login_count = 0
                print(f"[OK] 登录失败次数已重置")

            # 清除锁定状态
            if getattr(admin, "locked_until", None):
                admin.locked_until = None
                print(f"[OK] 账户锁定已清除")

        # 重置密码（使用随机临时密码，首次登录强制修改）
        import secrets
        new_password = secrets.token_urlsafe(12)
        admin.hashed_password = hash_password(new_password)
        admin.must_change_password = True
        print(f"[OK] 密码已重置，临时密码: {new_password}")

        db.commit()

        print("\n" + "="*50)
        print("[DONE] 管理员权限修复完成!")
        print("="*50)
        print(f"用户名: admin")
        print(f"密码: {new_password}")
        print(f"角色: {admin.role}")
        print(f"超级用户: {admin.is_superuser}")
        print("="*50)
        print("现在可以重新登录系统管理所有功能")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 修复失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def check_database_connection():
    """检查数据库连接"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("[OK] 数据库连接正常")
            return True
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    print("管理员权限修复工具")
    print("="*50)

    if not check_database_connection():
        sys.exit(1)

    fix_admin_user()
