#!/usr/bin/env python3
"""重置管理员密码"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import hash_password

db = SessionLocal()
try:
    from app.models.user import User

    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        # 重置密码为随机临时密码（首次登录强制修改）
        import secrets
        new_password = secrets.token_urlsafe(12)
        admin.hashed_password = hash_password(new_password)
        admin.must_change_password = True
        admin.failed_login_count = 0
        admin.locked_until = None
        admin.revoke_all_tokens()
        db.commit()
        print(f"管理员密码已重置，临时密码: {new_password}")
        print("首次登录后将强制要求修改密码")
    else:
        print("未找到管理员用户")
except Exception as e:
    print(f"重置密码错误: {e}")
    db.rollback()
finally:
    db.close()