"""
村庄服务层 - 数据权限过滤（委托实现）

本模块委托 core.data_permission.filter_by_data_scope 实现，
避免重复维护权限逻辑。
"""

from typing import Optional

from sqlalchemy.orm import Query, Session

from app.core.data_permission import filter_by_data_scope


def filter_villages_by_permission(
    query: Query,
    user,
    village_model,
    db: Optional[Session] = None,
) -> Query:
    """
    根据用户权限过滤村庄查询。

    委托给 core.data_permission.filter_by_data_scope 实现。

    Args:
        query: SQLAlchemy Query 对象
        user: 当前用户
        village_model: Village 模型类
        db: 数据库会话（用于查询子组织）

    Returns:
        过滤后的 Query 对象
    """
    return filter_by_data_scope(query, village_model, user, db=db)
