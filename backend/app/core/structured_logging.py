"""Structured logging utilities.

Provides helper functions for emitting JSON-formatted log entries and
binding contextual metadata (user ID, request ID, etc.) to log records.
"""

import logging
from typing import Any, Dict, Optional


class _StructuredContext:
    """Thread-local context storage for structured logging metadata."""

    def __init__(self):
        import threading
        self._store = threading.local()

    @property
    def data(self) -> Dict[str, Any]:
        if not hasattr(self._store, "data"):
            self._store.data = {}
        return self._store.data

    def set(self, **kwargs) -> None:
        self.data.update(kwargs)

    def get(self, key: str, default=None) -> Any:
        return self.data.get(key, default)

    def clear(self) -> None:
        if hasattr(self._store, "data"):
            self._store.data.clear()


_context = _StructuredContext()

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def bind_context(**kwargs) -> None:
    """Bind key-value pairs to the current processing context.

    These values will be included in subsequent structured log entries
    emitted from the same thread.

    Usage::

        bind_context(user_id=42, request_id="abc123")
    """
    _context.set(**kwargs)


def clear_context() -> None:
    """Clear all bound context data for the current thread."""
    _context.clear()


def get_context() -> Dict[str, Any]:
    """Return a copy of the current structured context."""
    return dict(_context.data)


# ---------------------------------------------------------------------------
# Structured logger
# ---------------------------------------------------------------------------


class StructuredLogger:
    """A logger wrapper that emits JSON-formatted messages.

    Usage::

        slog = StructuredLogger(__name__)
        slog.info("用户登录", user_id=42)
    """

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def _log(self, level: int, msg: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Merge context data with extra fields and emit."""
        payload = dict(_context.data)
        if extra:
            payload.update(extra)

        import json as _json

        if payload:
            full = f"{msg} | {_json.dumps(payload, ensure_ascii=False, default=str)}"
        else:
            full = msg
        self._logger.log(level, full)

    def debug(self, msg: str, **kwargs) -> None:
        self._log(logging.DEBUG, msg, kwargs)

    def info(self, msg: str, **kwargs) -> None:
        self._log(logging.INFO, msg, kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        self._log(logging.WARNING, msg, kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self._log(logging.ERROR, msg, kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        self._log(logging.CRITICAL, msg, kwargs)

    def exception(self, msg: str, **kwargs) -> None:
        """Log an exception with traceback."""
        payload = dict(_context.data)
        payload.update(kwargs)
        import json as _json
        full = f"{msg} | {_json.dumps(payload, ensure_ascii=False, default=str)}"
        self._logger.exception(full)


# ---------------------------------------------------------------------------
# Log sanitization
# ---------------------------------------------------------------------------

SENSITIVE_KEYS = {"password", "secret", "token", "authorization", "key"}


def sanitize(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of *data* with sensitive values redacted.

    Args:
        data: A dictionary that may contain sensitive keys.

    Returns:
        A new dictionary with sensitive values replaced by ``[REDACTED]``.
    """
    return {
        k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS or any(s in k.lower() for s in SENSITIVE_KEYS) else v
        for k, v in data.items()
    }
