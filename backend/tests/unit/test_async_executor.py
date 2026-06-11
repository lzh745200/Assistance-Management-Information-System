"""Tests for app/utils/async_executor.py — 100% coverage."""
import time

import pytest


class TestGetExecutor:
    """_get_executor — lazy ThreadPoolExecutor singleton."""

    def test_returns_thread_pool_executor(self):
        from app.utils.async_executor import _get_executor
        from concurrent.futures import ThreadPoolExecutor
        ex = _get_executor()
        assert isinstance(ex, ThreadPoolExecutor)

    def test_singleton(self):
        from app.utils.async_executor import _get_executor
        ex1 = _get_executor()
        ex2 = _get_executor()
        assert ex1 is ex2


class TestRunInThread:
    """run_in_thread — execute sync function in thread pool."""

    async def test_successful_execution(self):
        from app.utils.async_executor import run_in_thread

        def sync_add(a, b):
            return a + b

        result = await run_in_thread(sync_add, 2, 3)
        assert result == 5

    async def test_with_kwargs(self):
        from app.utils.async_executor import run_in_thread

        def sync_kwargs(a, b=10):
            return a * b

        result = await run_in_thread(sync_kwargs, 5, b=20)
        assert result == 100

    async def test_lambda_func(self):
        from app.utils.async_executor import run_in_thread

        result = await run_in_thread(lambda x: x * 2, 7)
        assert result == 14

    async def test_slow_operation_logs_warning(self, caplog):
        import logging
        caplog.set_level(logging.WARNING)
        from app.utils.async_executor import run_in_thread

        def slow_func():
            time.sleep(0.01)
            return "done"

        result = await run_in_thread(slow_func, log_slow_ms=1)
        assert result == "done"
        assert len(caplog.records) > 0
        assert "慢线程操作" in caplog.text or "slow_func" in caplog.text

    async def test_timeout_raises_error(self):
        from app.utils.async_executor import run_in_thread

        def never_ending():
            time.sleep(100)
            return "done"

        with pytest.raises(TimeoutError, match="超时"):
            await run_in_thread(never_ending, timeout=0.1)

    async def test_debug_log_fast_op(self, caplog):
        import logging
        caplog.set_level(logging.DEBUG)
        from app.utils.async_executor import run_in_thread

        def fast_func():
            return "fast"

        result = await run_in_thread(fast_func, log_slow_ms=100000)
        assert result == "fast"
        assert any("线程操作" in rec.message for rec in caplog.records)

    async def test_exception_propagates(self):
        from app.utils.async_executor import run_in_thread

        def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await run_in_thread(failing_func)

    async def test_class_method(self):
        from app.utils.async_executor import run_in_thread

        class MyClass:
            @staticmethod
            def compute(x):
                return x * x

        result = await run_in_thread(MyClass.compute, 6)
        assert result == 36


class TestAsyncify:
    """asyncify decorator — wraps sync function into async."""

    async def test_asyncify_decorator(self):
        from app.utils.async_executor import asyncify

        @asyncify
        def sync_heavy(data: list) -> int:
            return sum(data)

        result = await sync_heavy([1, 2, 3, 4, 5])
        assert result == 15

    async def test_asyncify_preserves_name(self):
        from app.utils.async_executor import asyncify

        @asyncify
        def my_custom_func():
            return 42

        assert my_custom_func.__name__ == "my_custom_func"
        assert my_custom_func.__wrapped__ is not None

    async def test_asyncify_with_args_kwargs(self):
        from app.utils.async_executor import asyncify

        @asyncify
        def concat(sep, *items):
            return sep.join(items)

        result = await concat(",", "a", "b", "c")
        assert result == "a,b,c"


class TestGetExecutorStats:
    """get_executor_stats — thread pool monitoring."""

    def test_executor_not_initialized(self):
        from app.utils.async_executor import get_executor_stats
        from app.utils.async_executor import _executor
        old = _executor
        try:
            import app.utils.async_executor as m
            m._executor = None
            stats = get_executor_stats()
            assert stats == {"workers": 0, "pending": 0}
        finally:
            m._executor = old

    def test_executor_initialized(self):
        from app.utils.async_executor import _get_executor, get_executor_stats
        _get_executor()
        stats = get_executor_stats()
        assert stats["max_workers"] == 4
        assert "pending" in stats
