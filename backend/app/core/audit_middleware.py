"""Audit middleware for logging API requests with user identity."""
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs request method, path, status code, duration, and authenticated user."""

    async def dispatch(self, request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        # Extract user identity from Authorization header
        user_id = self._extract_user_id(request)

        logger.info(
            "%s %s -> %d (%dms) [user: %s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            user_id,
        )
        return response

    @staticmethod
    def _extract_user_id(request) -> str:
        """Extract user ID from JWT token in Authorization header.

        Returns user_id string or 'anonymous' if not authenticated.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return "anonymous"

        token = auth_header[7:]
        try:
            from jose import jwt
            from app.core.config import settings

            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": False},  # Don't re-verify expiry for audit log
            )
            return payload.get("sub", "unknown")
        except Exception:
            return "unauthenticated"
