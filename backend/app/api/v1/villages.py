"""
村庄 API 路由

提供自然村的 CRUD 操作。
已优化 N+1 查询：使用 selectinload 分离查询加载关联数据（避免多 joinedload 笛卡尔积）。
"""

from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/villages", tags=["村庄管理"])


@router.get("")
async def list_villages(
    skip: int = 0,
    limit: int = 50,
    keyword: str = QueryParam(None, description="搜索关键词"),
    ethnic_group: str = QueryParam(None, description="民族属性筛选"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取村庄列表（已优化 N+1 查询）"""
    from app.models.village import Village

    query = db.query(Village).options(
        selectinload(Village.villagers),
        selectinload(Village.industries),
        selectinload(Village.tea_plantations),
        selectinload(Village.cactus_fruit_plots),
    )

    # 关键词搜索
    if keyword:
        query = query.filter(
            Village.name.ilike(f"%{keyword}%")
            | Village.code.ilike(f"%{keyword}%")
            | Village.county.ilike(f"%{keyword}%")
        )

    # 民族属性筛选
    if ethnic_group:
        query = query.filter(Village.ethnic_group == ethnic_group)

    # 数据权限过滤
    from app.core.data_permission import filter_by_data_scope
    query = filter_by_data_scope(query, Village, current_user, db=db)

    villages = query.offset(skip).limit(limit).all()

    return [
        {
            "id": v.id,
            "name": v.name,
            "code": v.code,
            "province": v.province,
            "city": v.city,
            "county": v.county,
            "township": v.township,
            "ethnic_group": getattr(v, "ethnic_group", ""),
            "is_ethnic_village": getattr(v, "is_ethnic_village", False),
            "karst_ratio": getattr(v, "karst_ratio", 0.0),
            "terrain_type": v.terrain_type or "",
            "region_code": v.region_code or "",
            "latitude": v.latitude,
            "longitude": v.longitude,
            "villager_count": len(v.villagers) if v.villagers else 0,
            "industry_count": len(v.industries) if v.industries else 0,
            "tea_plantation_count": len(v.tea_plantations)
            if v.tea_plantations
            else 0,
            "cactus_fruit_count": len(v.cactus_fruit_plots)
            if v.cactus_fruit_plots
            else 0,
        }
        for v in villages
    ]


@router.get("/{village_id}")
async def get_village(
    village_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取单个村庄详情（已优化 N+1 查询）"""
    from app.models.village import Village

    village = (
        db.query(Village)
        .options(
            selectinload(Village.villagers),
            selectinload(Village.industries),
            selectinload(Village.tea_plantations),
            selectinload(Village.cactus_fruit_plots),
        )
        .filter(Village.id == village_id)
        .first()
    )
    if not village:
        raise HTTPException(status_code=404, detail="村庄不存在")
    return {
        "id": village.id,
        "name": village.name,
        "code": village.code,
        "province": village.province,
        "city": village.city,
        "county": village.county,
        "township": village.township,
        "description": village.description,
        "ethnic_group": getattr(village, "ethnic_group", ""),
        "is_ethnic_village": getattr(village, "is_ethnic_village", False),
        "karst_ratio": getattr(village, "karst_ratio", 0.0),
        "terrain_type": village.terrain_type or "",
        "region_code": village.region_code or "",
        "latitude": village.latitude,
        "longitude": village.longitude,
        "villagers": [
            {
                "id": vl.id,
                "name": vl.name,
                "phone": vl.phone,
                "is_poverty": vl.is_poverty,
            }
            for vl in (village.villagers or [])
        ],
        "industries": [
            {"id": ind.id, "name": ind.name, "industry_type": ind.industry_type}
            for ind in (village.industries or [])
        ],
    }
