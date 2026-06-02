"""Repository 基类。封装通用 CRUD 操作。"""
from typing import Any, Dict, Optional, Type
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """泛型 Repository 基类。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, model: Type, id: int) -> Optional[Any]:
        result = await self.db.execute(select(model).where(model.id == id))
        return result.scalar_one_or_none()

    async def list(self, model: Type, *, filters: Optional[Dict[str, Any]] = None,
                   order_by: Optional[Any] = None, page: int = 1,
                   page_size: int = 20) -> Dict[str, Any]:
        query = select(model)
        count_query = select(func.count()).select_from(model)
        if filters:
            for col, val in filters.items():
                if val is not None and hasattr(model, col):
                    clause = getattr(model, col) == val
                    query = query.where(clause)
                    count_query = count_query.where(clause)
        if order_by is not None:
            query = query.order_by(order_by)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        return {"items": list(items), "total": total, "page": page, "page_size": page_size}

    async def create(self, model: Type, **kwargs) -> Any:
        instance = model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance, **kwargs) -> Any:
        for key, value in kwargs.items():
            if hasattr(instance, key) and value is not None:
                setattr(instance, key, value)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance, *, soft: bool = True) -> None:
        if soft and hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            await self.db.commit()
        else:
            await self.db.delete(instance)
            await self.db.commit()
