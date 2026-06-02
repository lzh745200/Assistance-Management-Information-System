"""权限系统核心 — 薄封装层。

此模块现在是 services/rbac_service.py 的 re-export 封装。
Permission 枚举和角色-权限映射的权威来源是 RBACService。

历史说明: 此文件原本维护了一套独立的 Permission 枚举和
ROLE_PERMISSIONS 映射，与 rbac_service.py 中的实现不一致。
已在 P1-4 架构优化中统一。
"""

from app.services.rbac_service import Permission, RBACService  # noqa: E402, F401


def has_permission(user, resource: str, action: str) -> bool:
    """检查用户权限 (backward-compat re-export 到 permission_utils)."""
    from app.core.permission_utils import check_permission
    return check_permission(user, resource, action)


__all__ = [
    "Permission",
    "RBACService",
    "has_permission",
]
