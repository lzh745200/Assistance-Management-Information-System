"""全局请求体大小限制中间件。

非文件上传端点限制为 10MB，防止恶意超大 JSON 请求。
文件上传端点（multipart/form-data）由 MAX_FILE_SIZE 单独控制，此处放行。

策略：
1. multipart/form-data 请求一律放行（由 MAX_FILE_SIZE 端点级控制）
2. 以下业务路径可能接收大 JSON 批量数据，也一并放行
3. 其余非 multipart 请求超过 10MB 返回 413
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# 可能接收大体积 JSON / 批量数据的路径前缀
# 这些端点要么直接处理文件上传，要么处理大批量 JSON 导入/批量操作
LARGE_PAYLOAD_PATH_PREFIXES = (
    # 文件上传 / 导入导出
    "/api/v1/import",
    "/api/v1/import-export",
    "/api/v1/data-sync",
    "/api/v1/data/packages",
    # 业务模块（含文件上传或批量操作端点）
    "/api/v1/schools",
    "/api/v1/policies",
    "/api/v1/projects",
    "/api/v1/funds",
    "/api/v1/supported-villages",
    "/api/v1/rural-works",
    "/api/v1/rural-tasks",
    "/api/v1/report-templates",
    "/api/v1/permission-packages",
    # 系统管理（备份恢复、配置包导入）
    "/api/v1/system/backup",
    "/api/v1/system/config-package",
    # 批量操作
    "/api/v1/batch",
    # 用户（头像上传）
    "/api/v1/users",
)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_size: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        content_type = request.headers.get("content-type", "")

        is_multipart = "multipart/form-data" in content_type
        is_large_payload_path = any(
            request.url.path.startswith(p) for p in LARGE_PAYLOAD_PATH_PREFIXES
        )

        if not is_multipart and not is_large_payload_path and content_length:
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
