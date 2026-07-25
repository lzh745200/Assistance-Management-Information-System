"""app.core.cache 覆盖率攻坚测试

覆盖缺口：
- SimpleCache.get 过期条目清理（30-32）
- SimpleCache.delete_by_prefix（48-52）与 close（59）
- _evict_if_needed 容量淘汰（63-65）与空库 StopIteration 退出（66-67）
- CacheManager.delete_by_prefix / clear / close（87/90/93）
- cached 装饰器 async 命中分支（113）与 sync 包装整体（119-128）
- _cache 兼容属性的 getter/setter/deleter（152-154/158/162）

全部用例使用独立 SimpleCache 实例，不触碰模块级单例 default_cache/cache_manager，
不给后续测试留脏状态。
"""

from types import SimpleNamespace
from unittest.mock import patch

import app.core.cache as m
from app.core.cache import CacheManager, SimpleCache, cached, get_cache_service


class TestSimpleCacheExpiry:
    def test_expired_entry_deleted_and_counts_miss(self):
        c = SimpleCache()
        # 只替换 cache 模块命名空间内的 time 引用，不影响全局 time 模块
        with patch.object(m, "time", SimpleNamespace(monotonic=lambda: 1000.0)):
            c.set("k", "v", ttl=10)  # expires_at = 1010
        with patch.object(m, "time", SimpleNamespace(monotonic=lambda: 2000.0)):
            assert c.get("k") is None  # 30-32：过期删除并计 miss
        assert "k" not in c._store
        assert c._misses == 1
        assert c._hits == 0


class TestDeleteByPrefix:
    def test_deletes_only_matching(self):
        c = SimpleCache()
        c.set("user:1", 1)
        c.set("user:2", 2)
        c.set("order:1", 3)
        assert c.delete_by_prefix("user:") == 2  # 48-52
        assert c.get("user:1") is None
        assert c.get("user:2") is None
        assert c.get("order:1") == 3

    def test_no_match_returns_zero(self):
        c = SimpleCache()
        c.set("a", 1)
        assert c.delete_by_prefix("zzz") == 0
        assert c.get("a") == 1


class TestDelete:
    def test_delete_existing_and_missing(self):
        c = SimpleCache()
        c.set("a", 1)
        c.delete("a")  # 43-44
        assert c.get("a") is None
        # 删除不存在的键不报错（pop 默认 None）
        c.delete("ghost")


class TestClose:
    def test_close_is_noop(self):
        assert SimpleCache().close() is None  # 59


class TestEviction:
    def test_evicts_oldest_when_full(self):
        c = SimpleCache(max_size=2)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)  # 63-65：淘汰最旧的 a
        assert "a" not in c._store
        assert c.get("b") == 2
        assert c.get("c") == 3

    def test_zero_max_size_breaks_on_empty_store(self):
        c = SimpleCache(max_size=0)
        c.set("x", 1)  # 66-67：空库 next(iter(...)) 抛 StopIteration → break
        assert c.get("x") == 1


class TestCacheManagerAsyncApi:
    async def test_delete(self):
        cm = CacheManager(SimpleCache())
        await cm.set("a", 1)
        await cm.delete("a")  # 83
        assert await cm.get("a") is None

    async def test_delete_by_prefix(self):
        cm = CacheManager(SimpleCache())
        await cm.set("p:1", 1)
        await cm.set("p:2", 2)
        await cm.set("q:1", 3)
        assert await cm.delete_by_prefix("p:") == 2  # 87
        assert await cm.get("p:1") is None
        assert await cm.get("q:1") == 3

    async def test_clear(self):
        cm = CacheManager(SimpleCache())
        await cm.set("a", 1)
        await cm.clear()  # 90
        assert await cm.get("a") is None

    def test_close(self):
        cm = CacheManager(SimpleCache())
        assert cm.close() is None  # 93


class TestCachedDecorator:
    async def test_async_hit_branch(self):
        c = SimpleCache()
        calls = []

        @cached(cache_instance=c, ttl=60)
        async def fetch(x):
            calls.append(x)
            return x * 2

        assert await fetch(3) == 6
        assert await fetch(3) == 6  # 113：命中缓存直接返回
        assert calls == [3]

    def test_sync_wrapper_miss_and_hit(self):
        c = SimpleCache()
        calls = []

        @cached(cache_instance=c, ttl=60)
        def add(a, b):
            calls.append((a, b))
            return a + b

        assert add(1, 2) == 3  # 119-122、125-127：未命中执行并写缓存
        assert add(1, 2) == 3  # 123-124：命中直接返回
        assert calls == [(1, 2)]

    def test_sync_wrapper_with_key_builder(self):
        c = SimpleCache()
        calls = []

        @cached(cache_instance=c, ttl=60, key_builder=lambda x: f"k:{x}")
        def ident(x):
            calls.append(x)
            return x

        assert ident("a") == "a"  # 121 使用 key_builder 生成键
        assert ident("a") == "a"
        assert calls == ["a"]
        assert c.get("k:a") == "a"


class TestGetCacheService:
    async def test_returns_global_cache_manager(self):
        # 140：返回模块级单例（只读使用，不修改其状态）
        assert await get_cache_service() is m.cache_manager


class TestCacheCompatProperty:
    def test_getter_setter_deleter(self):
        cm = CacheManager(SimpleCache())
        assert cm._cache == {}  # 152-154：首次访问自动创建 _cache_data
        cm._cache["x"] = 1
        assert cm._cache == {"x": 1}  # 154：已存在时直接返回
        cm._cache = {"a": 2}  # 158 setter
        assert cm._cache == {"a": 2}
        del cm._cache  # 162 deleter：重置为空 dict
        assert cm._cache == {}
