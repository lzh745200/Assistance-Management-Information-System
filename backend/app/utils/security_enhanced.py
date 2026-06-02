"""
安全增强工具兼容模块

向后兼容 re-export，委托到：
- app.core.security（密码策略、输入清理、速率限制检查、IP提取）
- app.services.resource_limiter（速率限制类/实例）
"""

from app.core.security import (
    check_rate_limit,
    generate_password,
    get_client_ip,
    PasswordPolicy,
    sanitize_input,
)
from app.services.resource_limiter import _rate_limiter


# ── 兼容 RateLimiter（委托到 resource_limiter 全局单例）──

class RateLimiter:
    """速率限制器兼容包装 — 委托到 resource_limiter.ResourceLimiter 全局单例"""

    def __init__(self, max_requests: int = 60, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window

    def is_allowed(self, client_id: str) -> bool:
        return _rate_limiter.is_allowed(client_id)

    @staticmethod
    def get_client_id(request) -> str:
        return get_client_ip(request)


rate_limiter = RateLimiter()


# ── 兼容 PasswordValidator ──

class PasswordValidator:
    @staticmethod
    def validate_password_strength(password: str) -> tuple:
        return PasswordPolicy.validate(password)

    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        return generate_password(length)


# ── 兼容 InputSanitizer ──

class InputSanitizer:
    @staticmethod
    def sanitize_input(value: str) -> str:
        return sanitize_input(value)


# ── 兼容 SecurityHeaders ──

class SecurityHeaders:
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    @staticmethod
    def get_security_headers() -> dict:
        return dict(SecurityHeaders.SECURITY_HEADERS)


__all__ = [
    "RateLimiter",
    "rate_limiter",
    "PasswordValidator",
    "InputSanitizer",
    "SecurityHeaders",
    "check_rate_limit",
]
