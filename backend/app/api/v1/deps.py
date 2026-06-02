"""API dependencies."""

from __future__ import annotations

from fastapi import HTTPException

from app.core.database import get_db  # noqa: F401 — 统一从 database.py re-export
from app.core.security import get_current_user  # noqa: F401 — 真实 JWT 认证实现
from app.core.permission_utils import is_superuser

# 别名,兼容新代码
get_current_active_user = get_current_user

# 管理角色列表（可执行创建/编辑/删除操作）
ADMIN_ROLES = ("admin", "super_admin", "manager")


def require_manager_role(current_user) -> None:
    """要求管理角色，否则返回 403。在 funds / fund_lifecycle 等模块共用。"""
    role = getattr(current_user, "role", "")
    if role not in ADMIN_ROLES and not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="权限不足，仅管理员或管理角色可执行此操作")
