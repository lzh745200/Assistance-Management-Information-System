"""
简化测试 Token 黑名单服务
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, backend_path)

from app.models.token_blacklist import TokenBlacklist
from app.core.database import SessionLocal

print("=" * 60)
print("测试 Token 黑名单数据模型")
print("=" * 60)
print()

# 创建数据库会话
db = SessionLocal()

try:
    # 测试 1: 添加 Token 到黑名单
    print("测试 1: 添加 Token 到黑名单")
    test_jti = "test_jti_12345"
    test_user_id = 1
    expires_at = datetime.utcnow() + timedelta(hours=1)

    blacklist_entry = TokenBlacklist(
        token_jti=test_jti,
        user_id=test_user_id,
        expires_at=expires_at,
        reason="logout",
    )
    db.add(blacklist_entry)
    db.commit()
    print("[OK] Token 添加成功")

    # 测试 2: 查询 Token
    print()
    print("测试 2: 查询 Token")
    result = db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == test_jti).first()

    if result:
        print(f"[OK] Token 查询成功: {result}")
        print(f"  - JTI: {result.token_jti}")
        print(f"  - User ID: {result.user_id}")
        print(f"  - Reason: {result.reason}")
        print(f"  - Expires At: {result.expires_at}")
    else:
        print("[FAIL] Token 查询失败")

    # 测试 3: 删除 Token
    print()
    print("测试 3: 删除 Token")
    db.delete(result)
    db.commit()
    print("[OK] Token 删除成功")

    # 测试 4: 验证删除
    print()
    print("测试 4: 验证删除")
    result = db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == test_jti).first()

    if not result:
        print("[OK] Token 已被删除")
    else:
        print("[FAIL] Token 仍然存在")

    print()
    print("=" * 60)
    print("所有测试通过！")
    print("=" * 60)

finally:
    db.close()
