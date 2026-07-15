"""
数据校验规则 API
管理员可配置字段级校验规则，前端动态读取并实时校验
"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models.validation_rule import RuleType, ValidationRule

router = APIRouter(prefix="/validation", tags=["数据校验"])


# ---- Schemas ----


class ValidationRuleCreate(BaseModel):
    module: str
    field: str
    rule_type: RuleType
    params: Optional[str] = None
    error_message: str = "数据校验失败"
    description: Optional[str] = None
    is_active: bool = True
    priority: int = 100


class ValidationRuleUpdate(BaseModel):
    module: Optional[str] = None
    field: Optional[str] = None
    rule_type: Optional[RuleType] = None
    params: Optional[str] = None
    error_message: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class ValidationRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module: str
    field: str
    rule_type: str
    params: Optional[str] = None
    error_message: str
    description: Optional[str] = None
    is_active: bool
    priority: int


# ---- Endpoints ----


@router.get("/rules", response_model=List[ValidationRuleOut])
async def list_rules(
    module: Optional[str] = Query(default=None, description="按模块筛选"),
    is_active: Optional[bool] = Query(default=None, description="是否启用"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取校验规则列表"""
    query = db.query(ValidationRule)
    if module:
        query = query.filter(ValidationRule.module == module)
    if is_active is not None:
        query = query.filter(ValidationRule.is_active == is_active)
    rules = query.order_by(ValidationRule.module, ValidationRule.priority).all()
    return rules


@router.post("/rules", response_model=ValidationRuleOut)
async def create_rule(
    rule_in: ValidationRuleCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建校验规则（管理员）"""
    # 校验 params 是否为合法 JSON
    if rule_in.params:
        try:
            json.loads(rule_in.params)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="params 必须为合法 JSON 字符串")

    rule = ValidationRule(
        module=rule_in.module,
        field=rule_in.field,
        rule_type=rule_in.rule_type,
        params=rule_in.params,
        error_message=rule_in.error_message,
        description=rule_in.description,
        is_active=rule_in.is_active,
        priority=rule_in.priority,
        created_by=current_user.id,
    )
    db.add(rule)
    safe_commit(db)
    db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=ValidationRuleOut)
async def update_rule(
    rule_id: int,
    rule_in: ValidationRuleUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新校验规则"""
    rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if rule_in.params is not None:
        try:
            json.loads(rule_in.params)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="params 必须为合法 JSON 字符串")

    update_data = rule_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    safe_commit(db)
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除校验规则"""
    rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    db.delete(rule)
    safe_commit(db)
    return {"message": "规则已删除"}


# 字段中文标签映射（覆盖常用模块字段）
FIELD_LABELS: dict = {
    # 帮扶村
    "department": "部门单位",
    "support_unit": "帮扶单位",
    "village_name": "帮扶村名称",
    "county": "所在县/市",
    "region_scope": "地区范围",
    "transition_fund_military_total": "部队合计投入(万元)",
    "transition_fund_local_total": "协调地方投入(万元)",
    "per_capita_income": "人均纯收入",
    "collective_income": "村集体收入",
    "total_households": "总户数",
    "total_population": "总人数",
    # 学校
    "name": "名称",
    "student_count": "学生人数",
    "teacher_count": "教师人数",
    "class_count": "班级数量",
    "principal": "校长姓名",
    "contact_phone": "联系电话",
    # 项目 / 经费
    "budget": "预算金额",
    "actual_cost": "实际投入",
    "investment": "投入金额",
    "planned_investment": "计划投入",
    "year": "年份",
}


@router.post("/validate")
async def validate_data(
    module: str,
    data: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    对提交数据执行校验
    返回 {valid: bool, errors: [{field, field_label, rule_type, message}]}
    """
    rules = (
        db.query(ValidationRule)
        .filter(ValidationRule.module == module, ValidationRule.is_active == True)  # noqa: E712
        .order_by(ValidationRule.priority)
        .all()
    )
    errors = []
    for rule in rules:
        field_value = data.get(rule.field)
        params = json.loads(rule.params) if rule.params else {}
        error = _check_rule(rule, field_value, params, data)
        if error:
            field_label = FIELD_LABELS.get(rule.field, rule.field)
            # 如果 error_message 是泛化的默认值，自动补充字段名
            message = rule.error_message
            if message == "数据校验失败":
                message = f"{field_label}校验失败"
            errors.append(
                {
                    "field": rule.field,
                    "field_label": field_label,
                    "rule_type": rule.rule_type.value,
                    "message": message,
                }
            )
    return {"valid": len(errors) == 0, "errors": errors}


def _check_rule(rule: ValidationRule, value, params: dict, full_data: dict) -> bool:
    """检查单条规则，返回 True 表示校验失败"""
    if rule.rule_type == RuleType.required:
        return value is None or (isinstance(value, str) and value.strip() == "")
    if value is None:
        return False
    handler = _RULE_HANDLERS.get(rule.rule_type)
    return handler(value, params, full_data) if handler else False


def _check_positive(value, params, full_data):
    try:
        return float(value) <= 0
    except (ValueError, TypeError):
        return True


def _check_non_negative(value, params, full_data):
    try:
        return float(value) < 0
    except (ValueError, TypeError):
        return True


def _check_max_length(value, params, full_data):
    return len(str(value)) > params.get("max", 255)


def _check_min_length(value, params, full_data):
    return len(str(value)) < params.get("min", 0)


def _check_range(value, params, full_data):
    try:
        v = float(value)
        min_v = params.get("min")
        max_v = params.get("max")
        if min_v is not None and v < float(min_v):
            return True
        if max_v is not None and v > float(max_v):
            return True
    except (ValueError, TypeError):
        return True
    return False


def _check_regex(value, params, full_data):
    import re
    return not re.match(params.get("pattern", ""), str(value))


def _check_date_format(value, params, full_data):
    from datetime import datetime
from app.core.transaction import safe_commit
    fmt = params.get("format", "%Y-%m-%d")
    try:
        datetime.strptime(str(value), fmt)
    except ValueError:
        return True
    return False


def _check_file_type(value, params, full_data):
    allowed = params.get("allowed", [])
    if isinstance(value, str):
        ext = value.rsplit(".", 1)[-1].lower() if "." in value else ""
        return ext not in allowed
    return False


def _check_enum_values(value, params, full_data):
    allowed = params.get("values", [])
    return str(value) not in [str(v) for v in allowed]


def _check_cross_field(value, params, full_data):
    other_field = params.get("other_field")
    operator = params.get("operator", "<=")
    if other_field and other_field in full_data:
        try:
            v1 = float(value)
            v2 = float(full_data[other_field])
            if operator == "<=" and v1 > v2:
                return True
            if operator == ">=" and v1 < v2:
                return True
            if operator == "<" and v1 >= v2:
                return True
            if operator == ">" and v1 <= v2:
                return True
            if operator == "==" and v1 != v2:
                return True
        except (ValueError, TypeError):
            return True
    return False


_RULE_HANDLERS = {
    RuleType.positive: _check_positive,
    RuleType.non_negative: _check_non_negative,
    RuleType.max_length: _check_max_length,
    RuleType.min_length: _check_min_length,
    RuleType.range: _check_range,
    RuleType.regex: _check_regex,
    RuleType.date_format: _check_date_format,
    RuleType.file_type: _check_file_type,
    RuleType.enum_values: _check_enum_values,
    RuleType.cross_field: _check_cross_field,
}
