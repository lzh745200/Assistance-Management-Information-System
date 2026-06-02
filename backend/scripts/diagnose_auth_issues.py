#!/usr/bin/env python3
"""全面诊断认证问题"""

import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal, engine
from app.core.token_blacklist import token_blacklist
from app.core.token_manager import token_manager
from sqlalchemy import text
from jose import jwt

def check_database():
    """检查数据库连接"""
    print("=" * 60)
    print("1. 数据库连接检查")
    print("=" * 60)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("[OK] 数据库连接正常")
            return True
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False

def check_admin_user():
    """检查管理员用户"""
    print("\n" + "=" * 60)
    print("2. 管理员用户检查")
    print("=" * 60)
    db = SessionLocal()
    try:
        from app.models.user import User
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("[ERROR] 未找到 admin 用户")
            return False

        print(f"  ID: {admin.id}")
        print(f"  用户名: {admin.username}")
        print(f"  角色: {admin.role}")
        print(f"  is_active: {admin.is_active}")
        print(f"  is_superuser: {admin.is_superuser}")
        print(f"  失败次数: {getattr(admin, 'failed_login_count', 0)}")
        print(f"  锁定时间: {getattr(admin, 'locked_until', None)}")

        if admin.role not in ["admin", "super_admin"]:
            print(f"[WARNING] 角色不是管理员: {admin.role}")
        if not admin.is_active:
            print("[ERROR] 用户未激活")
        if getattr(admin, 'locked_until', None):
            print("[WARNING] 账户被锁定")

        return True
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        return False
    finally:
        db.close()

def check_token_blacklist():
    """检查Token黑名单"""
    print("\n" + "=" * 60)
    print("3. Token黑名单检查")
    print("=" * 60)
    try:
        # 获取黑名单数据库路径
        from app.core.config import settings
        db_url = settings.DATABASE_URL
        db_path_str = db_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path_str):
            db_path_str = os.path.join(os.getcwd(), db_path_str)
        blacklist_db = os.path.join(os.path.dirname(db_path_str), "token_blacklist.db")

        print(f"  黑名单数据库: {blacklist_db}")

        if os.path.exists(blacklist_db):
            import sqlite3
            conn = sqlite3.connect(blacklist_db)
            cursor = conn.execute("SELECT COUNT(*) FROM token_blacklist")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"[INFO] 黑名单中共有 {count} 条记录")
            if count > 0:
                print("[WARNING] 黑名单中有记录，可能导致合法token被拒绝")
        else:
            print("[OK] 黑名单数据库不存在")

        return True
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        return False

def check_token_config():
    """检查Token配置"""
    print("\n" + "=" * 60)
    print("4. Token配置检查")
    print("=" * 60)
    try:
        from app.core.config import settings
        print(f"  SECRET_KEY: {'已设置' if settings.SECRET_KEY else '未设置'}")
        print(f"  ALGORITHM: {settings.ALGORITHM}")
        print(f"  ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
        print(f"  REFRESH_TOKEN_EXPIRE_DAYS: {settings.REFRESH_TOKEN_EXPIRE_DAYS}")
        return True
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        return False

def test_token_creation():
    """测试Token创建"""
    print("\n" + "=" * 60)
    print("5. Token创建测试")
    print("=" * 60)
    try:
        # 创建测试token
        tokens = token_manager.create_token_pair("test_user")
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        print(f"[OK] Access Token 创建成功")
        print(f"[OK] Refresh Token 创建成功")

        # 解码验证
        access_payload = token_manager.decode_token(access_token, expected_type="access")
        refresh_payload = token_manager.decode_token(refresh_token, expected_type="refresh")

        if access_payload:
            print(f"[OK] Access Token 可解码: sub={access_payload.get('sub')}")
        else:
            print("[ERROR] Access Token 无法解码")

        if refresh_payload:
            print(f"[OK] Refresh Token 可解码: sub={refresh_payload.get('sub')}")
        else:
            print("[ERROR] Refresh Token 无法解码")

        # 检查黑名单
        if token_blacklist.is_blacklisted(access_token):
            print("[ERROR] 新创建的Access Token在黑名单中")
        else:
            print("[OK] 新创建的Access Token不在黑名单中")

        if token_blacklist.is_blacklisted(refresh_token):
            print("[ERROR] 新创建的Refresh Token在黑名单中")
        else:
            print("[OK] 新创建的Refresh Token不在黑名单中")

        return True
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_all_issues():
    """修复所有发现的问题"""
    print("\n" + "=" * 60)
    print("6. 自动修复问题")
    print("=" * 60)

    db = SessionLocal()
    try:
        from app.models.user import User

        # 修复管理员用户
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            fixed = False

            # 修复角色
            if admin.role not in ["admin", "super_admin"]:
                print(f"[FIX] 修复角色: {admin.role} -> super_admin")
                admin.role = "super_admin"
                fixed = True

            # 修复is_superuser
            if not admin.is_superuser:
                print("[FIX] 设置 is_superuser = True")
                admin.is_superuser = True
                fixed = True

            # 修复激活状态
            if not admin.is_active:
                print("[FIX] 激活用户")
                admin.is_active = True
                fixed = True

            # 清除锁定
            if getattr(admin, 'locked_until', None):
                print("[FIX] 清除账户锁定")
                admin.locked_until = None
                fixed = True

            # 重置失败次数
            if getattr(admin, 'failed_login_count', 0) > 0:
                print("[FIX] 重置登录失败次数")
                admin.failed_login_count = 0
                fixed = True

            if fixed:
                db.commit()
                print("[OK] 管理员用户已修复")
            else:
                print("[OK] 管理员用户无需修复")

        # 清空黑名单
        try:
            token_blacklist.clear_all()
            print("[OK] Token黑名单已清空")
        except Exception as e:
            print(f"[WARNING] 清空黑名单失败: {e}")

        return True
    except Exception as e:
        db.rollback()
        print(f"[ERROR] 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    print("=" * 60)
    print("认证系统全面诊断工具")
    print("=" * 60)

    results = []
    results.append(check_database())
    results.append(check_admin_user())
    results.append(check_token_blacklist())
    results.append(check_token_config())
    results.append(test_token_creation())
    results.append(fix_all_issues())

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

    if all(results):
        print("[OK] 所有检查通过")
        print("\n请在前端执行以下操作:")
        print("1. 打开浏览器控制台 (F12)")
        print("2. 执行: sessionStorage.clear(); localStorage.clear();")
        print("3. 刷新页面并重新登录")
        return 0
    else:
        print("[WARNING] 发现部分问题，请检查日志")
        return 1

if __name__ == "__main__":
    sys.exit(main())
