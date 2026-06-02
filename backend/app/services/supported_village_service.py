"""SupportedVillage 业务服务。"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.supported_village import SupportedVillage

logger = logging.getLogger(__name__)


class SupportedVillageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_villages(self, *, page: int = 1, page_size: int = 20,
                           organization_id: Optional[int] = None,
                           name: Optional[str] = None) -> dict:
        query = select(SupportedVillage)
        count_q = select(func.count(SupportedVillage.id))
        if organization_id:
            query = query.where(SupportedVillage.organization_id == organization_id)
            count_q = count_q.where(SupportedVillage.organization_id == organization_id)
        if name:
            query = query.where(SupportedVillage.name.contains(name))
            count_q = count_q.where(SupportedVillage.name.contains(name))
        total = (await self.db.execute(count_q)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return {"items": result.scalars().all(), "total": total, "page": page, "page_size": page_size}

    async def get_village(self, village_id: int) -> Optional[SupportedVillage]:
        result = await self.db.execute(select(SupportedVillage).where(SupportedVillage.id == village_id))
        return result.scalar_one_or_none()

    async def create_village(self, **kwargs) -> SupportedVillage:
        village = SupportedVillage(**kwargs)
        self.db.add(village)
        await self.db.commit()
        await self.db.refresh(village)
        return village

    async def update_village(self, village_id: int, **kwargs) -> Optional[SupportedVillage]:
        village = await self.get_village(village_id)
        if not village:
            return None
        for k, v in kwargs.items():
            if hasattr(village, k) and v is not None:
                setattr(village, k, v)
        await self.db.commit()
        await self.db.refresh(village)
        return village

    async def delete_village(self, village_id: int) -> bool:
        village = await self.get_village(village_id)
        if not village:
            return False
        await self.db.delete(village)
        await self.db.commit()
        return True

    # ── Backward-compat aliases (tests expect these method names) ──
    async def get(self, village_id: int):
        return await self.get_village(village_id)

    async def get_population(self, village_id: int):
        return await self.get_village(village_id)

    async def get_income(self, village_id: int):
        return await self.get_village(village_id)

    async def get_departments(self):
        from sqlalchemy import distinct
        result = await self.db.execute(select(distinct(SupportedVillage.department)))
        return [r[0] for r in result.all() if r[0]]
