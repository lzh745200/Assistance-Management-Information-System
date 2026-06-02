"""
API版本中间件

处理API版本控制
"""

import anyio

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    API版本中间件

    处理API版本相关的逻辑
    """

    def __init__(self, app: ASGIApp, default_version: str = "v1", header_name: str = "X-API-Version"):
        super().__init__(app)
        self.default_version = default_version
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        version = request.headers.get(self.header_name, self.default_version)
        request.state.api_version = version

        try:
            response = await call_next(request)
        except anyio.EndOfStream:
            return JSONResponse(status_code=499, content={"detail": "客户端关闭了连接"})

        response.headers[self.header_name] = version
        return response
