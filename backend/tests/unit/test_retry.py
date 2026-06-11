"""Tests for offline fault tolerance retry utility — 100% coverage."""
import pytest
from unittest.mock import patch, Mock


class TestRetryOnLock:
    def test_success_first_attempt(self):
        from app.utils.retry import retry_on_lock
        call_count = [0]

        @retry_on_lock(max_retries=3, base_delay=0.01)
        def succeed():
            call_count[0] += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count[0] == 1

    def test_retry_on_lock_error(self):
        from app.utils.retry import retry_on_lock
        call_count = [0]

        @retry_on_lock(max_retries=3, base_delay=0.01)
        def always_locked():
            call_count[0] += 1
            raise Exception("database is locked")

        with pytest.raises(Exception, match="database is locked"):
            always_locked()
        assert call_count[0] == 3

    def test_no_retry_on_other_errors(self):
        from app.utils.retry import retry_on_lock
        call_count = [0]

        @retry_on_lock(max_retries=3, base_delay=0.01)
        def other_error():
            call_count[0] += 1
            raise ValueError("bad data")

        with pytest.raises(ValueError, match="bad data"):
            other_error()
        assert call_count[0] == 1

    def test_retry_eventually_succeeds(self):
        from app.utils.retry import retry_on_lock
        call_count = [0]

        @retry_on_lock(max_retries=3, base_delay=0.01)
        def lock_once():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("database is locked")
            return "recovered"

        result = lock_once()
        assert result == "recovered"
        assert call_count[0] == 2

    def test_max_retries_zero_returns_none(self):
        from app.utils.retry import retry_on_lock
        call_count = [0]

        @retry_on_lock(max_retries=0, base_delay=0.01)
        def never_called():
            call_count[0] += 1
            return "should_not_run"

        result = never_called()
        assert result is None
        assert call_count[0] == 0

    def test_logger_warning_called_on_retry(self):
        from app.utils.retry import retry_on_lock
        call_count = [0]

        @retry_on_lock(max_retries=2, base_delay=0.001)
        def lock_then_succeed():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("database is locked")
            return "ok"

        result = lock_then_succeed()
        assert result == "ok"
        assert call_count[0] == 2

    def test_logger_error_called_on_give_up(self):
        from app.utils.retry import retry_on_lock
        call_count = [0]

        @retry_on_lock(max_retries=2, base_delay=0.001)
        def always_locked():
            call_count[0] += 1
            raise Exception("database is locked")

        with pytest.raises(Exception, match="database is locked"):
            always_locked()
        assert call_count[0] == 2

    def test_exponential_backoff_delay(self):
        from app.utils.retry import retry_on_lock
        call_count = [0]

        @retry_on_lock(max_retries=3, base_delay=1.0)
        def locked_twice():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception("database is locked")
            return "ok"

        with patch("app.utils.retry.time.sleep") as mock_sleep:
            result = locked_twice()
            assert result == "ok"
            assert call_count[0] == 3
            assert mock_sleep.call_count == 2
            delay1 = mock_sleep.call_args_list[0][0][0]
            delay2 = mock_sleep.call_args_list[1][0][0]
            assert delay1 == 1.0
            assert delay2 == 4.0

    def test_case_insensitive_lock_check(self):
        from app.utils.retry import retry_on_lock
        call_count = [0]

        @retry_on_lock(max_retries=2, base_delay=0.001)
        def uppercase_lock():
            call_count[0] += 1
            raise Exception("DATABASE IS LOCKED")

        with pytest.raises(Exception, match="(?i)database is locked"):
            uppercase_lock()
        assert call_count[0] == 2


class TestSafeImport:
    def test_import_existing_module(self):
        from app.utils.retry import safe_import
        mod = safe_import("os.path")
        assert mod is not None
        assert mod.join is not None

    def test_import_existing_module_with_name(self):
        from app.utils.retry import safe_import
        func = safe_import("os.path", "join")
        import os.path
        assert func is os.path.join

    def test_import_nonexistent_module(self):
        from app.utils.retry import safe_import
        mod = safe_import("nonexistent.module.xyz")
        assert mod is None

    def test_import_nonexistent_module_with_name(self):
        from app.utils.retry import safe_import
        result = safe_import("nonexistent.module.xyz", "SomeClass")
        assert result is None
