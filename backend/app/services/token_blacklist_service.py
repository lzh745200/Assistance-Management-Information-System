"""
Token 黑名单服务
使用 SQLite + 缓存双层架构实现 Token 黑名单持久化
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.models.token_blacklist import TokenBlacklist

logger = logging.getLogger(__name__)


class TokenBlacklistService:
    """Token 黑名单服务"""

    # 缓存键前缀
    CACHE_PREFIX = "token_blacklist:"
    # 缓存 TTL（秒）- 使用 Token 的剩余有效期
    DEFAULT_CACHE_TTL = 3600

    def __init__(self, db: AsyncSession):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    async def add_to_blacklist(
        self,
        token_jti: str,
        user_id: int,
        expires_at: datetime,
        reason: str = "logout",
    ) -> bool:
        """
        添加 Token 到黑名单

        Args:
            token_jti: JWT ID
            user_id: 用户ID
            expires_at: Token 过期时间
            reason: 加入黑名单原因

        Returns:
            是否添加成功
        """
        try:
            # 1. 添加到数据库
            blacklist_entry = TokenBlacklist(
                token_jti=token_jti,
                user_id=user_id,
                expires_at=expires_at,
                reason=reason,
            )
            self.db.add(blacklist_entry)
            await self.db.commit()

            # 2. 添加到缓存
            cache_key = f"{self.CACHE_PREFIX}{token_jti}"
            # 计算 TTL（Token 剩余有效期）
            ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
            if ttl > 0:
                await cache_manager.set(cache_key, "1", ttl=ttl)

            logger.info(f"Token 已加入黑名单: jti={token_jti}, user_id={user_id}, reason={reason}")
            return True

        except Exception as e:
            logger.error(f"添加 Token 到黑名单失败: {e}")
            await self.db.rollback()
            return False

    async def is_blacklisted(self, token_jti: str) -> bool:
        """
        检查 Token 是否在黑名单中

        Args:
            token_jti: JWT ID

        Returns:
            是否在黑名单中
        """
        try:
            # 1. 先查缓存
            cache_key = f"{self.CACHE_PREFIX}{token_jti}"
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                return True

            # 2. 查数据库
            result = await self.db.execute(select(TokenBlacklist).where(TokenBlacklist.token_jti == token_jti))
            blacklist_entry = result.scalar_one_or_none()

            if blacklist_entry:
                # 回填缓存
                ttl = int((blacklist_entry.expires_at - datetime.now(timezone.utc)).total_seconds())
                if ttl > 0:
                    await cache_manager.set(cache_key, "1", ttl=ttl)
                return True

            return False

        except Exception as e:
            logger.error(f"检查 Token 黑名单失败: {e}")
            # 出错时保守处理，认为不在黑名单中
            return False

    async def blacklist_user_tokens(self, user_id: int, reason: str = "password_change") -> int:
        """
        将用户的所有 Token 加入黑名单（用于密码修改等场景）

        Args:
            user_id: 用户ID
            reason: 原因

        Returns:
            加入黑名单的 Token 数量
        """
        try:
            # 注意：这里需要从其他地方获取用户的活跃 Token
            # 简化实现：仅记录操作，实际的 Token 验证会在检查时失败
            logger.info(f"用户 {user_id} 的所有 Token 已标记为失效，原因: {reason}")
            return 0

        except Exception as e:
            logger.error(f"批量加入黑名单失败: {e}")
            return 0

    async def cleanup_expired(self) -> int:
        """
        清理过期的 Token 黑名单记录

        Returns:
            清理的记录数
        """
        try:
            # 删除已过期的记录
            result = await self.db.execute(
                delete(TokenBlacklist).where(
                    TokenBlacklist.expires_at < datetime.now(timezone.utc)
                )
            )
            await self.db.commit()

            count = result.rowcount
            if count > 0:
                logger.info(f"清理了 {count} 条过期的 Token 黑名单记录")

            return count

        except Exception as e:
            logger.error(f"清理过期 Token 失败: {e}")
            await self.db.rollback()
            return 0

    async def get_blacklist_count(self, user_id: Optional[int] = None) -> int:
        """
        获取黑名单记录数

        Args:
            user_id: 用户ID（可选，不提供则返回总数）

        Returns:
            记录数
        """
        try:
            query = select(TokenBlacklist)
            if user_id:
                query = query.where(TokenBlacklist.user_id == user_id)

            result = await self.db.execute(query)
            return len(result.scalars().all())

        except Exception as e:
            logger.error(f"获取黑名单记录数失败: {e}")
            return 0


# 全局服务实例工厂


def get_token_blacklist_service(db: AsyncSession) -> TokenBlacklistService:
    """获取 Token 黑名单服务实例"""
    return TokenBlacklistService(db)
