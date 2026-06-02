"""
数据范围过滤依赖

根据当前用户的角色和所属组织，返回可访问的组织名称列表。
用于帮扶村（support_unit / department）和学校（support_unit）的数据过滤。

规则：
- admin 角色 / data_scope=all：可访问所有数据
- org_children（默认）：本组织及下级组织
- org：仅本组织
- self：仅自己创建的数据
"""

import logging
from typing import List, Optional, Tuple

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permission_utils import is_superuser
from app.core.security import get_current_user
from app.models.organization import Organization

logger = logging.getLogger(__name__)

_ORG_TREE_MAX_DEPTH = 10  # 防止环形引用导致无限递归


class DataScope:
    """数据范围对象"""

    def __init__(
        self,
        is_admin: bool,
        org_names: Optional[List[str]] = None,
        org_ids: Optional[List[int]] = None,
        self_only: bool = False,
        user_id: Optional[int] = None,
    ):
        self.is_admin = is_admin
        self.org_names = org_names or []
        self.org_ids = org_ids or []
        self.self_only = self_only
        self.user_id = user_id

    def has_full_access(self) -> bool:
        return self.is_admin

    def filter_by_org_ids(self, query, *id_columns, created_by_column=None):
        """
        基于 organization_id 外键的精确数据范围过滤。

        优先使用此方法代替 filter_query，可彻底消除文本模糊匹配的超范围风险。

        Args:
            query: SQLAlchemy query对象
            *id_columns: 要过滤的 organization_id 字段
            created_by_column: 可选，created_by 字段，用于 self_only 模式
        """
        if self.is_admin:
            return query

        if self.self_only:
            if created_by_column is not None and self.user_id is not None:
                return query.filter(created_by_column == self.user_id)
            return query.filter(False)

        if not self.org_ids:
            return query.filter(False)

        from sqlalchemy import or_

        conditions = [col.in_(self.org_ids) for col in id_columns]
        if conditions:
            return query.filter(or_(*conditions))
        return query.filter(False)


def _get_org_subtree(
    db: Session, org_id: int, _depth: int = 0, _visited: Optional[set] = None
) -> Tuple[List[int], List[str]]:
    """
    单次遍历获取组织及所有下级的 ID 列表和名称列表。

    返回 (ids, names) 元组，避免两次独立遍历。
    """
    if _depth > _ORG_TREE_MAX_DEPTH:
        logger.warning("组织树递归超过最大深度 %d，截断于 org_id=%d", _ORG_TREE_MAX_DEPTH, org_id)
        return [], []
    if _visited is None:
        _visited = set()
    if org_id in _visited:
        logger.warning("组织树检测到环形引用，org_id=%d", org_id)
        return [], []
    _visited.add(org_id)

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return [], []

    ids = [org.id]
    names = [org.name]
    for child in db.query(Organization).filter(Organization.parent_id == org_id).all():
        child_ids, child_names = _get_org_subtree(db, child.id, _depth + 1, _visited)
        ids.extend(child_ids)
        names.extend(child_names)
    return ids, names


async def get_data_scope(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataScope:
    """
    FastAPI 依赖项：根据用户的 data_scope 字段返回 DataScope 对象。
    """
    role = getattr(current_user, "role", "user")
    user_data_scope = getattr(current_user, "data_scope", "org") or "org"

    if role in ("admin", "super_admin") or is_superuser(current_user) or user_data_scope == "all":
        return DataScope(is_admin=True)

    org_id = getattr(current_user, "organization_id", None)

    if user_data_scope == "self":
        return DataScope(
            is_admin=False,
            org_names=[],
            org_ids=[],
            self_only=True,
            user_id=getattr(current_user, "id", None),
        )

    if user_data_scope == "org":
        if not org_id:
            dept = getattr(current_user, "department", None)
            if dept:
                return DataScope(is_admin=False, org_names=[dept], org_ids=[])
            # 未分配组织的用户：单机版中可访问全部数据
            return DataScope(is_admin=True)
        org = db.query(Organization).filter(Organization.id == org_id).first()
        org_names = [org.name] if org else []
        return DataScope(is_admin=False, org_names=org_names, org_ids=[org_id])

    # org_children（默认）：本组织及下级
    if not org_id:
        dept = getattr(current_user, "department", None)
        if dept:
            return DataScope(is_admin=False, org_names=[dept])
        # 未分配组织的用户：单机版中可访问全部数据
        return DataScope(is_admin=True)

    org_ids, org_names = _get_org_subtree(db, org_id)
    if not org_names:
        dept = getattr(current_user, "department", None)
        if dept:
            return DataScope(is_admin=False, org_names=[dept], org_ids=org_ids)
        # 组织存在但名称为空：访问全部数据
        return DataScope(is_admin=True)

    return DataScope(is_admin=False, org_names=org_names, org_ids=org_ids)
