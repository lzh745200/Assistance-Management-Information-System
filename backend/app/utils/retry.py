"""Retry utilities for offline standalone fault tolerance."""

import functools
import logging
import time

logger = logging.getLogger(__name__)


def retry_on_lock(max_retries: int = 3, base_delay: float = 0.1):
    """Retry on SQLite 'database is locked' with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default 3).
        base_delay: Initial delay in seconds, doubles each retry (default 0.1).

    Example:
        @retry_on_lock(max_retries=3)
        def write_to_db(session, data):
            session.add(data)
            session.commit()
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "database is locked" not in str(e).lower():
                        raise
                    if attempt == max_retries - 1:
                        logger.error(
                            "DB locked after %d retries, giving up: %s", max_retries, e
                        )
                        raise
                    delay = base_delay * (4**attempt)
                    logger.warning(
                        "DB locked, retry %d/%d in %.1fs",
                        attempt + 1,
                        max_retries,
                        delay,
                    )
                    time.sleep(delay)
            return None  # unreachable

        return wrapper

    return decorator


def safe_import(module_path: str, name: str = None):
    """Import a module gracefully; return None if unavailable.

    Args:
        module_path: e.g. 'app.services.monitoring_service'
        name: Optional attribute name to return from the module.

    Returns:
        Module, attribute, or None if import failed.
    """
    import importlib

    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, name) if name else mod
    except ImportError as e:
        logger.warning("Optional module unavailable: %s (%s)", module_path, e)
        return None
