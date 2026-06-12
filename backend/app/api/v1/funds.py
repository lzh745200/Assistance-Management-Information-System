"""
经费管理 API 路由 (最终优化版)

军用级离线桌面管理系统 - 经费全流程管理
重构亮点：
1. 全面拥抱 SQLAlchemy 2.0 (select 语法)
2. 修复状态流转中的字段映射 Bug (allocated_at -> allocation_date 等)
3. 引入严格的状态机校验，防止非法状态流转
4. 统计接口性能极致优化 (单次聚合、消灭 strftime 全表扫描)
5. 集成 DataScope 数据权限隔离
6. 修复 list_funds 中 status 参数名覆盖 fastapi.status 模块的致命隐患
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.v1.deps import require_manager_role
from app.core.database import get_db
from app.core.security import get_current_user
from app.utils.pagination import keyset_paginate
from app.core.data_permission import apply_data_scope

from app.models.fund import Fund
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/funds", tags=["经费管理"])


# ============================================================================
# Pydantic Schemas (建议后续移至 app/schemas/fund.py)
# ============================================================================


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


# ============================================================================
# 辅助工具与序列化
# ============================================================================

# 缓存驼峰命名映射，避免每次请求都反射和转换，提升序列化性能
try:
    from app.utils.common import StringHelper
    _FUND_CAMEL_MAP = {col.name: StringHelper.to_camel_case(col.name) for col in Fund.__table__.columns}
except ImportError:
    # 降级处理：如果 StringHelper 不可用，使用简单替换
    _FUND_CAMEL_MAP = {
        col.name: (
            col.name.replace('_', ' ').title().replace(' ', '')[:1].lower()
            + col.name.replace('_', ' ').title().replace(' ', '')[1:]
        )
        for col in Fund.__table__.columns
    }


def _safe_val(val: Any) -> Any:
    """安全转换数据库值为 JSON 可序列化类型"""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, datetime):
        return val.isoformat()
    if hasattr(val, "isoformat"):  # 兼容 date 类型
        return val.isoformat()
    return val


def _fund_to_dict(f: Fund) -> Dict[str, Any]:
    """将 Fund ORM 对象转为字典（camelCase 键名，前端直接使用）"""
    result = {}
    for col_name, camel_name in _FUND_CAMEL_MAP.items():
        result[camel_name] = _safe_val(getattr(f, col_name, None))

    # 补充关联数据（如果使用了 joinedload 预加载）
    if hasattr(f, "project") and f.project:
        result["projectName"] = f.project.name
    if hasattr(f, "village") and f.village:
        result["villageName"] = f.village.name

    return result


def _get_fund_or_404(db: Session, fund_id: int, current_user: User) -> Fund:
    """通用：获取经费并校验权限，不存在则抛出 404"""
    stmt = select(Fund).where(Fund.id == fund_id)
    stmt = apply_data_scope(stmt, Fund, current_user)
    fund = db.execute(stmt).scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="经费记录不存在或无权访问")
    return fund


# ============================================================================
# 1. 基础 CRUD 操作
# ============================================================================


@router.get("")
def list_funds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = None,
    # 🚨 修复：使用 status_filter 避免覆盖 fastapi.status 模块，通过 alias 保持 API 契约
    status_filter: Optional[str] = Query(None, alias="status"),
    fund_type: Optional[str] = None,
    fund_source: Optional[str] = None,
    project_id: Optional[int] = None,
    village_id: Optional[int] = None,
    cursor: Optional[str] = Query(None, description="Keyset分页游标"),
    pagination: str = Query("offset", description="分页方式: 'offset' | 'keyset'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询经费列表（支持OFFSET和Keyset两种分页）"""
    # 1. 构建基础查询 (SQLAlchemy 2.0)
    stmt = select(Fund).options(
        selectinload(Fund.project),
        selectinload(Fund.village)
    )

    # 2. 数据权限隔离
    stmt = apply_data_scope(stmt, Fund, current_user)

    # 3. 动态过滤
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(
            (Fund.name.ilike(kw)) | (Fund.code.ilike(kw)) | (Fund.purpose.ilike(kw))
        )
    if status_filter:
        stmt = stmt.where(Fund.status == status_filter)
    if fund_type:
        stmt = stmt.where(Fund.fund_type == fund_type)
    if fund_source:
        stmt = stmt.where(Fund.fund_source == fund_source)
    if project_id:
        stmt = stmt.where(Fund.project_id == project_id)
    if village_id:
        stmt = stmt.where(Fund.village_id == village_id)

    # 4. 分页执行
    if pagination == "keyset":
        result = keyset_paginate(
            stmt, order_column=Fund.id, page_size=page_size, cursor=cursor, desc=True, db=db
        )
        return {
            "total": result["total"], "page_size": result["page_size"],
            "items": [_fund_to_dict(f) for f in result["items"]],
            "next_cursor": result["next_cursor"], "has_more": result["has_more"],
            "pagination": "keyset",
        }

    # 传统 OFFSET 分页 (手动构建以完美兼容 apply_data_scope 和 joinedload)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()

    items_stmt = stmt.order_by(Fund.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(items_stmt).scalars().unique().all()

    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [_fund_to_dict(f) for f in items], "pagination": "offset",
    }


@router.get("/export")
def export_funds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(5000, ge=1, le=50000, description="最大导出条数"),
):
    """导出经费数据（带分页上限，防止内存溢出）"""
    stmt = select(Fund).order_by(Fund.id.desc()).limit(limit)
    stmt = apply_data_scope(stmt, Fund, current_user)
    funds = db.execute(stmt).scalars().all()
    return {
        "data": [_fund_to_dict(f) for f in funds],
        "total_exported": len(funds), "limit": limit,
    }


@router.get("/{fund_id}")
def get_fund(
    fund_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询经费详情"""
    stmt = (
        select(Fund)
        .where(Fund.id == fund_id)
        .options(joinedload(Fund.project), joinedload(Fund.village), selectinload(Fund.organization))
    )
    stmt = apply_data_scope(stmt, Fund, current_user)
    fund = db.execute(stmt).scalar_one_or_none()

    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="经费记录不存在或无权访问")
    return {"data": _fund_to_dict(fund)}


def _create_fund_impl(
    data: FundCreate,
    current_user: User,
    db: Session,
    *,
    status: Optional[str] = None,
    applicant: Optional[str] = None,
) -> Fund:
    """共享的经费创建逻辑"""
    fund = Fund(**data.model_dump(exclude_none=True))
    fund.created_by = current_user.id
    fund.organization_id = current_user.organization_id
    if status is not None:
        fund.status = status
    if applicant is not None:
        fund.applicant = applicant
    db.add(fund)
    db.commit()
    db.refresh(fund)
    return fund


@router.post("", status_code=status.HTTP_201_CREATED)
def create_fund(
    data: FundCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建经费记录（需管理员权限）"""
    require_manager_role(current_user)
    fund = _create_fund_impl(data, current_user, db)
    return {"data": {"id": fund.id}, "message": "创建成功"}


@router.post("/apply", status_code=status.HTTP_201_CREATED)
def apply_fund(
    data: FundCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户经费申请 — 无需管理员权限，所有登录用户均可提交"""
    fund = _create_fund_impl(
        data, current_user, db,
        status="pending",
        applicant=current_user.full_name or current_user.username,
    )
    return {"data": {"id": fund.id}, "message": "申请已提交，等待审批"}


@router.put("/{fund_id}")
def update_fund(
    fund_id: int,
    data: FundUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新经费记录"""
    require_manager_role(current_user)
    fund = _get_fund_or_404(db, fund_id, current_user)

    # 业务校验：已审批或已拨付的经费不允许随意修改核心字段
    if fund.status not in ["pending", "planned", "rejected"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不允许修改")

    for key, value in data.model_dump(exclude_none=True).items():
        if hasattr(fund, key):
            setattr(fund, key, value)
        else:
            logger.warning("update_fund: skipping unknown field '%s' on Fund(id=%d)", key, fund_id)

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
    fund = _get_fund_or_404(db, fund_id, current_user)

    if fund.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅允许删除待审批(pending)状态的经费")

    db.delete(fund)
    db.commit()
    return {"message": "删除成功"}


# ============================================================================
# 2. 资金统计 (极致性能优化)
# ============================================================================


@router.get("/statistics/overview")
def fund_statistics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """经费统计概览 (单次聚合查询)"""
    stmt = select(
        func.count(Fund.id).label("total_count"),
        func.coalesce(func.sum(Fund.amount), 0).label("total_amount"),
        func.sum(case((Fund.status == "pending", 1), else_=0)).label("pending_count"),
        func.sum(case((Fund.status == "approved", 1), else_=0)).label("approved_count"),
    )
    stmt = apply_data_scope(stmt, Fund, current_user)

    row = db.execute(stmt).one()
    return {
        "data": {
            "total_count": row.total_count,
            "total_amount": float(row.total_amount),
            "pending_count": row.pending_count,
            "approved_count": row.approved_count,
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
    """经费多维度统计分析 (利用冗余字段消灭全表扫描)"""
    stmt = select(Fund)
    stmt = apply_data_scope(stmt, Fund, current_user)

    try:
        if start_date:
            stmt = stmt.where(Fund.date >= datetime.strptime(start_date, "%Y-%m-%d").date())
        if end_date:
            stmt = stmt.where(Fund.date <= datetime.strptime(end_date, "%Y-%m-%d").date())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式错误，请使用 YYYY-MM-DD 格式")

    agg_cols = [
        func.count(Fund.id).label("count"),
        func.coalesce(func.sum(Fund.amount), 0).label("total_amount"),
        func.coalesce(func.sum(Fund.allocated_amount), 0).label("total_allocated"),
        func.coalesce(func.sum(Fund.used_amount), 0).label("total_used"),
    ]

    if group_by == "period":
        if period_type == "quarterly":
            group_col = Fund.year_quarter
        elif period_type == "yearly":
            group_col = Fund.year
        else:
            group_col = Fund.year_month

        stmt = stmt.with_only_columns(
            group_col.label("group_key"), *agg_cols
        ).group_by(group_col).order_by(group_col)

    elif group_by in ("type", "source", "status"):
        col_map = {"type": Fund.fund_type, "source": Fund.fund_source, "status": Fund.status}
        group_col = col_map[group_by]
        stmt = stmt.with_only_columns(group_col.label("group_key"), *agg_cols).group_by(group_col)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的分组维度: {group_by}")

    rows = db.execute(stmt).all()

    label_maps = {
        "source": {"military": "军队投资", "government": "政府拨款", "donation": "社会捐赠", "enterprise": "企业投资", "other": "其他"},
        "status": {
            "pending": "待审批", "planned": "规划中", "approved": "已批准",
            "allocated": "已拨付", "in_use": "使用中", "completed": "已完成", "audited": "已审计",
        },
        "type": {
            "project": "项目经费", "operation": "运营经费", "education": "教育帮扶",
            "infrastructure": "基础设施", "emergency": "应急经费", "other": "其他",
        }
    }
    current_map = label_maps.get(group_by, {})

    result = []
    for r in rows:
        key = r.group_key or "未知"
        if not key:
            continue

        label = str(key) if group_by == "period" else current_map.get(key, key)
        total_amt = float(r.total_amount or 0)
        used_amt = float(r.total_used or 0)

        result.append({
            "label": label,
            "count": r.count,
            "total_amount": round(total_amt, 2),
            "total_allocated": round(float(r.total_allocated or 0), 2),
            "total_used": round(used_amt, 2),
            "utilization_rate": round((used_amt / total_amt * 100), 1) if total_amt > 0 else 0,
        })

    return {"success": True, "data": result}


# ============================================================================
# 3. 资金审批流程 (严格状态机校验)
# ============================================================================


def _transition_status(db: Session, fund: Fund, target_status: str, allowed_statuses: List[str], **kwargs):
    """内部辅助：状态流转核心逻辑"""
    if fund.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"状态流转非法：当前状态为 '{fund.status}'，不允许变更为 '{target_status}'"
        )
    fund.status = target_status
    for k, v in kwargs.items():
        if hasattr(fund, k):
            setattr(fund, k, v)
        else:
            logger.warning("_transition_status: skipping unknown field '%s' on Fund(id=%d)", k, fund.id)
    db.commit()


@router.post("/{fund_id}/approve")
def approve_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager_role(current_user)
    fund = _get_fund_or_404(db, fund_id, current_user)
    _transition_status(db, fund, "approved", ["pending", "planned"],
                       approved_by=current_user.full_name or current_user.username,
                       approval_date=datetime.now(timezone.utc))
    return {"message": "审批通过"}


@router.post("/{fund_id}/reject")
def reject_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager_role(current_user)
    fund = _get_fund_or_404(db, fund_id, current_user)
    _transition_status(db, fund, "rejected", ["pending", "planned"],
                       approved_by=current_user.full_name or current_user.username)
    return {"message": "审批驳回"}


@router.post("/{fund_id}/allocate")
def allocate_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager_role(current_user)
    fund = _get_fund_or_404(db, fund_id, current_user)
    _transition_status(db, fund, "allocated", ["approved"],
                       allocation_date=datetime.now(timezone.utc))
    return {"message": "经费已拨付"}


@router.post("/{fund_id}/start-use")
def start_use_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager_role(current_user)
    fund = _get_fund_or_404(db, fund_id, current_user)
    _transition_status(db, fund, "in_use", ["allocated"],
                       start_date=datetime.now(timezone.utc))
    return {"message": "经费已开始使用"}


@router.post("/{fund_id}/complete")
def complete_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager_role(current_user)
    fund = _get_fund_or_404(db, fund_id, current_user)
    _transition_status(db, fund, "completed", ["in_use"],
                       end_date=datetime.now(timezone.utc))
    return {"message": "经费使用完成"}


@router.post("/{fund_id}/audit")
def audit_fund(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager_role(current_user)
    fund = _get_fund_or_404(db, fund_id, current_user)
    _transition_status(db, fund, "audited", ["completed"],
                       audit_date=datetime.now(timezone.utc))
    return {"message": "经费审计完成"}


# ============================================================================
# 4. 帮扶村资金统计 & 历史
# ============================================================================


@router.get("/supported-village/statistics/by-type")
def fund_stats_by_type(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(
        Fund.fund_type,
        func.count(Fund.id).label("count"),
        func.coalesce(func.sum(Fund.amount), 0).label("amount")
    ).group_by(Fund.fund_type)
    stmt = apply_data_scope(stmt, Fund, current_user)
    rows = db.execute(stmt).all()
    return {"data": [{"type": r.fund_type or "其他", "count": r.count, "amount": float(r.amount)} for r in rows]}


@router.get("/supported-village/statistics/yearly-comparison")
def fund_stats_yearly_comparison(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"data": []}


@router.get("/supported-village/statistics/utilization-rate")
def fund_stats_utilization(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"data": {"overall_rate": 0, "by_type": []}}


@router.get("/supported-village/statistics/summary")
def fund_stats_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(
        func.count(Fund.id).label("total_count"),
        func.coalesce(func.sum(Fund.amount), 0).label("total_amount")
    )
    stmt = apply_data_scope(stmt, Fund, current_user)
    row = db.execute(stmt).one()
    return {"data": {"total_count": row.total_count, "total_amount": float(row.total_amount)}}


@router.get("/{fund_id}/history/status")
def fund_history_status(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_fund_or_404(db, fund_id, current_user)
    return {"data": []}


@router.get("/{fund_id}/history/fields")
def fund_history_fields(fund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"data": []}


@router.get("/{fund_id}/history/operations")
def fund_history_operations(
    fund_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"data": []}
