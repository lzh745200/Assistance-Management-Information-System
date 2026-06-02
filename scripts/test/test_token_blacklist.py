"""
测试 Token 黑名单服务
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, backend_path)

from app.core.database import get_db
from app.services.token_blacklist_service import TokenBlacklistService


async def test_token_blacklist():
    """测试 Token 黑名单服务"""
    print("=" * 60)
    print("测试 Token 黑名单服务")
    print("=" * 60)
    print()

    # 获取数据库会话
    db_gen = get_db()
    db = await anext(db_gen)

    try:
        service = TokenBlacklistService(db)

        # 测试 1: 添加 Token 到黑名单
        print("测试 1: 添加 Token 到黑名单")
        test_jti = "test_jti_12345"
        test_user_id = 1
        expires_at = datetime.utcnow() + timedelta(hours=1)

        success = await service.add_to_blacklist(
            token_jti=test_jti,
            user_id=test_user_id,
            expires_at=expires_at,
            reason="logout",
        )

        if success:
            print("[OK] Token 添加成功")
        else:
            print("[FAIL] Token 添加失败")
            return

        # 测试 2: 检查 Token 是否在黑名单中
        print()
        print("测试 2: 检查 Token 是否在黑名单中")
        is_blacklisted = await service.is_blacklisted(test_jti)

        if is_blacklisted:
            print("[OK] Token 在黑名单中")
        else:
            print("[FAIL] Token 不在黑名单中")
            return

        # 测试 3: 检查不存在的 Token
        print()
        print("测试 3: 检查不存在的 Token")
        is_blacklisted = await service.is_blacklisted("non_existent_jti")

        if not is_blacklisted:
            print("[OK] 不存在的 Token 不在黑名单中")
        else:
            print("[FAIL] 不存在的 Token 被误判为在黑名单中")
            return

        # 测试 4: 获取黑名单记录数
        print()
        print("测试 4: 获取黑名单记录数")
        count = await service.get_blacklist_count()
        print(f"黑名单记录数: {count}")

        if count > 0:
            print("[OK] 黑名单记录数正确")
        else:
            print("[FAIL] 黑名单记录数错误")
            return

        # 测试 5: 清理过期 Token
        print()
        print("测试 5: 清理过期 Token")
        # 添加一个已过期的 Token
        expired_jti = "expired_jti_67890"
        expired_time = datetime.utcnow() - timedelta(hours=1)
        await service.add_to_blacklist(
            token_jti=expired_jti,
            user_id=test_user_id,
            expires_at=expired_time,
            reason="test",
        )

        # 清理过期 Token
        cleaned = await service.cleanup_expired()
        print(f"清理了 {cleaned} 条过期记录")

        if cleaned > 0:
            print("[OK] 过期 Token 清理成功")
        else:
            print("[OK] 没有过期 Token 需要清理")

        print()
        print("=" * 60)
        print("所有测试通过！")
        print("=" * 60)

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(test_token_blacklist())
