"""Data permission utilities.

Provides helpers for scoping database queries based on the current user's
permission level and data visibility rules.
"""

import logging
from enum import Enum
from typing import Any

from fastapi import HTTPException

from app.core.permission_utils import is_admin

logger = logging.getLogger(__name__)


class DataScope(str, Enum):
    """Data visibility scopes."""

    ALL = "all"
    """See all records – super admin."""

    OWN_DEPT = "own_dept"
    """See records belonging to the user's own department."""

    OWN = "own"
    """See only the user's own records."""


def get_data_scope(user: Any) -> DataScope:
    """Determine the data scope for a given user.

    Args:
        user: A user model instance (must have ``role`` and optionally
            ``is_superuser`` attributes).

    Returns:
        The appropriate :class:`DataScope` value.
    """
    if user is None:
        return DataScope.OWN

    is_superuser = getattr(user, "is_superuser", False)
    role = getattr(user, "role", "")

    if is_superuser or role == "super_admin":
        return DataScope.ALL

    if role in ("admin", "manager", "approval_leader"):
        return DataScope.OWN_DEPT

    return DataScope.OWN


def apply_scope_to_query(
    query: Any,
    model: Any,
    user: Any,
    *,
    owner_field: str = "created_by",
    dept_field: str = "department_id",
) -> Any:
    """Add filters to a SQLAlchemy query based on the user's data scope.

    Args:
        query: An existing SQLAlchemy :class:`Query` object.
        model: The ORM model class.
        user: The current user instance.
        owner_field: Name of the column holding the owner's user ID.
        dept_field: Name of the column holding the department ID.

    Returns:
        The filtered query.
    """
    scope = get_data_scope(user)

    if scope == DataScope.ALL:
        return query

    if scope == DataScope.OWN_DEPT:
        user_dept = getattr(user, "department_id", None)
        if user_dept is not None:
            return query.filter(getattr(model, dept_field) == user_dept)
        # Fall through to OWN if department is not set
        logger.debug("User has no department; falling back to OWN scope")

    if scope == DataScope.OWN:
        return query.filter(getattr(model, owner_field) == getattr(user, "id", None))

    return query


def check_record_access(
    record: Any,
    user: Any,
    *,
    owner_field: str = "created_by",
    dept_field: str = "department_id",
) -> bool:
    """Check whether *user* is allowed to access a single *record*.

    Args:
        record: An ORM model instance.
        user: The current user.
        owner_field: Column name identifying the record owner.
        dept_field: Column name identifying the department.

    Returns:
        *True* if access is permitted.
    """
    scope = get_data_scope(user)
    if scope == DataScope.ALL:
        return True
    if scope == DataScope.OWN_DEPT:
        return getattr(record, dept_field, None) == getattr(user, "department_id", None)
    if scope == DataScope.OWN:
        return getattr(record, owner_field, None) == getattr(user, "id", None)
    return False


def filter_by_data_scope(query, model, user, db=None, org_field="organization_id"):
    """按数据权限过滤查询。委托给 apply_scope_to_query 实现完整过滤。"""
    if is_admin(user):
        return query
    return apply_scope_to_query(query, model, user, owner_field="created_by", dept_field=org_field)


def require_data_permission(current_user, organization_id=None, created_by=None, db=None, error_message="无权执行此操作"):
    """检查数据权限。管理员自动通过；非管理员需通过 record-ownership 检查。"""
    if is_admin(current_user):
        return True
    if not db:
        logger.warning("require_data_permission called without db session — denying access")
        raise HTTPException(status_code=403, detail=error_message)
    if created_by is not None and created_by == getattr(current_user, "id", None):
        return True
    raise HTTPException(status_code=403, detail=error_message)
