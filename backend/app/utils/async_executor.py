"""
异步执行器 — 将 CPU/IO 密集型同步操作安全地转移到线程池。

避免在 FastAPI async 路由中直接执行同步阻塞操作（文件 I/O、加密、大 JSON 解析、
Excel/PDF 生成等），防止阻塞 Event Loop 导致所有请求排队。

Usage:
    from app.utils.async_executor import run_in_thread

    # 在 async 路由中
    result = await run_in_thread(sync_heavy_function, arg1, arg2)

或者用作装饰器:
    from app.utils.async_executor import asyncify

    @asyncify
    def generate_large_report(data: list) -> bytes:
        ...  # 同步代码
"""

import asyncio
import functools
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# 全局线程池 — 限制并发以避免 SQLite 写冲突
_MAX_WORKERS = 4
_executor: Optional[ThreadPoolExecutor] = None


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=_MAX_WORKERS,
            thread_name_prefix="async-cpu",
        )
    return _executor


async def run_in_thread(
    func: Callable[..., T],
    *args,
    timeout: float = 120.0,
    log_slow_ms: float = 2000,
    **kwargs,
) -> T:
    """在线程池中执行同步函数，返回协程可等待的结果。

    Args:
        func: 同步函数
        *args: 位置参数
        timeout: 超时秒数
        log_slow_ms: 超过此阈值（毫秒）时记录 WARNING
        **kwargs: 关键字参数

    Returns:
        函数返回值

    Raises:
        TimeoutError: 超时
    """
    loop = asyncio.get_running_loop()
    name = getattr(func, "__qualname__", getattr(func, "__name__", str(func)))
    start = time.perf_counter()

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(
                _get_executor(),
                functools.partial(func, *args, **kwargs),
            ),
            timeout=timeout,
        )
        elapsed = (time.perf_counter() - start) * 1000
        if elapsed > log_slow_ms:
            logger.warning(
                "慢线程操作 %s: %.0fms (timeout=%.0fs)",
                name, elapsed, timeout,
            )
        else:
            logger.debug("线程操作 %s: %.0fms", name, elapsed)
        return result
    except asyncio.TimeoutError:
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(
            "线程操作超时 %s: %.0fms (timeout=%.0fs)",
            name, elapsed, timeout,
        )
        raise TimeoutError(f"操作超时（{timeout}秒）: {name}")


def asyncify(func: Callable[..., T]) -> Callable[..., "asyncio.Future[T]"]:
    """装饰器：将同步函数包装为异步版本。

    Usage:
        @asyncify
        def heavy_encrypt(data: bytes, key: bytes) -> bytes:
            ...

        # 现在可以作为 await 调用
        result = await heavy_encrypt(data, key)
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await run_in_thread(func, *args, **kwargs)

    return wrapper


def get_executor_stats() -> dict:
    """获取线程池统计信息（用于监控）"""
    ex = _executor
    if ex is None:
        return {"workers": 0, "pending": 0}
    return {
        "max_workers": _MAX_WORKERS,
        "pending": getattr(ex, "_work_queue", None) and ex._work_queue.qsize() or 0,
    }
