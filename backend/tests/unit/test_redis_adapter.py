"""Tests for app/core/redis_adapter.py — 目标 100% 覆盖。"""
from app.core.redis_adapter import RedisAdapter, redis_adapter


class TestRedisAdapter:
    def test_init_empty(self):
        r = RedisAdapter()
        assert r._data == {}

    def test_get_nonexistent(self):
        r = RedisAdapter()
        assert r.get("missing") is None

    def test_set_and_get(self):
        r = RedisAdapter()
        r.set("key1", "value1")
        assert r.get("key1") == "value1"

    def test_set_with_ttl(self):
        r = RedisAdapter()
        r.set("key", "val", ttl=60)
        assert r.get("key") == "val"

    def test_delete_existing(self):
        r = RedisAdapter()
        r.set("key", "val")
        assert r.delete("key") is True
        assert r.get("key") is None

    def test_delete_nonexistent(self):
        r = RedisAdapter()
        assert r.delete("missing") is True

    def test_exists(self):
        r = RedisAdapter()
        r.set("key", "val")
        assert r.exists("key") is True
        assert r.exists("missing") is False

    def test_flush(self):
        r = RedisAdapter()
        r.set("a", 1)
        r.set("b", 2)
        r.flush()
        assert r._data == {}

    def test_global_instance(self):
        assert isinstance(redis_adapter, RedisAdapter)
