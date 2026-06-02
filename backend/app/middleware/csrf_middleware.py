"""
CSRF 保护中间件

实现 Double Submit Cookie 模式：
1. 前端先调用 GET /api/v1/auth/csrf-token 获取 token
2. 服务器在响应中设置 csrftoken Cookie（httponly=False，JS 可读）
3. 前端在状态变更请求的 X-CSRF-Token 请求头中携带 token
4. 服务器比对 Cookie 中的 token 与 Header 中的 token，一致则放行

军用安全基线要求：即使单机部署也应启用 CSRF 保护，防止同源跨站请求攻击。
"""

import hashlib
import hmac
import logging
import os
from typing import List, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# CSRF Cookie 名称
CSRF_COOKIE_NAME = "csrftoken"

# CSRF Token 有效期（秒），默认 24 小时
CSRF_TOKEN_EXPIRY = 86400

# CSRF 请求头名称
CSRF_HEADER_NAME = "X-CSRF-Token"

# 安全请求方法（无需 CSRF 验证）
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# CSRF 豁免路径前缀（无需 CSRF 验证）
_CSRF_EXEMPT_PATH_PREFIXES: List[str] = [
    "/api/v1/auth/csrf-token",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/shutdown",
    "/health",
    "/api/v1/health",
    "/docs",
    "/openapi.json",
    "/redoc",
]


def generate_csrf_token() -> str:
    """生成 CSRF token（64 字符十六进制随机字符串）"""
    return os.urandom(32).hex()


def sign_csrf_token(token: str, secret_key: Optional[str] = None) -> str:
    """对 CSRF token 进行 HMAC-SHA256 签名

    使用 CSRF_SECRET_KEY 对原始 token 签名，防止 token 篡改。
    前端可将签名版本存储在 Authorization 头之外的地方用于双重验证。

    Args:
        token: 原始 CSRF token
        secret_key: 签名密钥，默认从 settings 读取

    Returns:
        HMAC-SHA256 十六进制签名
    """
    if secret_key is None:
        from app.core.config import settings

        secret_key = settings.CSRF_SECRET_KEY or settings.SECRET_KEY

    if isinstance(secret_key, str):
        secret_key = secret_key.encode("utf-8")
    if isinstance(token, str):
        token = token.encode("utf-8")

    return hmac.new(secret_key, token, hashlib.sha256).hexdigest()


def _is_path_exempt(path: str) -> bool:
    """检查请求路径是否在 CSRF 豁免列表中"""
    for prefix in _CSRF_EXEMPT_PATH_PREFIXES:
        if path == prefix or path.startswith(prefix.rstrip("/") + "/") or path.startswith(prefix):
            return True
    return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF 保护中间件

    配置:
    - CSRF_ENABLED: 全局开关（settings.CSRF_ENABLED）
    - CSRF_SECRET_KEY: Token 签名密钥（settings.CSRF_SECRET_KEY）

    验证逻辑:
    1. GET/HEAD/OPTIONS 请求直接放行
    2. 豁免路径直接放行
    3. POST/PUT/DELETE/PATCH 请求需要携带有效的 X-CSRF-Token 头
    4. Token 与 Cookie 中的 csrftoken 值比对，一致则放行
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # 延迟导入避免循环依赖
        from app.core.config import settings

        # CSRF 未启用时直接放行
        if not getattr(settings, "CSRF_ENABLED", False):
            return await call_next(request)

        # 安全方法直接放行
        if request.method.upper() in _SAFE_METHODS:
            return await call_next(request)

        # 豁免路径直接放行
        if _is_path_exempt(request.url.path):
            return await call_next(request)

        # ── 状态变更请求（POST/PUT/DELETE/PATCH）验证 CSRF token ──
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME, "")
        csrf_header = request.headers.get(CSRF_HEADER_NAME, "")

        if not csrf_cookie or not csrf_header:
            logger.warning(
                "CSRF 验证失败：缺少 token | method=%s path=%s cookie=%s header=%s",
                request.method,
                request.url.path,
                "present" if csrf_cookie else "missing",
                "present" if csrf_header else "missing",
            )
            return JSONResponse(
                status_code=403,
                content={
                    "code": 403,
                    "message": "CSRF 验证失败：请先调用 GET /api/v1/auth/csrf-token 获取 token",
                    "data": None,
                },
            )

        if not hmac.compare_digest(csrf_cookie, csrf_header):
            logger.warning(
                "CSRF 验证失败：token 不匹配 | method=%s path=%s",
                request.method,
                request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={
                    "code": 403,
                    "message": "CSRF token 无效或已过期，请重新获取",
                    "data": None,
                },
            )

        return await call_next(request)
