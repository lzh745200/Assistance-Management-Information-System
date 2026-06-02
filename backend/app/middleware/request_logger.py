"""
请求日志中间件（ASGI 原生实现）

记录每个 HTTP 请求的详细信息：
- 请求方法、路径、查询参数
- 客户端 IP
- User-Agent
- 响应状态码
- 请求耗时

跳过静态资源和健康检查路径。
"""

import logging
import time

logger = logging.getLogger("app.request")

# 不记录日志的路径前缀
_SKIP_PREFIXES = (
    "/health",
    "/metrics",
    "/favicon.ico",
    "/static/",
)


def _get_client_ip(scope: dict) -> str:
    """从 ASGI scope 中提取客户端 IP"""
    # 优先从 headers 获取代理后的真实 IP
    headers = dict(scope.get("headers", []))
    forwarded = headers.get(b"x-forwarded-for")
    if forwarded:
        return forwarded.decode("utf-8", errors="replace").split(",")[0].strip()
    real_ip = headers.get(b"x-real-ip")
    if real_ip:
        return real_ip.decode("utf-8", errors="replace").strip()
    # 回退到 socket 地址
    client = scope.get("client")
    if client:
        return client[0]
    return "unknown"


def _get_user_agent(scope: dict) -> str:
    """从 ASGI headers 中提取 User-Agent"""
    headers = dict(scope.get("headers", []))
    ua = headers.get(b"user-agent", b"")
    return ua.decode("utf-8", errors="replace")[:200]


class RequestLoggerMiddleware:
    """
    ASGI 请求日志中间件

    用法: app.add_middleware(RequestLoggerMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # 跳过不需要记录的路径
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "?")
        query_string = scope.get("query_string", b"").decode("utf-8", errors="replace")
        client_ip = _get_client_ip(scope)
        user_agent = _get_user_agent(scope)
        start_time = time.time()
        status_code = 0

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                "%s %s - ERROR (%.3fs) ip=%s ua=%s error=%s",
                method,
                path,
                duration,
                client_ip,
                user_agent,
                exc,
            )
            raise
        finally:
            duration = time.time() - start_time
            if status_code > 0:
                logger.info(
                    "%s %s%s - %d (%.3fs) ip=%s ua=%s",
                    method,
                    path,
                    f"?{query_string}" if query_string else "",
                    status_code,
                    duration,
                    client_ip,
                    user_agent,
                )
