"""Tests for offline fault tolerance retry utility."""

import pytest
from app.utils.retry import retry_on_lock, safe_import


class TestRetryOnLock:
    def test_retry_success_first_attempt(self):
        """Function succeeds immediately — single call, no retry."""
        call_count = [0]

        @retry_on_lock(max_retries=3, base_delay=0.01)
        def succeed():
            call_count[0] += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count[0] == 1

    def test_retry_on_lock_error(self):
        """Raises after max_retries when DB is locked."""
        call_count = [0]

        @retry_on_lock(max_retries=3, base_delay=0.01)
        def always_locked():
            call_count[0] += 1
            raise Exception("database is locked")

        with pytest.raises(Exception, match="database is locked"):
            always_locked()
        assert call_count[0] == 3

    def test_no_retry_on_other_errors(self):
        """Non-lock errors raise immediately without retry."""
        call_count = [0]

        @retry_on_lock(max_retries=3, base_delay=0.01)
        def other_error():
            call_count[0] += 1
            raise ValueError("bad data")

        with pytest.raises(ValueError, match="bad data"):
            other_error()
        assert call_count[0] == 1

    def test_retry_eventually_succeeds(self):
        """Succeeds on 2nd attempt after one lock error."""
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


class TestSafeImport:
    def test_safe_import_existing_module(self):
        mod = safe_import("os.path")
        assert mod is not None

    def test_safe_import_nonexistent_module(self):
        mod = safe_import("nonexistent.module.xyz")
        assert mod is None
