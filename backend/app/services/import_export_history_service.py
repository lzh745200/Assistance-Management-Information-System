"""导入导出历史服务。"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.import_export_history import ImportExportHistory


class ImportExportHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_history(self, *, page: int = 1, page_size: int = 20,
                           user_id: Optional[int] = None) -> dict:
        query = select(ImportExportHistory).order_by(desc(ImportExportHistory.created_at))
        count_q = select(func.count(ImportExportHistory.id))
        if user_id:
            query = query.where(ImportExportHistory.user_id == user_id)
            count_q = count_q.where(ImportExportHistory.user_id == user_id)
        total = (await self.db.execute(count_q)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return {"items": result.scalars().all(), "total": total, "page": page, "page_size": page_size}

    async def record(self, **kwargs) -> ImportExportHistory:
        record = ImportExportHistory(**kwargs)
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record
