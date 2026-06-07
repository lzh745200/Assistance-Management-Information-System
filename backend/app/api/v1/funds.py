"""经费管理 API 路由"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import require_manager_role
from app.core.database import get_db
from app.core.security import get_current_user
from app.utils.pagination import keyset_paginate
from sqlalchemy import Integer
from sqlalchemy.sql import func

from app.models.fund import Fund
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/funds", tags=["经费管理"])


class FundCreate(BaseModel):
    """创建经费记录"""
    name: Optional[str] = None
    amount: float = 0
    planned_amount: float = 0
    code: Optional[str] = None
    type: Optional[str] = None
    fund_type: Optional[str] = None
    fund_source: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    village_id: Optional[int] = None
    school_id: Optional[int] = None
    purpose: Optional[str] = None
    source: Optional[str] = None
    operator: Optional[str] = None
    status: str = "pending"
    applicant: Optional[str] = None
    remarks: Optional[str] = None
    date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    model_config = {"extra": "forbid"}


class FundUpdate(BaseModel):
    """更新经费记录"""
    name: Optional[str] = None
    amount: Optional[float] = None
    planned_amount: Optional[float] = None
    approved_amount: Optional[float] = None
    allocated_amount: Optional[float] = None
    used_amount: Optional[float] = None
    remaining_amount: Optional[float] = None
    code: Optional[str] = None
    type: Optional[str] = None
    fund_type: Optional[str] = None
    fund_source: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    village_id: Optional[int] = None
    school_id: Optional[int] = None
    purpose: Optional[str] = None
    source: Optional[str] = None
    operator: Optional[str] = None
    status: Optional[str] = None
    applicant: Optional[str] = None
    remarks: Optional[str] = None
    date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    approved_by: Optional[str] = None
    approval_date: Optional[str] = None

    model_config = {"extra": "forbid"}


def _fund_to_dict(f: Fund) -> Dict[str, Any]:
    """将 Fund ORM 对象转为字典（camelCase 键名，前端直接使用）"""
    from app.utils.common import StringHelper
    cols = Fund.__table__.columns
    result = {}
    for col in cols:
        val = getattr(f, col.name, None)
        result[StringHelper.to_camel_case(col.name)] = val
    return result


@router.get("")
def list_funds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    fund_type: Optional[str] = None,
    fund_source: Optional[str] = None,
    project_id: Optional[int] = None,
    village_id: Optional[int] = None,
    cursor: Optional[str] = Query(None, description="Keyset分页游标（优先于page参数）"),
    pagination: str = Query("offset", description="分页方式: 'offset' | 'keyset'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询经费列表（支持OFFSET和Keyset两种分页）"""
    query = db.query(Fund)

    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            (Fund.name.ilike(kw))
            | (Fund.code.ilike(kw))
            | (Fund.purpose.ilike(kw))
        )
    if status:
        query = query.filter(Fund.status == status)
    if fund_type:
        query = query.filter(Fund.fund_type == fund_type)
    if fund_source:
        query = query.filter(Fund.fund_source == fund_source)
    if project_id:
        query = query.filter(Fund.project_id == project_id)
    if village_id:
        query = query.filter(Fund.village_id == village_id)

    # Keyset分页（高性能，推荐大数据量使用）
    if pagination == "keyset":
        result = keyset_paginate(
            query,
            order_column=Fund.id,
            page_size=page_size,
            cursor=cursor,
            desc=True,
        )
        return {
            "total": result["total"],
            "page_size": result["page_size"],
            "items": [_fund_to_dict(f) for f in result["items"]],
            "next_cursor": result["next_cursor"],
            "has_more": result["has_more"],
            "pagination": "keyset",
        }

    # 传统OFFSET分页（兼容旧版）
    total = query.count()
    items = query.order_by(Fund.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_fund_to_dict(f) for f in items],
        "pagination": "offset",
    }


# ── 资金导出（必须在 /{fund_id} 之前注册）──

@router.get("/export")
def export_funds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(5000, ge=1, le=50000, description="最大导出条数"),
):
    """导出经费数据（带分页上限，防止内存溢出）"""
    funds = db.query(Fund).order_by(Fund.id.desc()).limit(limit).all()
    return {
        "data": [_fund_to_dict(f) for f in funds],
        "total_exported": len(funds),
        "limit": limit,
    }


@router.get("/{fund_id}")
def get_fund(
    fund_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询经费详情"""
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="经费记录不存在")
    return {"data": _fund_to_dict(fund)}


@router.post("")
def create_fund(
    data: FundCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建经费记录"""
    require_manager_role(current_user)
    fund = Fund()
    for key, value in data.model_dump(exclude_none=True).items():
        if hasattr(fund, key):
            setattr(fund, key, value)
    db.add(fund)
    db.commit()
    db.refresh(fund)
    return {"data": {"id": fund.id}, "message": "创建成功"}


@router.put("/{fund_id}")
def update_fund(
    fund_id: int,
    data: FundUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新经费记录"""
    require_manager_role(current_user)
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="经费记录不存在")
    for key, value in data.model_dump(exclude_none=True).items():
        if hasattr(fund, key):
            setattr(fund, key, value)
    db.commit()
    return {"message": "更新成功"}


@router.delete("/{fund_id}")
def delete_fund(
    fund_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除经费记录"""
    require_manager_role(current_user)
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="经费记录不存在")
    db.delete(fund)
    db.commit()
    return {"message": "删除成功"}


# ── 资金统计 ──

@router.get("/statistics/overview")
def fund_statistics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """经费统计概览"""
    total = db.query(Fund).count()
    total_amount = db.query(Fund).with_entities(
        func.sum(Fund.amount)
    ).scalar() or 0
    pending_count = db.query(Fund).filter(Fund.status == "pending").count()
    approved_count = db.query(Fund).filter(Fund.status == "approved").count()
    return {
        "data": {
            "total_count": total,
            "total_amount": float(total_amount),
            "pending_count": pending_count,
            "approved_count": approved_count,
        }
    }


@router.get("/statistics/multi-dimension")
def fund_statistics_multi_dimension(
    group_by: str = Query("type", description="分组维度: period, type, source, status"),
    start_date: str = Query(None, description="起始日期 YYYY-MM-DD"),
    end_date: str = Query(None, description="结束日期 YYYY-MM-DD"),
    period_type: str = Query("monthly", description="时间粒度: monthly, quarterly, yearly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """经费多维度统计分析 — 按来源/状态/类型/时间聚合

    返回统一格式: {success: true, data: [{label, count, total_amount, total_allocated, total_used, utilization_rate}, ...]}
    """
    from datetime import datetime as dt

    base = db.query(Fund)
    try:
        if start_date:
            base = base.filter(Fund.date >= dt.strptime(start_date, "%Y-%m-%d").date())
        if end_date:
            base = base.filter(Fund.date <= dt.strptime(end_date, "%Y-%m-%d").date())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式错误，请使用 YYYY-MM-DD 格式",
        )

    # 定义维度映射
    dimension_map = {
        "type": Fund.fund_type,
        "source": Fund.fund_source,
        "status": Fund.status,
    }

    if group_by == "period":
        # 时间维度：按粒度分组
        if period_type == "quarterly":
            # 季度聚合：((month-1)//3)+1 = 1,2,3,4
            quarter_expr = ((func.cast(func.strftime("%m", Fund.date), Integer) - 1) / 3 + 1)
            rows = (
                base.with_entities(
                    func.strftime("%Y", Fund.date).label("year"),
                    func.cast(quarter_expr, Integer).label("quarter"),
                    func.count(Fund.id).label("count"),
                    func.coalesce(func.sum(Fund.amount), 0).label("total_amount"),
                    func.coalesce(func.sum(Fund.allocated_amount), 0).label("total_allocated"),
                    func.coalesce(func.sum(Fund.used_amount), 0).label("total_used"),
                )
                .group_by(func.strftime("%Y", Fund.date), quarter_expr)
                .order_by(func.strftime("%Y", Fund.date), quarter_expr)
                .all()
            )
        elif period_type == "yearly":
            rows = (
                base.with_entities(
                    func.strftime("%Y", Fund.date).label("year"),
                    func.count(Fund.id).label("count"),
                    func.coalesce(func.sum(Fund.amount), 0).label("total_amount"),
                    func.coalesce(func.sum(Fund.allocated_amount), 0).label("total_allocated"),
                    func.coalesce(func.sum(Fund.used_amount), 0).label("total_used"),
                )
                .group_by(func.strftime("%Y", Fund.date))
                .order_by(func.strftime("%Y", Fund.date))
                .all()
            )
        else:
            # monthly (default)
            rows = (
                base.with_entities(
                    func.strftime("%Y", Fund.date).label("year"),
                    func.strftime("%m", Fund.date).label("month"),
                    func.count(Fund.id).label("count"),
                    func.coalesce(func.sum(Fund.amount), 0).label("total_amount"),
                    func.coalesce(func.sum(Fund.allocated_amount), 0).label("total_allocated"),
                    func.coalesce(func.sum(Fund.used_amount), 0).label("total_used"),
                )
                .group_by(func.strftime("%Y", Fund.date), func.strftime("%m", Fund.date))
                .order_by(func.strftime("%Y", Fund.date), func.strftime("%m", Fund.date))
                .all()
            )
        result = []
        for r in rows:
            if not r[0]:
                continue
            if period_type == "quarterly":
                label = f"{r[0]}Q{r[1]}"
            elif period_type == "yearly":
                label = str(r[0])
            else:
                label = f"{r[0]}-{r[1]}" if len(r) > 1 and r[1] else str(r[0])
            result.append({
                "label": label,
                "count": r.count,
                "total_amount": round(float(r.total_amount or 0), 2),
                "total_allocated": round(float(r.total_allocated or 0), 2),
                "total_used": round(float(r.total_used or 0), 2),
                "utilization_rate": round(
                    float(r.total_used or 0) / float(r.total_amount or 1) * 100, 1
                ) if float(r.total_amount or 0) > 0 else 0,
            })
    elif group_by in dimension_map:
        col = dimension_map[group_by]
        rows = (
            base.with_entities(
                col.label("group_key"),
                func.count(Fund.id).label("count"),
                func.coalesce(func.sum(Fund.amount), 0).label("total_amount"),
                func.coalesce(func.sum(Fund.allocated_amount), 0).label("total_allocated"),
                func.coalesce(func.sum(Fund.used_amount), 0).label("total_used"),
            )
            .group_by(col)
            .all()
        )
        # 来源维度标签映射
        source_labels = {
            "military": "军队投资", "government": "政府拨款",
            "donation": "社会捐赠", "enterprise": "企业投资", "other": "其他",
        }
        # 状态维度标签映射
        status_labels = {
            "pending": "待审批", "planned": "规划中", "approved": "已批准",
            "allocated": "已拨付", "in_use": "使用中", "completed": "已完成",
            "audited": "已审计",
        }
        # 类型维度标签映射
        type_labels = {
            "project": "项目经费", "operation": "运营经费",
            "education": "教育帮扶", "infrastructure": "基础设施",
            "emergency": "应急经费", "other": "其他",
        }
        label_map = (
            source_labels if group_by == "source"
            else status_labels if group_by == "status"
            else type_labels if group_by == "type"
            else {}
        )
        result = []
        for r in rows:
            key = r.group_key or "未知"
            result.append({
                "label": label_map.get(key, key),
                "count": r.count,
                "total_amount": round(float(r.total_amount or 0), 2),
                "total_allocated": round(float(r.total_allocated or 0), 2),
                "total_used": round(float(r.total_used or 0), 2),
                "utilization_rate": round(
                    float(r.total_used or 0) / float(r.total_amount or 1) * 100, 1
                ) if float(r.total_amount or 0) > 0 else 0,
            })
    else:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的分组维度: {group_by}，支持: period, type, source, status",
        )

    return {"success": True, "data": result}


# ── 资金审批流程 ──

@router.post("/{fund_id}/approve")
def approve_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager_role(current_user)
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="经费记录不存在")
    fund.status = "approved"
    fund.approved_by = current_user.full_name or current_user.username
    from datetime import datetime, timezone
    fund.approval_date = datetime.now(timezone.utc)
    db.commit()
    return {"message": "审批通过"}


@router.post("/{fund_id}/reject")
def reject_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager_role(current_user)
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="经费记录不存在")
    fund.status = "rejected"
    fund.approved_by = current_user.full_name or current_user.username
    db.commit()
    return {"message": "审批驳回"}


@router.post("/{fund_id}/allocate")
def allocate_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """经费拨付"""
    require_manager_role(current_user)
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="经费记录不存在")
    from datetime import datetime, timezone
    fund.status = "allocated"
    fund.allocated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "经费已拨付"}


@router.post("/{fund_id}/start-use")
def start_use_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """经费开始使用"""
    require_manager_role(current_user)
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="经费记录不存在")
    from datetime import datetime, timezone
    fund.status = "in_use"
    fund.used_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "经费已开始使用"}


@router.post("/{fund_id}/complete")
def complete_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """经费使用完成"""
    require_manager_role(current_user)
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="经费记录不存在")
    from datetime import datetime, timezone
    fund.status = "completed"
    fund.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "经费使用完成"}


@router.post("/{fund_id}/audit")
def audit_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """经费审计"""
    require_manager_role(current_user)
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="经费记录不存在")
    from datetime import datetime, timezone
    fund.status = "audited"
    fund.audited_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "经费审计完成"}


# ── 帮扶村资金统计 ──

@router.get("/supported-village/statistics/by-type")
def fund_stats_by_type(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """帮扶村资金按类型统计"""
    from sqlalchemy import func as sa_func
    rows = db.query(Fund.fund_type, sa_func.count(Fund.id), sa_func.sum(Fund.amount)).group_by(Fund.fund_type).all()
    return {"data": [{"type": r[0] or "其他", "count": r[1], "amount": float(r[2] or 0)} for r in rows]}


@router.get("/supported-village/statistics/yearly-comparison")
def fund_stats_yearly_comparison(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """帮扶村资金年度对比"""
    return {"data": []}


@router.get("/supported-village/statistics/utilization-rate")
def fund_stats_utilization(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """帮扶村资金使用率"""
    return {"data": {"overall_rate": 0, "by_type": []}}


@router.get("/supported-village/statistics/summary")
def fund_stats_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """帮扶村资金汇总"""
    from sqlalchemy import func as sa_func
    total_count = db.query(sa_func.count(Fund.id)).scalar() or 0
    total_amount = db.query(sa_func.sum(Fund.amount)).scalar() or 0
    return {"data": {"total_count": total_count, "total_amount": float(total_amount)}}


# ── 资金历史 ──

@router.get("/{fund_id}/history/status")
def fund_history_status(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="经费记录不存在")
    return {"data": []}


@router.get("/{fund_id}/history/fields")
def fund_history_fields(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"data": []}


@router.get("/{fund_id}/history/operations")
def fund_history_operations(
        fund_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    return {"data": []}
