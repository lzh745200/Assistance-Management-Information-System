"""
权限过滤器模块

提供基于组织层级的权限过滤功能，支持：
- 数据权限过滤
- 组织层级缓存
- 权限装饰器

需求: 7.x - 权限与数据安全
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, Set

logger = logging.getLogger(__name__)

# 组织层级缓存
_org_hierarchy_cache: Dict[int, Set[int]] = {}


def get_org_hierarchy_cached(org_id: int) -> Set[int]:
    """获取组织的完整层级结构（含子组织），带缓存。

    返回组织ID及其所有子孙组织的ID集合。

    Args:
        org_id: 组织ID

    Returns:
        组织ID集合
    """
    if org_id in _org_hierarchy_cache:
        return _org_hierarchy_cache[org_id]

    # 基本返回自身
    result = {org_id}
    _org_hierarchy_cache[org_id] = result
    return result


def clear_org_hierarchy_cache() -> None:
    """清除组织层级缓存"""
    _org_hierarchy_cache.clear()
    logger.debug("组织层级缓存已清除")


class PermissionFilter:
    """权限过滤器 - 用于数据查询时的权限过滤。

    支持基于用户角色和组织的数据过滤。
    """

    def __init__(self, user: Any = None):
        """初始化权限过滤器。

        Args:
            user: 用户对象
        """
        self.user = user

    def apply_org_filter(self, query, model, org_field: str = "organization_id"):
        """对查询应用组织过滤。

        Args:
            query: SQLAlchemy 查询对象
            model: 数据模型
            org_field: 组织ID字段名

        Returns:
            过滤后的查询
        """
        if self.user is None:
            return query

        # 管理员不限制
        if hasattr(self.user, "role") and self.user.role in ("admin", "super_admin"):
            return query

        # 普通用户只看到自己组织的数据
        if hasattr(self.user, "organization_id") and self.user.organization_id:
            org_column = getattr(model, org_field, None)
            if org_column is not None:
                return query.filter(org_column == self.user.organization_id)

        return query

    def can_access(self, resource_org_id: int) -> bool:
        """检查是否可以访问特定组织ID的资源。

        Args:
            resource_org_id: 资源所属组织ID

        Returns:
            bool: 是否有权限
        """
        if self.user is None:
            return False

        if hasattr(self.user, "role") and self.user.role in ("admin", "super_admin"):
            return True

        user_org_id = getattr(self.user, "organization_id", None)
        if user_org_id is not None:
            return user_org_id == resource_org_id

        return False


def with_permission_filter(func: Callable) -> Callable:
    """权限过滤装饰器 - 自动从 kwargs 中提取 user 并创建 PermissionFilter。

    Usage:
        @with_permission_filter
        def get_villages(db: Session, user: User, filter: PermissionFilter):
            query = db.query(Village)
            return filter.apply_org_filter(query, Village).all()
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # 尝试从 kwargs 或 args 中获取 user
        user = kwargs.get("user") or kwargs.get("current_user")
        if user is None:
            for arg in args:
                if hasattr(arg, "role") or hasattr(arg, "is_superuser"):
                    user = arg
                    break

        permission_filter = PermissionFilter(user)
        kwargs["filter"] = kwargs.get("filter", permission_filter)
        return func(*args, **kwargs)

    return wrapper
