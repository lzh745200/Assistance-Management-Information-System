"""
Token 黑名单服务单元测试
覆盖: app/services/token_blacklist_service.py
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone


class TestTokenBlacklistServiceConstants:
    def test_cache_prefix(self):
        from app.services.token_blacklist_service import TokenBlacklistService
        assert TokenBlacklistService.CACHE_PREFIX == "token_blacklist:"

    def test_default_cache_ttl(self):
        from app.services.token_blacklist_service import TokenBlacklistService
        assert TokenBlacklistService.DEFAULT_CACHE_TTL == 3600


class TestTokenBlacklistServiceInit:
    def test_init_stores_db(self):
        from app.services.token_blacklist_service import TokenBlacklistService
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        svc = TokenBlacklistService(db=mock_db)
        assert svc.db is mock_db


class TestTokenBlacklistServiceAsync:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def svc(self, mock_db):
        from app.services.token_blacklist_service import TokenBlacklistService
        return TokenBlacklistService(db=mock_db)

    @pytest.mark.asyncio
    async def test_add_to_blacklist_success(self, svc, mock_db):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()

        with patch("app.services.token_blacklist_service.cache_manager") as mock_cache:
            mock_cache.set = AsyncMock()
            expires = datetime(2027, 1, 1, tzinfo=timezone.utc)
            result = await svc.add_to_blacklist("jti-123", 1, expires)
            assert result is True
            mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_to_blacklist_rollback_on_error(self, svc, mock_db):
        mock_db.add = MagicMock(side_effect=Exception("DB error"))
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()

        expires = datetime(2027, 1, 1, tzinfo=timezone.utc)
        result = await svc.add_to_blacklist("jti-456", 2, expires)
        assert result is False
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_blacklisted_cache_hit(self, svc, mock_db):
        with patch("app.services.token_blacklist_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value="1")
            result = await svc.is_blacklisted("jti-cached")
            assert result is True

    @pytest.mark.asyncio
    async def test_is_blacklisted_not_found(self, svc, mock_db):
        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("app.services.token_blacklist_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            result = await svc.is_blacklisted("jti-missing")
            assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, svc, mock_db):
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await svc.cleanup_expired()
        assert result >= 0
