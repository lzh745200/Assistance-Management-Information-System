"""全局请求体大小限制中间件。

非文件上传端点限制为 10MB，防止恶意超大 JSON 请求。
文件上传端点（multipart/form-data）由 MAX_FILE_SIZE 单独控制，此处放行。
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

UPLOAD_PATH_PREFIXES = (
    "/api/v1/import",
    "/api/v1/schools/",
    "/api/v1/policies/",
    "/api/v1/data-sync/",
)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_size: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        content_type = request.headers.get("content-type", "")

        is_multipart = "multipart/form-data" in content_type
        is_upload_path = any(request.url.path.startswith(p) for p in UPLOAD_PATH_PREFIXES)

        if not is_multipart and not is_upload_path and content_length:
            try:
                if int(content_length) > self.max_body_size:
                    logger.warning(
                        "请求体过大被拒绝: %s %s (%s bytes)",
                        request.method,
                        request.url.path,
                        content_length,
                    )
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"请求体超过大小限制 ({self.max_body_size // 1024 // 1024}MB)"},
                    )
            except (ValueError, TypeError):
                pass

        return await call_next(request)
