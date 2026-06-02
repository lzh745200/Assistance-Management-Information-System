"""权限工具模块

提供用户权限检查、管理员验证和组织关系查询。
"""

import logging
from functools import wraps
from typing import Optional

from fastapi import HTTPException, status

from app.core.constants import ADMIN_ROLES

logger = logging.getLogger(__name__)


def is_superuser(user) -> bool:
    """检查用户是否为超级管理员

    Args:
        user: 用户对象

    Returns:
        bool: 是否为超级管理员
    """
    if user is None:
        return False

    # 检查 is_superuser 属性（仅当为 True 时直接返回）
    if hasattr(user, "is_superuser") and user.is_superuser:
        return True

    # 检查 role 属性
    if hasattr(user, "role"):
        return user.role == "super_admin"

    return False


def is_admin(user) -> bool:
    """检查用户是否为管理员（包括超级管理员）

    Args:
        user: 用户对象

    Returns:
        bool: 是否为管理员
    """
    if user is None:
        return False

    if is_superuser(user):
        return True

    if hasattr(user, "role"):
        return user.role in ADMIN_ROLES

    return False


def require_admin(func):
    """管理员权限验证装饰器

    用法:
        @require_admin
        def admin_only_endpoint(current_user=Depends(get_current_user)):
            pass
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 从 kwargs 中查找 current_user
        current_user = kwargs.get("current_user")
        if current_user is None:
            # 尝试从 args 中查找（如果是位置参数）
            for arg in args:
                if hasattr(arg, "role") or hasattr(arg, "is_superuser"):
                    current_user = arg
                    break

        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供用户认证信息",
            )

        if not is_admin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限",
            )

        return await func(*args, **kwargs)

    return wrapper


def get_user_org_id(user) -> Optional[int]:
    """获取用户的组织ID

    Args:
        user: 用户对象

    Returns:
        Optional[int]: 组织ID，如果不存在则返回 None
    """
    if user is None:
        return None

    if hasattr(user, "organization_id") and user.organization_id is not None:
        return user.organization_id

    if hasattr(user, "org_id") and user.org_id is not None:
        return user.org_id

    return None


def get_org_with_fallback(user):
    """获取用户的组织对象，支持多种回退策略

    优先级:
    1. user.organization 直接关系
    2. 通过 organization_id 查询
    3. 返回 None

    Args:
        user: 用户对象

    Returns:
        组织对象或 None
    """
    if user is None:
        return None

    # 直接关系
    if hasattr(user, "organization") and user.organization is not None:
        return user.organization

    # 通过 ID 查询（需要数据库会话，这里不直接查询，由调用方处理）
    if hasattr(user, "organization_id") and user.organization_id is not None:
        # 返回 ID，让调用方查询
        logger.debug("User has organization_id=%s but no direct relationship", user.organization_id)
        return None

    return None


def require_organization(func=None, *, org_param: str = "organization_id"):
    """组织访问控制装饰器

    确保用户只能访问自己所属组织的数据。

    Args:
        func: 被装饰的函数
        org_param: 组织ID参数名

    Usage:
        @require_organization
        def endpoint(organization_id: int, current_user=Depends(get_current_user)):
            ...
    """
    if func is None:
        # 支持带参数和不带参数的两种用法
        def decorator(f):
            return require_organization(f, org_param=org_param)
        return decorator

    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")
        if current_user is None:
            for arg in args:
                if hasattr(arg, "role") or hasattr(arg, "is_superuser"):
                    current_user = arg
                    break

        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供用户认证信息",
            )

        # 管理员跳过组织检查
        if is_admin(current_user):
            return await func(*args, **kwargs)

        user_org_id = get_user_org_id(current_user)
        requested_org_id = kwargs.get(org_param)

        if requested_org_id is not None and user_org_id is not None:
            if requested_org_id != user_org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问其他组织的数据",
                )

        return await func(*args, **kwargs)

    return wrapper


def check_org_access(user, target_org_id: int) -> bool:
    """检查用户是否有权访问目标组织的数据。

    Args:
        user: 用户对象
        target_org_id: 目标组织ID

    Returns:
        bool: 是否有访问权限
    """
    if user is None:
        return False

    if is_admin(user):
        return True

    user_org_id = get_user_org_id(user)
    return user_org_id is not None and user_org_id == target_org_id


def require_permission(permission: str):
    """权限检查装饰器

    Args:
        permission: 所需权限标识，如 "villages:write"

    Usage:
        @require_permission("villages:write")
        def create_village(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if current_user is None:
                for arg in args:
                    if hasattr(arg, "role") or hasattr(arg, "is_superuser"):
                        current_user = arg
                        break

            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供用户认证信息",
                )

            if not check_permission(current_user, permission, ""):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限: {permission}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def check_permission(user, resource: str, action: str) -> bool:
    """检查用户对特定资源的特定操作权限

    Args:
        user: 用户对象
        resource: 资源名称（如 "villages", "projects"）
        action: 操作类型（如 "read", "write", "delete"）

    Returns:
        bool: 是否有权限
    """
    if user is None:
        return False

    # 管理员拥有所有权限
    if is_admin(user):
        return True

    # 检查用户的 permissions 字段（JSON 格式或逗号分隔字符串）
    if hasattr(user, "permissions"):
        perms = user.permissions
        if not perms:
            return False

        # 如果是字符串，解析为列表
        if isinstance(perms, str):
            # 尝试 JSON 解析
            try:
                import json
                perm_list = json.loads(perms)
            except (json.JSONDecodeError, ValueError):
                # 逗号分隔格式
                perm_list = [p.strip() for p in perms.split(",")]
        else:
            perm_list = list(perms)

        # 检查权限格式：resource:action 或 *:* (全部权限)
        required = f"{resource}:{action}"
        wildcard_all = "*:*"
        wildcard_resource = f"*:{action}"
        wildcard_action = f"{resource}:*"

        return any(
            p in (required, wildcard_all, wildcard_resource, wildcard_action)
            for p in perm_list
        )

    return False
