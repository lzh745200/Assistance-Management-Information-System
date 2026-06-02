"""解锁所有用户账户"""
from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    users = db.query(User).all()
    unlocked_count = 0

    for user in users:
        if user.locked_until is not None or user.failed_login_count > 0:
            print(f"解锁用户: {user.username}")
            print(f"  之前失败次数: {user.failed_login_count}")
            print(f"  之前锁定到: {user.locked_until}")

            user.locked_until = None
            user.failed_login_count = 0
            unlocked_count += 1

    if unlocked_count > 0:
        db.commit()
        print(f"\n成功解锁 {unlocked_count} 个用户")
    else:
        print("\n没有需要解锁的用户")

except Exception as e:
    print(f"错误: {e}")
    db.rollback()
finally:
    db.close()
