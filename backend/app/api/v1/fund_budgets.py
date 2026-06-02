"""经费预算与使用明细 API"""

import logging
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.fund_budget import FundBudget, FundTransaction, check_budget_alerts
from app.api.v1.deps import require_manager_role as _require_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fund-budgets", tags=["经费预算"])

# ==================== Pydantic 模型 ====================


class BudgetCreate(BaseModel):
    year: int = Field(..., ge=2000, le=2099)
    category: str = Field(..., min_length=1, max_length=100)
    budget_amount: float = Field(..., ge=0)
    village_id: Optional[int] = None
    organization_id: Optional[int] = None
    description: Optional[str] = None
    remarks: Optional[str] = None


class BudgetUpdate(BaseModel):
    budget_amount: Optional[float] = Field(None, ge=0)
    executed_amount: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    remarks: Optional[str] = None


class BudgetResponse(BaseModel):
    id: int
    year: int
    category: str
    budget_amount: float
    executed_amount: float
    remaining_amount: float = 0
    execution_rate: float = 0
    village_id: Optional[int] = None
    organization_id: Optional[int] = None
    description: Optional[str] = None
    remarks: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    fund_id: Optional[int] = None
    project_id: Optional[int] = None
    village_id: Optional[int] = None
    budget_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    category: Optional[str] = None
    purpose: str = Field(..., min_length=1, description="用途说明")
    transaction_date: date
    receipt_number: Optional[str] = None
    handler: Optional[str] = None
    reimbursement_person: Optional[str] = None
    remarks: Optional[str] = None

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        """验证并清理用途说明"""
        if v:
            v = v.strip()
            if not v:
                raise ValueError("用途说明不能为空或仅包含空格")
        return v


class TransactionResponse(BaseModel):
    id: int
    fund_id: Optional[int] = None
    project_id: Optional[int] = None
    village_id: Optional[int] = None
    budget_id: Optional[int] = None
    amount: float
    category: Optional[str] = None
    purpose: str
    transaction_date: date
    receipt_number: Optional[str] = None
    handler: Optional[str] = None
    reimbursement_person: Optional[str] = None
    status: str
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ==================== 预算 API ====================


@router.get("", response_model=List[BudgetResponse])
async def get_budgets(
    year: Optional[int] = None,
    category: Optional[str] = None,
    village_id: Optional[int] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取预算列表"""
    query = db.query(FundBudget)
    if year:
        query = query.filter(FundBudget.year == year)
    if category:
        query = query.filter(FundBudget.category == category)
    if village_id:
        query = query.filter(FundBudget.village_id == village_id)

    budgets = query.order_by(FundBudget.year.desc(), FundBudget.category).all()

    result = []
    for b in budgets:
        data = b.to_dict()
        data["remaining_amount"] = b.remaining_amount
        data["execution_rate"] = b.execution_rate
        result.append(data)
    return result


@router.post("", response_model=BudgetResponse)
async def create_budget(
    data: BudgetCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建预算（仅管理角色）"""
    _require_manager(current_user)
    budget = FundBudget(
        **data.model_dump(),
        created_by=getattr(current_user, "id", None),
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)

    resp = budget.to_dict()
    resp["remaining_amount"] = budget.remaining_amount
    resp["execution_rate"] = budget.execution_rate
    return resp


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新预算（仅管理角色）"""
    _require_manager(current_user)
    budget = db.query(FundBudget).filter(FundBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(budget, key, value)
    db.commit()
    db.refresh(budget)

    resp = budget.to_dict()
    resp["remaining_amount"] = budget.remaining_amount
    resp["execution_rate"] = budget.execution_rate
    return resp


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除预算（仅管理角色）"""
    _require_manager(current_user)
    budget = db.query(FundBudget).filter(FundBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")
    db.delete(budget)
    db.commit()
    return {"message": "删除成功"}


# ==================== 预算预警 ====================


@router.get("/alerts")
async def get_budget_alerts(
    year: Optional[int] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取预算预警信息（首页仪表板用）"""
    query = db.query(FundBudget)
    if year:
        query = query.filter(FundBudget.year == year)
    else:
        # 默认当前年度
        query = query.filter(FundBudget.year == date.today().year)

    budgets = query.all()
    alerts = check_budget_alerts(budgets)
    return {"items": alerts, "total": len(alerts)}


# ==================== 预算汇总 ====================


@router.get("/summary")
async def get_budget_summary(
    year: Optional[int] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取预算汇总统计"""
    target_year = year or date.today().year
    budgets = db.query(FundBudget).filter(FundBudget.year == target_year).all()

    total_budget = sum(float(b.budget_amount or 0) for b in budgets)
    total_executed = sum(float(b.executed_amount or 0) for b in budgets)

    # 按科目汇总
    by_category = {}
    for b in budgets:
        cat = b.category or "其他"
        if cat not in by_category:
            by_category[cat] = {"budget": 0, "executed": 0}
        by_category[cat]["budget"] += float(b.budget_amount or 0)
        by_category[cat]["executed"] += float(b.executed_amount or 0)

    return {
        "year": target_year,
        "total_budget": round(total_budget, 2),
        "total_executed": round(total_executed, 2),
        "total_remaining": round(total_budget - total_executed, 2),
        "execution_rate": (round(total_executed / total_budget * 100, 2) if total_budget > 0 else 0),
        "by_category": [
            {
                "category": cat,
                "budget": round(v["budget"], 2),
                "executed": round(v["executed"], 2),
                "remaining": round(v["budget"] - v["executed"], 2),
                "rate": (round(v["executed"] / v["budget"] * 100, 2) if v["budget"] > 0 else 0),
            }
            for cat, v in by_category.items()
        ],
    }


# ==================== 使用明细 API ====================


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    fund_id: Optional[int] = None,
    project_id: Optional[int] = None,
    village_id: Optional[int] = None,
    budget_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取经费使用明细列表"""
    query = db.query(FundTransaction)
    if fund_id:
        query = query.filter(FundTransaction.fund_id == fund_id)
    if project_id:
        query = query.filter(FundTransaction.project_id == project_id)
    if village_id:
        query = query.filter(FundTransaction.village_id == village_id)
    if budget_id:
        query = query.filter(FundTransaction.budget_id == budget_id)

    items = (
        query.order_by(FundTransaction.transaction_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    )
    return items


@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    data: TransactionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建经费使用明细（仅管理角色）"""
    _require_manager(current_user)
    transaction = FundTransaction(
        **data.model_dump(),
        created_by=getattr(current_user, "id", None),
    )
    db.add(transaction)

    # 如果关联了预算，自动更新已执行金额
    if data.budget_id:
        budget = db.query(FundBudget).filter(FundBudget.id == data.budget_id).first()
        if budget:
            budget.executed_amount = float(budget.executed_amount or 0) + data.amount

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除经费使用明细（仅管理角色）"""
    _require_manager(current_user)
    tx = db.query(FundTransaction).filter(FundTransaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="明细不存在")

    # 如果关联了预算，减回已执行金额
    if tx.budget_id:
        budget = db.query(FundBudget).filter(FundBudget.id == tx.budget_id).first()
        if budget:
            budget.executed_amount = max(0, float(budget.executed_amount or 0) - float(tx.amount or 0))

    db.delete(tx)
    db.commit()
    return {"message": "删除成功"}
