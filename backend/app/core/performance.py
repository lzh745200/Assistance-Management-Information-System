"""Performance monitoring.

Provides lightweight decorators and context managers for measuring
execution time, counting calls, and tracking memory usage.
"""

import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# In-memory metrics store
_metrics: Dict[str, list] = {
    "timings": [],   # (name, elapsed_ms)
    "counters": {},  # name -> count
}


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------


def timed(name: Optional[str] = None, *, log_slow_ms: float = 0):
    """Decorator that logs the execution time of a function.

    Usage::

        @timed("my_func")
        def my_func():
            ...

    Args:
        name: Label used in the log message (defaults to func.__qualname__).
        log_slow_ms: If > 0, only emit a WARNING when elapsed > threshold.
    """

    def decorator(func: Callable) -> Callable:
        label = name or func.__qualname__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            _metrics["timings"].append((label, elapsed))
            _metrics["counters"][label] = _metrics["counters"].get(label, 0) + 1
            if log_slow_ms > 0 and elapsed > log_slow_ms:
                logger.warning("慢操作 %s: %.2f ms", label, elapsed)
            else:
                logger.debug("%s: %.2f ms", label, elapsed)
            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            _metrics["timings"].append((label, elapsed))
            _metrics["counters"][label] = _metrics["counters"].get(label, 0) + 1
            if log_slow_ms > 0 and elapsed > log_slow_ms:
                logger.warning("慢操作 %s: %.2f ms", label, elapsed)
            else:
                logger.debug("%s: %.2f ms", label, elapsed)
            return result

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


@contextmanager
def measure(name: str = "block"):
    """Context manager that logs the duration of a code block.

    Usage::

        with measure("expensive_loop"):
            ...
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug("%s: %.2f ms", name, elapsed)


# ---------------------------------------------------------------------------
# Metrics accessors
# ---------------------------------------------------------------------------


def get_metrics() -> Dict[str, Any]:
    """Return a snapshot of the current performance metrics."""
    timings = _metrics["timings"][-500:]  # last 500
    if timings:
        avg = sum(t[1] for t in timings) / len(timings)
        slowest = max(timings, key=lambda x: x[1])
        fastest = min(timings, key=lambda x: x[1])
    else:
        avg = slowest = fastest = None
    return {
        "timing_count": len(timings),
        "avg_ms": round(avg, 2) if avg else None,
        "slowest": (slowest[0], round(slowest[1], 2)) if slowest else None,
        "fastest": (fastest[0], round(fastest[1], 2)) if fastest else None,
        "counters": dict(_metrics["counters"]),
    }


def reset_metrics() -> None:
    """Clear all performance metrics."""
    _metrics["timings"].clear()
    _metrics["counters"].clear()
    logger.info("性能指标已重置")
