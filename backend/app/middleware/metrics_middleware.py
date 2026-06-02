"""
指标采集中间件（ASGI 原生实现）

收集 HTTP 请求性能指标：
- 请求计数（按方法、路径、状态码）
- 请求耗时统计
- 活跃请求数

指标通过内存计数器存储，供 /metrics 端点查询。
"""

import logging
import time
import threading

logger = logging.getLogger(__name__)

# 不采集指标的路径前缀
_SKIP_PREFIXES = (
    "/health",
    "/metrics",
    "/favicon.ico",
)


class _MetricsStore:
    """线程安全的指标存储"""

    def __init__(self):
        self._lock = threading.Lock()
        self.request_count = 0
        self.error_count = 0
        self.active_requests = 0
        self.total_duration = 0.0
        self._path_counts = {}  # (method, status) -> count

    def record(self, method: str, path: str, status: int, duration: float):
        with self._lock:
            self.request_count += 1
            self.total_duration += duration
            if status >= 400:
                self.error_count += 1
            key = (method, status)
            self._path_counts[key] = self._path_counts.get(key, 0) + 1

    def inc_active(self):
        with self._lock:
            self.active_requests += 1

    def dec_active(self):
        with self._lock:
            self.active_requests -= 1

    def get_summary(self) -> dict:
        with self._lock:
            avg_duration = (
                self.total_duration / self.request_count
                if self.request_count > 0
                else 0.0
            )
            return {
                "request_count": self.request_count,
                "error_count": self.error_count,
                "active_requests": self.active_requests,
                "avg_duration": round(avg_duration, 3),
                "by_method_status": {
                    f"{m}_{s}": c for (m, s), c in self._path_counts.items()
                },
            }


# 全局指标存储（单例）
metrics_store = _MetricsStore()


class MetricsMiddleware:
    """
    ASGI 指标采集中间件

    用法: app.add_middleware(MetricsMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # 跳过不需要采集的路径
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "?")
        start_time = time.time()
        status_code = 0

        metrics_store.inc_active()

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration = time.time() - start_time
            metrics_store.record(method, path, 500, duration)
            raise
        finally:
            duration = time.time() - start_time
            metrics_store.dec_active()
            if status_code > 0:
                metrics_store.record(method, path, status_code, duration)
