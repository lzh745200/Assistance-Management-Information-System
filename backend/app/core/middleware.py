"""Middleware utilities.

Provides reusable FastAPI/Starlette middleware components for request
timing, CORS setup, and security header injection.
"""

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Adds an ``X-Process-Time`` header and logs slow requests.

    Uses SLOW_QUERY_THRESHOLD_MS from settings (default 200ms).
    """

    def __init__(self, app, slow_threshold_ms: float = None):
        super().__init__(app)
        if slow_threshold_ms is not None:
            self._slow_threshold = slow_threshold_ms
        else:
            try:
                from app.core.config import settings
                self._slow_threshold = getattr(settings, "SLOW_QUERY_THRESHOLD_MS", 200.0)
            except Exception:
                self._slow_threshold = 200.0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
        if elapsed_ms > self._slow_threshold:
            logger.warning(
                "慢请求 %s %s — %.0f ms",
                request.method,
                request.url.path,
                elapsed_ms,
            )
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a unique request ID (from headers or generated)."""

    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid

        request_id = request.headers.get(self.HEADER_NAME, uuid.uuid4().hex[:16])
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[self.HEADER_NAME] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %d (%.2f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response


def setup_cors(app: FastAPI, settings=None) -> None:
    """Configure CORS from application settings.

    Args:
        app: The FastAPI application.
        settings: Optional Settings instance (imported if None).
    """
    if settings is None:
        try:
            from app.core.config import settings
        except Exception:
            logger.warning("无法加载 CORS 配置，使用默认值")
            settings = None

    origins = getattr(settings, "cors_origins_list", ["*"]) if settings else ["*"]
    allow_credentials = getattr(settings, "CORS_ALLOW_CREDENTIALS", True) if settings else True
    allow_methods = (
        getattr(settings, "cors_allow_methods_list", ["*"])
        if settings
        else ["*"]
    )
    allow_headers = (
        getattr(settings, "cors_allow_headers_list", ["*"])
        if settings
        else ["*"]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )


def setup_default_middleware(app: FastAPI, settings=None) -> None:
    """Register standard middleware on a FastAPI app.

    Installs: RequestID, Timing, Logging, and CORS.
    """
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(LoggingMiddleware)
    setup_cors(app, settings)

    # Add security headers middleware
    try:
        from app.core.security import SecurityHeadersMiddleware
        app.add_middleware(SecurityHeadersMiddleware)
    except ImportError:
        pass
