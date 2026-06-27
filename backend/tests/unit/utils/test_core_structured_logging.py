"""
结构化日志测试

测试 app/core/structured_logging.py 模块
"""
import pytest
from app.core.structured_logging import (
    bind_context,
    clear_context,
    get_context,
    StructuredLogger,
    sanitize,
    SENSITIVE_KEYS,
)


class TestStructuredContext:
    def setup_method(self):
        clear_context()

    def test_bind_and_get_context(self):
        bind_context(user_id=42, request_id="abc")
        ctx = get_context()
        assert ctx == {"user_id": 42, "request_id": "abc"}

    def test_bind_merge(self):
        bind_context(user_id=1)
        bind_context(request_id="xyz")
        assert get_context() == {"user_id": 1, "request_id": "xyz"}

    def test_bind_overwrite(self):
        bind_context(user_id=1)
        bind_context(user_id=2)
        assert get_context()["user_id"] == 2

    def test_clear_context(self):
        bind_context(user_id=42)
        clear_context()
        assert get_context() == {}

    def test_get_context_returns_copy(self):
        bind_context(user_id=42)
        ctx = get_context()
        ctx["extra"] = "should_not_appear"
        assert "extra" not in get_context()

    def test_clear_empty_context(self):
        clear_context()
        assert get_context() == {}


class TestStructuredLogger:
    def test_logger_basic_levels(self, caplog):
        slog = StructuredLogger("test_logger")
        caplog.set_level(0)
        slog.debug("debug msg", key="val")
        slog.info("info msg", extra_field=1)
        slog.warning("warn msg")
        slog.error("err msg")
        assert len(caplog.records) == 4
        assert caplog.records[1].message == 'info msg | {"extra_field": 1}'

    def test_logger_with_context(self, caplog):
        clear_context()
        bind_context(global_id=99)
        slog = StructuredLogger("test_logger")
        caplog.set_level(0)
        slog.info("with ctx", local="data")
        assert "global_id" in caplog.records[0].message
        assert "local" in caplog.records[0].message

    def test_logger_no_extra(self, caplog):
        clear_context()
        slog = StructuredLogger("test_logger")
        caplog.set_level(0)
        slog.info("plain message")
        assert caplog.records[0].message == "plain message"

    def test_critical(self, caplog):
        slog = StructuredLogger("test_logger")
        caplog.set_level(0)
        slog.critical("critical msg")
        assert caplog.records[0].levelname == "CRITICAL"

    def test_exception(self, caplog):
        slog = StructuredLogger("test_logger")
        caplog.set_level(0)
        try:
            raise ValueError("test error")
        except ValueError:
            slog.exception("exception caught", error_info="broken")
        assert "exception caught" in caplog.records[0].message
        assert "error_info" in caplog.records[0].message


class TestSanitize:
    def test_sanitize_password(self):
        result = sanitize({"password": "secret123", "user": "admin"})
        assert result["password"] == "[REDACTED]"
        assert result["user"] == "admin"

    def test_sanitize_token_and_secret(self):
        result = sanitize({"token": "abc", "secret_key": "xyz", "name": "test"})
        assert result["token"] == "[REDACTED]"
        assert result["secret_key"] == "[REDACTED]"
        assert result["name"] == "test"

    def test_sanitize_authorization(self):
        result = sanitize({"Authorization": "Bearer xxx", "content": "hello"})
        assert result["Authorization"] == "[REDACTED]"

    def test_sanitize_empty(self):
        result = sanitize({})
        assert result == {}

    def test_sanitize_no_sensitive(self):
        result = sanitize({"name": "test", "count": 42})
        assert result == {"name": "test", "count": 42}

    def test_sanitize_case_insensitive(self):
        result = sanitize({"Password": "secret", "TOKEN": "abc"})
        assert result["Password"] == "[REDACTED]"
        assert result["TOKEN"] == "[REDACTED]"

    def test_sanitize_partial_match(self):
        result = sanitize({"my_password": "secret", "auth_token": "abc", "normal": "ok"})
        assert result["my_password"] == "[REDACTED]"
        assert result["auth_token"] == "[REDACTED]"
        assert result["normal"] == "ok"
