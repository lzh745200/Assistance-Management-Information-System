"""乡村工作服务"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.models.rural_work import RuralWork

logger = logging.getLogger(__name__)


def _iso(val: Any) -> Optional[str]:
    """安全地将日期/时间值转换为 ISO 字符串"""
    return val.isoformat() if val else None


def _safe_enum_value(val: Any) -> Any:
    """安全获取枚举值：有 .value 则取 .value，否则返回原值"""
    return val.value if val and hasattr(val, "value") else val


class RuralWorkService:
    """乡村工作服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_rural_works(
        self,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        type: Optional[str] = None,
        village_id: Optional[int] = None,
        search: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        year: Optional[int] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取乡村工作列表（含筛选）"""
        query = self.db.query(RuralWork)

        if status:
            query = query.filter(RuralWork.status == status)
        if type:
            query = query.filter(RuralWork.type == type)
        if village_id:
            query = query.filter(RuralWork.village_id == village_id)
        if search:
            like = f"%{search}%"
            query = query.filter(
                RuralWork.name.ilike(like) | RuralWork.description.ilike(like)
            )
        if start_date:
            try:
                dt = datetime.fromisoformat(start_date)
                query = query.filter(RuralWork.start_date >= dt)
            except ValueError:
                pass
        if end_date:
            try:
                dt = datetime.fromisoformat(end_date)
                query = query.filter(RuralWork.end_date <= dt)
            except ValueError:
                pass
        if year:
            query = query.filter(extract("year", RuralWork.start_date) == year)

        total = query.count()

        order_col = getattr(RuralWork, order_by, RuralWork.created_at)
        if order_desc:
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        rows = query.offset(skip).limit(limit).all()

        items = [
            {
                "id": r.id,
                "code": r.code,
                "name": r.name,
                "type": _safe_enum_value(r.type),
                "status": _safe_enum_value(r.status),
                "village_id": r.village_id,
                "responsible_person": r.responsible_person,
                "contact_phone": r.contact_phone,
                "start_date": _iso(r.start_date),
                "end_date": _iso(r.end_date),
                "description": r.description,
                "target": r.target,
                "progress": r.progress,
                "created_at": _iso(r.created_at),
                "updated_at": _iso(r.updated_at),
            }
            for r in rows
        ]

        return items, total

    # ── Backward-compat aliases (tests expect these method names) ──
    def get_rural_work_by_id(self, work_id: int) -> Optional[Dict[str, Any]]:
        work = self.db.query(RuralWork).filter(RuralWork.id == work_id).first()
        if not work:
            return None
        return {
            "id": work.id, "code": work.code, "name": work.name,
            "type": _safe_enum_value(work.type), "status": _safe_enum_value(work.status),
            "village_id": work.village_id,
        }

    def delete_rural_work(self, work_id: int) -> bool:
        work = self.db.query(RuralWork).filter(RuralWork.id == work_id).first()
        if not work:
            return False
        self.db.delete(work)
        self.db.commit()
        return True

    def update_rural_work(self, work_id: int, **kwargs) -> Optional[Dict]:
        work = self.db.query(RuralWork).filter(RuralWork.id == work_id).first()
        if not work:
            return None
        for k, v in kwargs.items():
            if hasattr(work, k):
                setattr(work, k, v)
        self.db.commit()
        return self.get_rural_work_by_id(work_id)

    @staticmethod
    def _generate_code() -> str:
        import uuid
        return f"RW-{uuid.uuid4().hex[:8].upper()}"
