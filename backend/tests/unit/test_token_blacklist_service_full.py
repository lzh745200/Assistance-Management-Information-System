"""Tests for app/services/token_blacklist_service.py — 目标 100% 覆盖。

覆盖要点：
- add_to_blacklist: 成功(ttl>0 写缓存) / 过期 token(ttl<=0 不写缓存) / 失败 rollback
- is_blacklisted:
  * 缓存命中 → True
  * 缓存未命中 + DB 命中 + ttl>0 → 回填缓存 + True
  * 缓存未命中 + DB 命中 + ttl<=0 → 不回填 + True
  * 缓存未命中 + DB 未命中 → False
  * 异常 → False
- blacklist_user_tokens: try 返回 0 / except 返回 0
- cleanup_expired: count>0 (写日志) / count==0 / 异常返回 0
- get_blacklist_count: 无 user_id / 有 user_id / 异常返回 0
- get_token_blacklist_service: 工厂返回实例
"""
import importlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.cache import cache_manager
from app.models import _MODULE_MAP
from app.models.base import Base
from app.services.token_blacklist_service import (
    TokenBlacklistService,
    get_token_blacklist_service,
)


# ---------------------------------------------------------------------------
# 真实异步内存 DB fixture
# ---------------------------------------------------------------------------


async def _build_async_session():
    """构建异步内存数据库，包含完整 Base.metadata。"""
    for mod_path in set(_MODULE_MAP.values()):
        importlib.import_module(f"app.models{mod_path}")
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(
        autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
    )
    db = Session()
    return db, engine


@pytest.fixture
async def async_db():
    db, engine = await _build_async_session()
    yield db
    await db.close()
    await engine.dispose()


@pytest.fixture(autouse=True)
def clear_cache():
    """每个测试前后清空全局缓存，避免跨用例污染。"""
    cache_manager._b.clear()
    yield
    cache_manager._b.clear()


# ---------------------------------------------------------------------------
# add_to_blacklist
# ---------------------------------------------------------------------------


class TestAddToBlacklist:
    async def test_add_success_writes_cache(self, async_db):
        """成功添加且 ttl>0 → 写缓存，返回 True。"""
        svc = TokenBlacklistService(async_db)
        expires = datetime(2027, 1, 1, tzinfo=timezone.utc)
        result = await svc.add_to_blacklist("jti-1", 1, expires, reason="logout")
        assert result is True
        cached = await cache_manager.get("token_blacklist:jti-1")
        assert cached == "1"

    async def test_add_expired_token_skips_cache(self, async_db):
        """已过期 token (ttl<=0) → 不写缓存，但仍返回 True。"""
        svc = TokenBlacklistService(async_db)
        expires = datetime(2020, 1, 1, tzinfo=timezone.utc)
        result = await svc.add_to_blacklist("jti-old", 1, expires)
        assert result is True
        cached = await cache_manager.get("token_blacklist:jti-old")
        assert cached is None

    async def test_add_duplicate_jti_returns_false(self, async_db):
        """重复 jti 触发唯一约束 → except → rollback → False。"""
        svc = TokenBlacklistService(async_db)
        expires = datetime(2027, 1, 1, tzinfo=timezone.utc)
        assert await svc.add_to_blacklist("jti-dup", 1, expires) is True
        # 第二次插入同一 jti → IntegrityError → 捕获 → False
        result = await svc.add_to_blacklist("jti-dup", 1, expires)
        assert result is False


# ---------------------------------------------------------------------------
# is_blacklisted
# ---------------------------------------------------------------------------


class TestIsBlacklisted:
    async def test_cache_hit_returns_true(self, async_db):
        """缓存命中 → True（不查 DB）。"""
        await cache_manager.set("token_blacklist:jti-c", "1", ttl=60)
        svc = TokenBlacklistService(async_db)
        assert await svc.is_blacklisted("jti-c") is True

    async def test_db_hit_ttl_positive_backfills_cache(self, async_db):
        """缓存未命中 + DB 命中 + ttl>0 → 回填缓存 + True。

        直接插入记录并在测试中保留引用，确保 identity map 返回带 tz 的 datetime
        （SQLite DateTime 列不保留 tz，弱引用被回收后会从 DB 重建为 naive）。
        """
        from app.models.token_blacklist import TokenBlacklist

        svc = TokenBlacklistService(async_db)
        future_entry = TokenBlacklist(
            token_jti="jti-future",
            user_id=1,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            reason="logout",
        )
        async_db.add(future_entry)
        await async_db.commit()

        result = await svc.is_blacklisted("jti-future")
        assert result is True
        # ttl>0 → 缓存应被回填
        cached = await cache_manager.get("token_blacklist:jti-future")
        assert cached == "1"

    async def test_db_hit_ttl_nonpositive_skips_cache(self, async_db):
        """缓存未命中 + DB 命中 + ttl<=0 → 不回填缓存 + True。"""
        svc = TokenBlacklistService(async_db)
        # 直接写入一条已过期的 DB 记录（绕过 add_to_blacklist 的 ttl>0 缓存写入）
        from app.models.token_blacklist import TokenBlacklist
        expired_entry = TokenBlacklist(
            token_jti="jti-expired",
            user_id=1,
            expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
            reason="expired",
        )
        async_db.add(expired_entry)
        await async_db.commit()

        result = await svc.is_blacklisted("jti-expired")
        assert result is True
        # ttl<=0 → 不回填缓存
        cached = await cache_manager.get("token_blacklist:jti-expired")
        assert cached is None

    async def test_db_miss_returns_false(self, async_db):
        """缓存未命中 + DB 未命中 → False。"""
        svc = TokenBlacklistService(async_db)
        result = await svc.is_blacklisted("jti-missing")
        assert result is False

    async def test_exception_returns_false(self, monkeypatch):
        """DB execute 抛异常 → except → False。"""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.execute = AsyncMock(side_effect=RuntimeError("db down"))
        svc = TokenBlacklistService(mock_db)
        result = await svc.is_blacklisted("jti-err")
        assert result is False


# ---------------------------------------------------------------------------
# blacklist_user_tokens
# ---------------------------------------------------------------------------


class TestBlacklistUserTokens:
    async def test_returns_zero_and_logs(self, async_db):
        """正常路径 → 记录日志并返回 0。"""
        svc = TokenBlacklistService(async_db)
        result = await svc.blacklist_user_tokens(42, reason="password_change")
        assert result == 0

    async def test_exception_returns_zero(self, monkeypatch):
        """logger.info 抛异常 → except → 返回 0。"""
        from app.services import token_blacklist_service as mod

        def raise_on_info(msg, *a, **kw):
            raise RuntimeError("logging broken")

        monkeypatch.setattr(mod.logger, "info", raise_on_info)
        svc = TokenBlacklistService(AsyncMock())
        result = await svc.blacklist_user_tokens(1, reason="test")
        assert result == 0


# ---------------------------------------------------------------------------
# cleanup_expired
# ---------------------------------------------------------------------------


class TestCleanupExpired:
    async def test_cleanup_with_expired_records_logs_count(self, async_db):
        """有过期记录 → 删除并记录日志，返回删除数。"""
        svc = TokenBlacklistService(async_db)
        from app.models.token_blacklist import TokenBlacklist

        # 插入 2 条已过期 + 1 条未过期
        async_db.add_all([
            TokenBlacklist(token_jti="old1", user_id=1,
                           expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc), reason="r"),
            TokenBlacklist(token_jti="old2", user_id=1,
                           expires_at=datetime(2020, 2, 1, tzinfo=timezone.utc), reason="r"),
            TokenBlacklist(token_jti="live", user_id=1,
                           expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc), reason="r"),
        ])
        await async_db.commit()

        count = await svc.cleanup_expired()
        assert count == 2

    async def test_cleanup_no_expired_returns_zero(self, async_db):
        """无过期记录 → 返回 0，不写日志。"""
        svc = TokenBlacklistService(async_db)
        from app.models.token_blacklist import TokenBlacklist

        async_db.add(TokenBlacklist(
            token_jti="live", user_id=1,
            expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc), reason="r",
        ))
        await async_db.commit()

        count = await svc.cleanup_expired()
        assert count == 0

    async def test_cleanup_exception_returns_zero(self, monkeypatch):
        """execute 抛异常 → except → rollback → 0。"""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.execute = AsyncMock(side_effect=RuntimeError("db error"))
        mock_db.rollback = AsyncMock()
        svc = TokenBlacklistService(mock_db)
        count = await svc.cleanup_expired()
        assert count == 0
        mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_blacklist_count
# ---------------------------------------------------------------------------


class TestGetBlacklistCount:
    async def test_count_all_no_user_id(self, async_db):
        """无 user_id → 返回总数。"""
        svc = TokenBlacklistService(async_db)
        expires = datetime(2027, 1, 1, tzinfo=timezone.utc)
        await svc.add_to_blacklist("a", 1, expires)
        await svc.add_to_blacklist("b", 2, expires)
        await svc.add_to_blacklist("c", 2, expires)
        cache_manager._b.clear()

        assert await svc.get_blacklist_count() == 3

    async def test_count_filtered_by_user_id(self, async_db):
        """有 user_id → 返回该用户的记录数。"""
        svc = TokenBlacklistService(async_db)
        expires = datetime(2027, 1, 1, tzinfo=timezone.utc)
        await svc.add_to_blacklist("a", 1, expires)
        await svc.add_to_blacklist("b", 2, expires)
        await svc.add_to_blacklist("c", 2, expires)
        cache_manager._b.clear()

        assert await svc.get_blacklist_count(user_id=2) == 2

    async def test_count_exception_returns_zero(self, monkeypatch):
        """execute 抛异常 → except → 0。"""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.execute = AsyncMock(side_effect=RuntimeError("db error"))
        svc = TokenBlacklistService(mock_db)
        assert await svc.get_blacklist_count() == 0


# ---------------------------------------------------------------------------
# get_token_blacklist_service 工厂
# ---------------------------------------------------------------------------


class TestFactory:
    def test_returns_service_instance(self):
        """工厂返回 TokenBlacklistService 实例。"""
        mock_db = MagicMock()
        svc = get_token_blacklist_service(mock_db)
        assert isinstance(svc, TokenBlacklistService)
        assert svc.db is mock_db
