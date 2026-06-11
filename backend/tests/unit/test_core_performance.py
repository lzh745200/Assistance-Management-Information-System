import asyncio
from unittest.mock import patch

import pytest

from app.core.performance import _metrics, get_metrics, measure, reset_metrics, timed


@pytest.fixture(autouse=True)
def clear_metrics():
    reset_metrics()
    yield
    reset_metrics()


def _module_level_fn():
    return 42


class TestTimed:
    def test_sync_function_default_name(self):
        @timed()
        def my_func():
            return 42

        assert my_func() == 42
        timings = _metrics["timings"]
        assert len(timings) == 1
        assert "my_func" in timings[0][0]
        assert timings[0][1] > 0
        assert _metrics["counters"].get("my_func", _metrics["counters"].get(timings[0][0])) == 1

    def test_sync_function_custom_name(self):
        @timed("custom_label")
        def another_func():
            return "ok"

        assert another_func() == "ok"
        timings = _metrics["timings"]
        assert timings[0][0] == "custom_label"
        assert _metrics["counters"]["custom_label"] == 1

    def test_sync_function_log_slow_warning(self):
        @timed("slow_op", log_slow_ms=0.001)
        def not_so_fast():
            import time
            time.sleep(0.01)
            return 1

        _metrics["timings"].clear()
        _metrics["counters"].clear()

        with patch("app.core.performance.logger.warning") as mock_warn:
            assert not_so_fast() == 1
            mock_warn.assert_called_once()

    def test_sync_function_log_debug(self):
        @timed("fast_op", log_slow_ms=999999)
        def super_fast():
            return 1

        _metrics["timings"].clear()
        _metrics["counters"].clear()

        with patch("app.core.performance.logger.debug") as mock_debug:
            assert super_fast() == 1
            mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_function(self):
        @timed("async_fn")
        async def my_async():
            await asyncio.sleep(0.001)
            return "done"

        result = await my_async()
        assert result == "done"
        timings = _metrics["timings"]
        assert len(timings) == 1
        assert timings[0][0] == "async_fn"

    @pytest.mark.asyncio
    async def test_async_function_log_slow(self):
        @timed("async_slow", log_slow_ms=0.001)
        async def slow_async():
            await asyncio.sleep(0.005)
            return "slow"

        _metrics["timings"].clear()
        _metrics["counters"].clear()

        with patch("app.core.performance.logger.warning") as mock_warn:
            result = await slow_async()
            assert result == "slow"
            mock_warn.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_function_no_slow_flag(self):
        @timed("async_fast")
        async def fast_async():
            return "fast"

        _metrics["timings"].clear()
        _metrics["counters"].clear()

        with patch("app.core.performance.logger.debug") as mock_debug:
            result = await fast_async()
            assert result == "fast"
            mock_debug.assert_called_once()

    def test_counter_increment(self):
        @timed("counter_test")
        def fn2():
            pass

        fn2()
        fn2()
        fn2()
        assert _metrics["counters"]["counter_test"] == 3
        assert len(_metrics["timings"]) == 3


class TestMeasure:
    def test_context_manager_logs_duration(self):
        with patch("app.core.performance.logger.debug") as mock_debug:
            with measure("test_block"):
                pass
            mock_debug.assert_called_once()

    def test_context_manager_with_exception(self):
        with patch("app.core.performance.logger.debug") as mock_debug:
            try:
                with measure("failing_block"):
                    raise ValueError("test error")
            except ValueError:
                pass
            mock_debug.assert_called_once()

    def test_context_manager_default_name(self):
        with patch("app.core.performance.logger.debug"):
            with measure():
                pass


class TestMetrics:
    def test_get_metrics_with_data(self):
        @timed("metric_test")
        def fn():
            pass

        fn()

        metrics = get_metrics()
        assert metrics["timing_count"] == 1
        assert metrics["avg_ms"] is not None
        assert metrics["slowest"] is not None
        assert "metric_test" in metrics["slowest"][0]
        assert metrics["fastest"] is not None
        assert "metric_test" in metrics["fastest"][0]
        assert metrics["counters"]["metric_test"] == 1

    def test_get_metrics_empty(self):
        _metrics["timings"].clear()
        _metrics["counters"].clear()
        metrics = get_metrics()
        assert metrics["timing_count"] == 0
        assert metrics["avg_ms"] is None
        assert metrics["slowest"] is None
        assert metrics["fastest"] is None
        assert metrics["counters"] == {}

    def test_get_metrics_last_500_only(self):
        for i in range(600):
            _metrics["timings"].append((f"fn_{i}", float(i)))
        metrics = get_metrics()
        assert metrics["timing_count"] == 500
        # slowest should be the one with max time among last 500
        assert metrics["slowest"][0] == "fn_599"

    def test_reset_metrics(self):
        _metrics["timings"].append(("test", 1.0))
        _metrics["counters"]["test"] = 1
        with patch("app.core.performance.logger.info") as mock_info:
            reset_metrics()
            mock_info.assert_called_once()
        assert _metrics["timings"] == []
        assert _metrics["counters"] == {}
