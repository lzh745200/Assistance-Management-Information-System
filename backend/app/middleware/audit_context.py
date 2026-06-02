"""
审计上下文

管理审计相关的上下文信息
"""

from contextvars import ContextVar
from typing import Optional

# 上下文变量
_current_user_id: ContextVar[Optional[int]] = ContextVar("current_user_id", default=None)
_current_request_id: ContextVar[Optional[str]] = ContextVar("current_request_id", default=None)


class AuditContext:
    """
    审计上下文

    存储当前请求的审计相关信息
    """

    def __init__(self, user_id: Optional[int] = None, request_id: Optional[str] = None):
        self.user_id = user_id
        self.request_id = request_id

    @classmethod
    def get_current(cls) -> "AuditContext":
        """获取当前审计上下文"""
        return cls(
            user_id=_current_user_id.get(),
            request_id=_current_request_id.get(),
        )

    def set_current(self):
        """设置为当前上下文"""
        _current_user_id.set(self.user_id)
        _current_request_id.set(self.request_id)


def get_current_user() -> Optional[int]:
    """获取当前用户ID"""
    return _current_user_id.get()


def get_request_id() -> Optional[str]:
    """获取当前请求ID"""
    return _current_request_id.get()


def set_current_user(user_id: Optional[int]):
    """设置当前用户ID"""
    _current_user_id.set(user_id)


def set_request_id(request_id: Optional[str]):
    """设置当前请求ID"""
    _current_request_id.set(request_id)
