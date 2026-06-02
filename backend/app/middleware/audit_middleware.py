"""
审计中间件

记录请求审计日志
"""

from typing import Optional

import anyio
import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.middleware.utils import should_skip_middleware

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    审计中间件

    记录所有请求的审计信息
    """

    def __init__(self, app: ASGIApp, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = frozenset(
            exclude_paths
            or [
                "/health",
                "/metrics",
            ]
        )

    async def dispatch(self, request: Request, call_next):
        """处理请求并记录审计日志"""
        start_time = time.time()

        try:
            path = request.url.path
            if should_skip_middleware(path, self.exclude_paths):
                return await call_next(request)

            response = await call_next(request)

            duration = time.time() - start_time
            logger.info(f"Audit: {request.method} {path} - {response.status_code} - {duration:.3f}s")

            return response
        except anyio.EndOfStream:
            duration = time.time() - start_time
            logger.info(f"Audit: {request.method} {request.url.path} - 499 - {duration:.3f}s")
            return JSONResponse(
                status_code=499,
                content={"detail": "客户端关闭了连接"},
            )
