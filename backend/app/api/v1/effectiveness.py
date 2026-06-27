"""
成效评估API
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user, get_db
from app.core.data_permission import filter_by_data_scope
from app.models.user import User
from app.models.village import Village
from app.services.effectiveness_service import EffectivenessService

router = APIRouter(prefix="/effectiveness", tags=["成效评估"])


class EvaluateRequest(BaseModel):
    """评估请求"""

    village_id: int
    year: int


@router.post("/evaluate")
async def evaluate_village(
    request: EvaluateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    评估村庄成效
    需要管理员权限
    """
    if not current_user.is_superuser:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="需要管理员权限")

    result = EffectivenessService.evaluate_village(
        db=db, village_id=request.village_id, year=request.year, user_id=current_user.id
    )

    if "error" in result:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/report/{village_id}")
async def get_evaluation_report(
    village_id: int,
    year: int = Query(..., description="年份"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取评估报告"""
    village = filter_by_data_scope(
        db.query(Village).filter(Village.id == village_id),
        Village, current_user, db=db
    ).first()
    if not village:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="评估报告不存在")

    report = EffectivenessService.get_evaluation_report(db=db, village_id=village_id, year=year)

    if not report:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="评估报告不存在")

    return report


@router.get("/compare/{village_id}")
async def compare_evaluations(
    village_id: int,
    year1: int = Query(..., description="年份1"),
    year2: int = Query(..., description="年份2"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """对比两年的评估结果"""
    village = filter_by_data_scope(
        db.query(Village).filter(Village.id == village_id),
        Village, current_user, db=db
    ).first()
    if not village:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="评估报告不存在")

    comparison = EffectivenessService.compare_evaluations(db=db, village_id=village_id, year1=year1, year2=year2)

    if "error" in comparison:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=comparison["error"])

    return comparison


@router.get("/rankings")
async def get_rankings(
    year: int = Query(..., description="年份"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取排名列表"""
    from app.models.effectiveness import EffectivenessEvaluation

    query = (
        db.query(EffectivenessEvaluation, Village.name)
        .join(Village, EffectivenessEvaluation.village_id == Village.id)
        .filter(EffectivenessEvaluation.year == year)
    )
    query = filter_by_data_scope(query, Village, current_user, db=db)
    evaluations = query.order_by(EffectivenessEvaluation.rank).limit(limit).all()

    return {
        "year": year,
        "rankings": [
            {
                "rank": eval.rank,
                "village_id": eval.village_id,
                "village_name": village_name,
                "total_score": eval.total_score,
                "grade": eval.grade,
            }
            for eval, village_name in evaluations
        ],
    }
