"""app.utils.performance 覆盖率攻坚测试

纯工具模块（LRU缓存/缓存装饰器/慢查询/批处理/性能监控），直接单元测试。
"""

import pytest

import app.utils.performance as perf
from app.utils.performance import (
    BatchProcessor,
    LRUCache,
    QueryOptimizer,
    cached,
    clear_cache,
    get_cache_stats,
    monitor_performance,
    optimize_query_decorator,
)


# ==================== LRUCache ====================


class TestLRUCache:
    def test_get_missing_key(self):
        assert LRUCache().get("nope") is None

    def test_set_and_get(self):
        c = LRUCache()
        c.set("a", 1)
        assert c.get("a") == 1

    def test_expired_entry_returns_none_and_deleted(self):
        c = LRUCache(ttl=-1)  # 立即过期
        c.set("a", 1)
        assert c.get("a") is None
        assert "a" not in c.cache
        assert "a" not in c.timestamps

    def test_get_moves_to_end(self):
        c = LRUCache()
        c.set("a", 1)
        c.set("b", 2)
        c.get("a")
        assert list(c.cache.keys()) == ["b", "a"]

    def test_set_existing_key_moves_to_end(self):
        c = LRUCache()
        c.set("a", 1)
        c.set("b", 2)
        c.set("a", 10)
        assert list(c.cache.keys()) == ["b", "a"]
        assert c.get("a") == 10

    def test_evict_oldest_when_full(self):
        c = LRUCache(maxsize=2)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)  # 驱逐最旧的 a
        assert "a" not in c.cache
        assert "a" not in c.timestamps
        assert list(c.cache.keys()) == ["b", "c"]

    def test_delete_nonexistent_is_noop(self):
        c = LRUCache()
        c.delete("ghost")  # 不抛异常

    def test_clear_and_size(self):
        c = LRUCache()
        c.set("a", 1)
        c.set("b", 2)
        assert c.size() == 2
        c.clear()
        assert c.size() == 0
        assert c.timestamps == {}


# ==================== cached 装饰器 / clear_cache / get_cache_stats ====================


class TestCachedDecorator:
    def setup_method(self):
        perf._global_cache.clear()

    def test_cache_hit_avoids_second_call(self):
        calls = []

        @cached(ttl=3600, key_prefix="t1")
        def heavy(x):
            calls.append(x)
            return x * 2

        assert heavy(3) == 6
        assert heavy(3) == 6
        assert calls == [3]  # 第二次命中缓存

    def test_different_args_not_cached(self):
        @cached(ttl=3600, key_prefix="t2")
        def heavy(x):
            return x * 2

        assert heavy(3) == 6
        assert heavy(4) == 8

    def test_clear_cache_with_prefix(self):
        @cached(key_prefix="pa")
        def fa(x):
            return x

        @cached(key_prefix="pb")
        def fb(x):
            return x

        fa(1)
        fb(1)
        clear_cache("pa")
        remaining = list(perf._global_cache.cache.keys())
        assert len(remaining) == 1
        assert remaining[0].startswith("pb")

    def test_clear_cache_all(self):
        @cached(key_prefix="pc")
        def fc(x):
            return x

        fc(1)
        clear_cache()
        assert perf._global_cache.size() == 0

    def test_get_cache_stats(self):
        perf._global_cache.set("k", "v")
        stats = get_cache_stats()
        assert stats["size"] == perf._global_cache.size()
        assert stats["maxsize"] == perf._global_cache.maxsize
        assert stats["ttl"] == perf._global_cache.ttl
        assert 0 <= stats["usage_percent"] <= 100


# ==================== QueryOptimizer ====================


class TestQueryOptimizerSlowLog:
    def test_fast_query_not_logged(self):
        qo = QueryOptimizer(slow_query_threshold=0.5)
        qo.log_query("SELECT 1", 0.1)
        assert qo.slow_queries == []

    def test_slow_query_logged_with_params(self):
        qo = QueryOptimizer(slow_query_threshold=0.5)
        qo.log_query("SELECT * FROM t", 1.2, params={"a": 1})
        assert len(qo.slow_queries) == 1
        entry = qo.slow_queries[0]
        assert entry["query"] == "SELECT * FROM t"
        assert entry["duration"] == 1.2
        assert entry["params"] == {"a": 1}
        assert entry["timestamp"] > 0

    def test_get_slow_queries_sorted_and_limited(self):
        qo = QueryOptimizer(slow_query_threshold=0.0)
        for d in (0.5, 2.0, 1.0):
            qo.log_query(f"q{d}", d)
        result = qo.get_slow_queries(limit=2)
        assert [r["duration"] for r in result] == [2.0, 1.0]

    def test_clear_slow_queries(self):
        qo = QueryOptimizer(slow_query_threshold=0.0)
        qo.log_query("q", 1.0)
        qo.clear_slow_queries()
        assert qo.slow_queries == []


# ==================== optimize_query_decorator ====================


class TestOptimizeQueryDecorator:
    def test_logs_query_and_returns_result(self, monkeypatch):
        from unittest.mock import MagicMock

        mock_qo = MagicMock()
        monkeypatch.setattr(perf, "query_optimizer", mock_qo)

        @optimize_query_decorator
        def my_query(a, b=2):
            return a + b

        assert my_query(1, b=3) == 4
        mock_qo.log_query.assert_called_once()
        kwargs = mock_qo.log_query.call_args.kwargs
        assert kwargs["query"] == "my_query"
        assert "duration" in kwargs
        assert "args" in kwargs["params"]


# ==================== BatchProcessor ====================


class TestBatchProcessor:
    def test_processes_in_batches(self):
        bp = BatchProcessor(batch_size=100)
        batches_seen = []

        def proc(batch):
            batches_seen.append(len(batch))
            return [x * 2 for x in batch]

        results = bp.process_in_batches(list(range(250)), proc)
        assert batches_seen == [100, 100, 50]
        assert results == [x * 2 for x in range(250)]

    def test_exception_propagates(self):
        bp = BatchProcessor(batch_size=2)

        def proc(batch):
            raise ValueError("bad batch")

        with pytest.raises(ValueError, match="bad batch"):
            bp.process_in_batches([1, 2], proc)


# ==================== monitor_performance ====================


class TestMonitorPerformance:
    def test_fast_function_debug_path(self):
        @monitor_performance
        def fast():
            return 42

        assert fast() == 42

    def test_slow_function_warning_path(self, monkeypatch):
        import itertools

        times = iter(itertools.chain([0.0], itertools.repeat(2.0)))  # 开始0s/结束2s → 耗时2s
        monkeypatch.setattr(perf.time, "time", lambda: next(times))

        @monitor_performance
        def slow():
            return "done"

        assert slow() == "done"

    def test_exception_still_logs_and_propagates(self):
        @monitor_performance
        def boom():
            raise RuntimeError("x")

        with pytest.raises(RuntimeError):
            boom()
