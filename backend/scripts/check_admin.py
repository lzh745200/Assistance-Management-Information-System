#!/usr/bin/env python3
"""检查管理员用户"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        print("管理员用户信息:")
        print(f"  ID: {admin.id}")
        print(f"  用户名: {admin.username}")
        print(f"  邮箱: {admin.email}")
        print(f"  全名: {admin.full_name}")
        print(f"  角色: {admin.role}")
        print(f"  是否超级用户: {admin.is_superuser}")
        print(f"  是否活跃: {admin.is_active}")
        print(f"  组织ID: {admin.organization_id}")
        print(f"  必须修改密码: {admin.must_change_password}")
        print(f"  锁定直到: {admin.locked_until}")
        print(f"  失败登录次数: {admin.failed_login_count}")
        print(f"  创建时间: {admin.created_at}")
    else:
        print("未找到管理员用户")

    # 检查所有用户
    users = db.query(User).all()
    print(f"\n所有用户 ({len(users)} 个):")
    for user in users:
        print(f"  {user.id}: {user.username} ({user.email}), 角色: {user.role}, 活跃: {user.is_active}")

except Exception as e:
    print(f"查询错误: {e}")
finally:
    db.close()
