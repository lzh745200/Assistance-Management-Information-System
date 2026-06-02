"""
RBAC中间件

基于角色的访问控制中间件
"""

from typing import Optional

import anyio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.middleware.utils import should_skip_middleware


class RBACMiddleware(BaseHTTPMiddleware):
    """
    RBAC中间件

    基于角色的访问控制
    """

    def __init__(self, app: ASGIApp, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = frozenset(
            exclude_paths
            or [
                "/docs",
                "/openapi.json",
                "/health",
            ]
        )

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        try:
            path = request.url.path
            if should_skip_middleware(path, self.exclude_paths):
                return await call_next(request)

            return await call_next(request)
        except anyio.EndOfStream:
            return JSONResponse(
                status_code=499,
                content={"detail": "客户端关闭了连接"},
            )
