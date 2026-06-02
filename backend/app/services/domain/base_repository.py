"""
DDD 仓储基类 — 统一数据访问模式

为所有聚合根提供标准 CRUD 操作，确保数据访问通过仓储接口而非直接 ORM 查询。
这是 DDD 架构深化的第一步（方案 #19）。
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """统一仓储基类。

    所有领域仓储必须继承此类，确保数据访问的统一性和可测试性。

    Usage::

        class VillageRepository(BaseRepository[VillageAggregate]):
            def __init__(self, db: Session):
                super().__init__(db, VillageORM)

        repo = VillageRepository(db)
        village = repo.get_by_id(1)
    """

    def __init__(self, db: Session, entity_class: Type[T]):
        self._db = db
        self._entity = entity_class
        # Discover the primary key column(s) for dynamic ID queries
        from sqlalchemy import inspect
        self._pk_columns = inspect(entity_class).primary_key

    # ── 内部 helpers ──

    def _apply_filters(self, query, **filters: Any):
        """Apply dynamic equality filters, skipping None values and missing columns."""
        for key, value in filters.items():
            if value is not None and hasattr(self._entity, key):
                query = query.filter(getattr(self._entity, key) == value)
        return query

    def _apply_order_by(self, query, order_by: Optional[str]):
        """Apply ordering.  Prefix with '-' for descending."""
        if not order_by:
            return query
        desc = order_by.startswith("-")
        col_name = order_by[1:] if desc else order_by
        if hasattr(self._entity, col_name):
            col = getattr(self._entity, col_name)
            return query.order_by(col.desc() if desc else col.asc())
        return query

    # ── 查询方法 ──

    def get_by_id(self, entity_id: int) -> Optional[T]:
        """根据主键获取实体（支持复合主键）"""
        if len(self._pk_columns) == 1:
            pk_col = self._pk_columns[0]
            return self._db.query(self._entity).filter(pk_col == entity_id).first()
        # Composite PK: build filter from dict
        if isinstance(entity_id, dict):
            filters = [col == entity_id.get(col.key) for col in self._pk_columns]
            return self._db.query(self._entity).filter(*filters).first()
        return None

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        **filters: Any,
    ) -> List[T]:
        """分页列表查询，支持动态过滤。

        Args:
            skip: 偏移量
            limit: 每页数量（最大 500）
            order_by: 排序字段名（如 "created_at" 或 "-created_at" 降序）
            **filters: 字段名=值的过滤条件
        """
        limit = min(limit, 500)
        query = self._db.query(self._entity)
        query = self._apply_filters(query, **filters)
        query = self._apply_order_by(query, order_by)
        return query.offset(skip).limit(limit).all()

    def count(self, **filters: Any) -> int:
        """计数查询"""
        query = self._apply_filters(self._db.query(self._entity), **filters)
        return query.count()

    def exists(self, **filters: Any) -> bool:
        """检查是否存在符合条件的记录（使用 EXISTS 而非 COUNT）"""
        query = self._apply_filters(self._db.query(self._entity), **filters)
        return self._db.query(query.exists()).scalar()

    # ── 写入方法 ──

    def add(self, entity: T) -> T:
        """新增实体（需调用方 commit）"""
        self._db.add(entity)
        return entity

    def add_all(self, entities: List[T]) -> List[T]:
        """批量新增"""
        self._db.add_all(entities)
        return entities

    def remove(self, entity: T) -> None:
        """删除实体（需调用方 commit）"""
        self._db.delete(entity)

    def remove_by_id(self, entity_id: int) -> bool:
        """根据 ID 删除实体，返回是否成功"""
        entity = self.get_by_id(entity_id)
        if entity:
            self._db.delete(entity)
            return True
        return False

    # ── 批量操作 ──

    def bulk_insert(self, mappings: List[Dict[str, Any]]) -> None:
        """高效批量插入（绕过 ORM，直接 INSERT）"""
        self._db.bulk_insert_mappings(self._entity, mappings)

    def bulk_update(self, mappings: List[Dict[str, Any]]) -> None:
        """高效批量更新"""
        self._db.bulk_update_mappings(self._entity, mappings)

    # ── 工具 ──

    @property
    def db(self) -> Session:
        """暴露数据库会话（供子类扩展）"""
        return self._db
