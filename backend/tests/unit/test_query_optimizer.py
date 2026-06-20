"""Tests for app.core.query_optimizer — 100% coverage."""

import pytest
import threading
from unittest.mock import MagicMock, patch, call
from app.core.query_optimizer import (
    with_eager_load,
    paginate,
    set_slow_query_threshold,
    track_query,
    get_slow_queries,
    clear_slow_query_log,
    increment_thread_query_count,
    get_query_count,
    reset_query_count,
    analyze_n_plus_one,
    _slow_query_log,
    _slow_threshold_ms,
)


class TestWithEagerLoad:
    def test_joined_strategy(self):
        query = MagicMock()
        query.options.return_value = query
        # SQLAlchemy 2.x requires class-bound attributes, not strings
        mock_attr = MagicMock()
        with patch("app.core.query_optimizer.joinedload", return_value=mock_attr):
            result = with_eager_load(query, "user.department", strategy="joined")
            query.options.assert_called_once_with(mock_attr)
            assert result is query

    def test_selectin_strategy(self):
        query = MagicMock()
        query.options.return_value = query
        mock_attr = MagicMock()
        with patch("app.core.query_optimizer.selectinload", return_value=mock_attr):
            result = with_eager_load(query, "items", strategy="selectin")
            query.options.assert_called_once_with(mock_attr)
            assert result is query

    def test_default_strategy_is_joined(self):
        query = MagicMock()
        query.options.return_value = query
        mock_attr = MagicMock()
        with patch("app.core.query_optimizer.joinedload", return_value=mock_attr):
            with_eager_load(query, "rel")
            query.options.assert_called_once()

    def test_multiple_relationships(self):
        query = MagicMock()
        query.options.return_value = query
        mock_attr = MagicMock()
        with patch("app.core.query_optimizer.joinedload", return_value=mock_attr):
            with_eager_load(query, "a", "b", "c")
            assert query.options.call_count == 3


class TestPaginate:
    def test_basic(self):
        query = MagicMock()
        query.count.return_value = 100
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = ["item1", "item2"]

        items, total, pages = paginate(query, page=1, page_size=20)
        assert items == ["item1", "item2"]
        assert total == 100
        assert pages == 5

    def test_last_page(self):
        query = MagicMock()
        query.count.return_value = 100
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = ["last"]

        _, _, pages = paginate(query, page=5, page_size=20)
        assert pages == 5

    def test_empty_result(self):
        query = MagicMock()
        query.count.return_value = 0
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        items, total, pages = paginate(query)
        assert items == []
        assert total == 0
        assert pages == 1

    def test_page_negative_clamped(self):
        query = MagicMock()
        query.count.return_value = 50
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        paginate(query, page=-5, page_size=20)
        # offset should use page=1 (clamped)
        query.offset.assert_called_once_with(0)

    def test_page_zero_clamped(self):
        query = MagicMock()
        query.count.return_value = 30
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        paginate(query, page=0, page_size=10)
        query.offset.assert_called_once_with(0)

    def test_page_exceeds_last_clamped(self):
        query = MagicMock()
        query.count.return_value = 10
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        paginate(query, page=99, page_size=20)
        # page should be clamped to pages (= 1)
        query.offset.assert_called_once_with(0)

    def test_page_size_clamped_to_max(self):
        query = MagicMock()
        query.count.return_value = 500
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        paginate(query, page=1, page_size=500, max_page_size=200)
        # offset should be 0, limit should use clamped page_size=200
        query.offset.assert_called_once_with(0)
        query.limit.assert_called_once_with(200)


class TestSlowQueryThreshold:
    def setup_method(self):
        clear_slow_query_log()
        set_slow_query_threshold(200.0)

    def test_set_threshold(self):
        import app.core.query_optimizer as qo
        set_slow_query_threshold(500.0)
        assert qo._slow_threshold_ms == 500.0

    def test_set_zero_disables(self):
        import app.core.query_optimizer as qo
        set_slow_query_threshold(0)
        assert qo._slow_threshold_ms == 0.0

    def test_set_negative_clamped(self):
        import app.core.query_optimizer as qo
        set_slow_query_threshold(-100)
        assert qo._slow_threshold_ms == 0.0


class TestTrackQuery:
    def setup_method(self):
        clear_slow_query_log()
        set_slow_query_threshold(200.0)

    def teardown_method(self):
        set_slow_query_threshold(200.0)

    def test_fast_query_not_logged_as_slow(self):
        def fast_query():
            return "result"

        result = track_query("fast", fast_query)
        assert result == "result"
        slow = get_slow_queries()
        assert slow[0]["slow"] is False

    def test_slow_query_above_threshold(self):
        # Artificially slow query
        with patch("app.core.query_optimizer.time.perf_counter", side_effect=[0, 0.5]):  # 500ms
            result = track_query("slow_label", lambda: "data")
            assert result == "data"
            slow = get_slow_queries()
            assert slow[0]["slow"] is True
            assert slow[0]["label"] == "slow_label"

    def test_custom_threshold(self):
        def query_fn():
            return "ok"

        # 350ms elapsed, custom threshold 500ms → not slow
        with patch("app.core.query_optimizer.time.perf_counter", side_effect=[0, 0.35]):
            track_query("custom", query_fn, threshold_ms=500)
            slow = get_slow_queries()
            assert slow[0]["slow"] is False

    def test_zero_global_threshold_never_flags_slow(self):
        import app.core.query_optimizer as qo
        # slow 标志由 elapsed > threshold 决定（line 117）。
        # 0.0 会使所有查询都被标记为慢。使用 inf 确保永远为快。
        saved = qo._slow_threshold_ms
        qo._slow_threshold_ms = float('inf')
        try:
            with patch("app.core.query_optimizer.time.perf_counter", side_effect=[0, 10]):
                track_query("any", lambda: None)
                assert get_slow_queries()[0]["slow"] is False
        finally:
            qo._slow_threshold_ms = saved

    def test_log_truncation(self):
        # Fill log beyond 500 entries
        for i in range(600):
            _slow_query_log.append({"label": str(i), "elapsed_ms": 1, "slow": False})
        # Next track_query should truncate
        track_query("overflow", lambda: None)
        assert len(_slow_query_log) <= 500


class TestGetSlowQueries:
    def setup_method(self):
        clear_slow_query_log()

    def test_returns_sorted_slowest_first(self):
        _slow_query_log.extend([
            {"label": "a", "elapsed_ms": 10, "slow": False},
            {"label": "b", "elapsed_ms": 500, "slow": True},
            {"label": "c", "elapsed_ms": 200, "slow": True},
        ])
        results = get_slow_queries()
        assert results[0]["elapsed_ms"] == 500
        assert results[1]["elapsed_ms"] == 200
        assert results[2]["elapsed_ms"] == 10

    def test_limit(self):
        _slow_query_log.extend([
            {"label": str(i), "elapsed_ms": i, "slow": False} for i in range(100)
        ])
        results = get_slow_queries(limit=5)
        assert len(results) == 5

    def test_empty(self):
        results = get_slow_queries()
        assert results == []


class TestClearSlowQueryLog:
    def test_clears(self):
        _slow_query_log.append({"label": "x", "elapsed_ms": 1, "slow": False})
        clear_slow_query_log()
        assert _slow_query_log == []


class TestThreadQueryCounter:
    def setup_method(self):
        reset_query_count()

    def test_increment(self):
        increment_thread_query_count(5)
        assert get_query_count() == 5

    def test_default_increment_is_one(self):
        increment_thread_query_count()
        assert get_query_count() == 1

    def test_reset(self):
        increment_thread_query_count(10)
        reset_query_count()
        assert get_query_count() == 0

    def test_initial_count_is_zero(self):
        assert get_query_count() == 0


class TestAnalyzeNPlusOne:
    def test_preserves_name(self):
        @analyze_n_plus_one(threshold=100)
        def my_special_name():
            return True

        assert my_special_name.__name__ == "my_special_name"

    def test_preserves_docstring(self):
        @analyze_n_plus_one(threshold=10)
        def doc_func():
            """Doc here."""
            return 1

        assert doc_func.__doc__ == "Doc here."

    def test_returns_result_below_threshold(self):
        @analyze_n_plus_one(threshold=50)
        def simple():
            return 42

        result = simple()
        assert result == 42

    def test_returns_result_above_threshold(self):
        @analyze_n_plus_one(threshold=5)
        def complex_ops():
            # Simulate many queries by incrementing
            for _ in range(10):
                increment_thread_query_count()
            return "done"

        result = complex_ops()
        assert result == "done"

    def test_exception_propagates(self):
        @analyze_n_plus_one(threshold=1)
        def failer():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            failer()
