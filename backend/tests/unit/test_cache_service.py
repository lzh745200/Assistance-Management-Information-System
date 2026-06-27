"""
缓存服务测试
"""
import pytest
from unittest.mock import patch, AsyncMock

class TestCacheService:
    """缓存服务测试"""

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        from app.services.cache_service import CacheService

        service = CacheService()

        with patch.object(service, 'cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value={"data": "value"})
            mock_cache.set = AsyncMock(return_value=True)

            await service.set("test_key", {"data": "value"}, ttl=3600)
            result = await service.get("test_key")

            assert result is not None

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """测试缓存删除"""
        from app.services.cache_service import CacheService

        service = CacheService()

        with patch.object(service, 'cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_cache.delete = AsyncMock(return_value=True)

            await service.set("delete_key", "value")
            await service.delete("delete_key")
            result = await service.get("delete_key")

            assert result is None

    @pytest.mark.asyncio
    async def test_cache_exists(self):
        """测试缓存键存在检查"""
        from app.services.cache_service import CacheService

        service = CacheService()

        with patch.object(service, 'cache_manager') as mock_cache:
            mock_cache.exists = AsyncMock(return_value=False)

            result = await service.exists("nonexistent_key")
            assert result is False

    @pytest.mark.asyncio
    async def test_cache_clear_pattern(self):
        """测试模式清除缓存"""
        from app.services.cache_service import CacheService

        service = CacheService()

        with patch.object(service, 'cache_manager') as mock_cache:
            mock_cache.clear_pattern = AsyncMock(return_value=0)

            result = await service.clear_pattern("test:*")
            assert isinstance(result, int)

class TestCacheServiceStats:
    """缓存统计测试"""

    def test_cache_stats_initial(self):
        """测试初始缓存统计"""
        from app.services.cache_service import CacheService

        service = CacheService()
        stats = service.cache_stats

        assert isinstance(stats, dict)
        assert "hits" in stats
        assert "misses" in stats

    def test_get_cache_stats(self):
        """测试获取缓存统计"""
        from app.services.cache_service import CacheService

        service = CacheService()
        stats = service.get_cache_stats()

        assert isinstance(stats, dict)

    def test_reset_cache_stats(self):
        """测试重置缓存统计"""
        from app.services.cache_service import CacheService

        service = CacheService()
        service.reset_cache_stats()

        stats = service.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

class TestCacheStrategy:
    """缓存策略测试"""

    def test_cache_strategy_constants(self):
        """测试缓存策略常量"""
        from app.services.cache_service import CacheStrategy

        assert CacheStrategy.SHORT == 60
        assert CacheStrategy.MEDIUM == 300
        assert CacheStrategy.LONG == 3600
        assert CacheStrategy.VERY_LONG == 86400

    def test_cache_strategy_prefixes(self):
        """测试缓存策略前缀"""
        from app.services.cache_service import CacheStrategy

        assert CacheStrategy.USER_PREFIX == "user:"
        assert CacheStrategy.VILLAGE_PREFIX == "village:"
        assert CacheStrategy.DATA_PREFIX == "data:"
        assert CacheStrategy.API_PREFIX == "api:"
        assert CacheStrategy.STATS_PREFIX == "stats:"
