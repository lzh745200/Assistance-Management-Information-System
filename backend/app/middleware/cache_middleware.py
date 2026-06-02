"""
缓存中间件

提供请求响应缓存功能
"""

from typing import Optional

import anyio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.middleware.utils import should_skip_middleware


class CacheMiddleware(BaseHTTPMiddleware):
    """
    缓存中间件

    缓存GET请求的响应
    """

    def __init__(self, app: ASGIApp, ttl: int = 300, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.ttl = ttl
        self.exclude_paths = frozenset(
            exclude_paths
            or [
                "/health",
                "/auth",
            ]
        )
        self._cache = {}

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        try:
            if request.method != "GET":
                return await call_next(request)

            path = request.url.path
            if should_skip_middleware(path, self.exclude_paths):
                return await call_next(request)

            return await call_next(request)
        except anyio.EndOfStream:
            return JSONResponse(
                status_code=499,
                content={"detail": "客户端关闭了连接"},
            )
