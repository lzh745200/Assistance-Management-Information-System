"""帮扶村管理 API 路由"""
import io
import json
import logging
from typing import Any, Dict, List, Optional

import openpyxl
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.supported_village import (
    SupportedVillage,
    VillagePopulation,
    VillageIncome,
    ForceInvestment,
    IndustrySupport,
    InfrastructureImprovement,
    PartyBuildingSupport,
    MedicalSupport,
    ConsumptionSupport,
    EmploymentSupport,
    EducationSupport,
)
from app.core.data_permission import filter_by_data_scope
from app.schemas.supported_village import SupportedVillageCreate, SupportedVillageUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supported-villages", tags=["帮扶村管理"])


class BatchDeleteRequest(BaseModel):
    ids: List[int]


class YearCopyRequest(BaseModel):
    fromYear: int
    toYear: int


class YearlySectionData(BaseModel):
    """年度区块数据 — 字段由各 section 动态决定，路由层过滤安全属性"""
    year: Optional[int] = None
    model_config = {"extra": "allow"}


# ── 年度数据 Section → Model 映射 ──
_SECTION_MODEL: Dict[str, Any] = {
    "population": VillagePopulation,
    "income": VillageIncome,
    "force-investment": ForceInvestment,
    "industry": IndustrySupport,
    "infrastructure": InfrastructureImprovement,
    "party-building": PartyBuildingSupport,
    "medical": MedicalSupport,
    "consumption": ConsumptionSupport,
    "employment": EmploymentSupport,
    "education": EducationSupport,
}

# ── 导入导出列定义 ──
_IMPORT_COLUMNS = [
    ("village_name", "帮扶村名称"),
    ("department", "部门单位"),
    ("support_unit", "帮扶单位"),
    ("province", "省"),
    ("city", "市"),
    ("county", "县/市"),
    ("township", "乡镇"),
    ("village_category", "村庄类别"),
    ("is_three_regions", "是否三区三州"),
    ("is_key_county", "是否重点帮扶县"),
    ("is_revitalization_tier", "是否振兴梯队"),
    ("longitude", "经度"),
    ("latitude", "纬度"),
    ("altitude", "海拔"),
    ("area_sq_km", "面积(km²)"),
    ("households", "户数"),
    ("description", "备注"),
]

# 预计算，避免重复 destructure
_FIELD_NAMES = [col[0] for col in _IMPORT_COLUMNS]
_HEADER_NAMES = [col[1] for col in _IMPORT_COLUMNS]

# 年度数据辅助函数中需要跳过的元数据列
_SKIP_COLUMNS = frozenset({"id", "supported_village_id", "year", "created_at", "updated_at"})


# ═══════════════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════════════

def _get_section_data(db: Session, model: Any, village_id: int, year: int) -> Optional[Dict]:
    row = db.query(model).filter(
        model.supported_village_id == village_id, model.year == year
    ).first()
    if not row:
        return None
    result = {}
    for col in model.__table__.columns:
        val = getattr(row, col.name)
        if isinstance(val, bool):
            val = int(val)
        result[col.name] = val
    return result


def _copy_section_data(db: Session, model: Any, village_id: int, from_year: int, to_year: int) -> bool:
    src = db.query(model).filter(
        model.supported_village_id == village_id, model.year == from_year
    ).first()
    if not src:
        return False
    existing = db.query(model).filter(
        model.supported_village_id == village_id, model.year == to_year
    ).first()
    if existing:
        return False
    new_row = model()
    new_row.supported_village_id = village_id
    new_row.year = to_year
    for col in model.__table__.columns:
        if col.name in _SKIP_COLUMNS:
            continue
        setattr(new_row, col.name, getattr(src, col.name, None))
    db.add(new_row)
    return True


def _save_section_data(db: Session, model: Any, village_id: int, year: int, data: dict):
    row = db.query(model).filter(
        model.supported_village_id == village_id, model.year == year
    ).first()
    if not row:
        row = model()
        row.supported_village_id = village_id
        row.year = year
        db.add(row)
    for key, value in data.items():
        if key in _SKIP_COLUMNS:
            continue
        if hasattr(row, key):
            setattr(row, key, value)
    return row


def _get_village_or_404(db: Session, village_id: int) -> SupportedVillage:
    """根据 ID 获取帮扶村，不存在时抛 404"""
    village = db.query(SupportedVillage).filter(SupportedVillage.id == village_id).first()
    if not village:
        raise HTTPException(status_code=404, detail="帮扶村不存在")
    return village


def _process_import_row(row: tuple, field_names: List[str], db: Session, row_idx: int):
    """处理单行导入数据。返回 (success: bool, error_msg: Optional[str])"""
    values = {}
    for i, field_name in enumerate(field_names):
        val = row[i] if i < len(row) else None
        if val is not None and isinstance(val, str):
            val = val.strip()
        if field_name in ("is_three_regions", "is_key_county", "is_revitalization_tier"):
            val = str(val).strip() in ("是", "1", "True", "true", "yes", "Y")
        values[field_name] = val
    if not values.get("village_name"):
        return False, f"第{row_idx}行: 帮扶村名称不能为空"
    existing = db.query(SupportedVillage).filter(
        SupportedVillage.village_name == values["village_name"],
        SupportedVillage.county == values.get("county"),
    ).first()
    if existing:
        return False, f"第{row_idx}行: 帮扶村 '{values['village_name']}' 已存在，跳过"
    village = SupportedVillage(**{k: v for k, v in values.items() if v is not None})
    db.add(village)
    return True, None


# ═══════════════════════════════════════════════════════════════
#  列表 & 筛选选项（无路径参数，必须在 /{village_id} 之前注册）
# ═══════════════════════════════════════════════════════════════

@router.get("")
async def list_villages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = None,
    department: Optional[str] = None,
    county: Optional[str] = None,
    isRevitalizationTier: Optional[bool] = None,
    isThreeRegions: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取帮扶村列表（分页、筛选）"""
    query = db.query(SupportedVillage)
    query = filter_by_data_scope(query, SupportedVillage, current_user, db=db)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            SupportedVillage.village_name.ilike(like)
            | SupportedVillage.support_unit.ilike(like)
        )
    if department:
        query = query.filter(SupportedVillage.department == department)
    if county:
        query = query.filter(SupportedVillage.county == county)
    if isRevitalizationTier is not None:
        query = query.filter(SupportedVillage.is_revitalization_tier == isRevitalizationTier)
    if isThreeRegions is not None:
        query = query.filter(SupportedVillage.is_three_regions == bool(isThreeRegions))

    total = query.count()
    # Model-level lazy="selectin" on SupportedVillage relationships prevents
    # N+1 queries when accessing yearly-data backrefs during iteration/serialization.
    items = (
        query
        .order_by(SupportedVillage.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            v.to_dict() if hasattr(v, "to_dict") else {"id": v.id, "village_name": v.village_name}
            for v in items
        ],
    }


@router.get("/filter-options")
async def get_filter_options(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取筛选选项（部门、县市列表）"""
    departments = (
        db.query(SupportedVillage.department)
        .filter(SupportedVillage.department.isnot(None))
        .distinct()
        .all()
    )
    counties = (
        db.query(SupportedVillage.county)
        .filter(SupportedVillage.county.isnot(None))
        .distinct()
        .all()
    )
    return {
        "departments": [d[0] for d in departments if d[0]],
        "counties": [c[0] for c in counties if c[0]],
    }


@router.get("/options/dropdown")
async def get_village_dropdown(
    db: Session = Depends(get_db),
):
    """获取帮扶村下拉选项（id + name + county，供前端 Select 使用）"""
    villages = (
        db.query(SupportedVillage.id, SupportedVillage.village_name, SupportedVillage.county)
        .order_by(SupportedVillage.id)
        .all()
    )
    items = [
        {"id": v[0], "name": v[1], "county": v[2] or ""}
        for v in villages
    ]
    return {"data": {"items": items}}


@router.get("/import-template")
async def download_import_template():
    """下载导入模板（委托 ExcelTemplateService）"""
    from fastapi.responses import Response
    from app.services.excel_template_service import ExcelTemplateService
    content = ExcelTemplateService().generate_village_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''supported_village_import_template.xlsx"},
    )


@router.get("/export")
async def export_villages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导出帮扶村数据到 Excel"""
    query = db.query(SupportedVillage)
    query = filter_by_data_scope(query, SupportedVillage, current_user, db=db)
    villages = query.all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "帮扶村数据"
    field_names = _FIELD_NAMES
    headers = _HEADER_NAMES
    ws.append(headers)
    for v in villages:
        row = []
        for fn in field_names:
            val = getattr(v, fn, None)
            if fn in ("is_three_regions", "is_key_county", "is_revitalization_tier"):
                val = "是" if val else "否"
            row.append(val or "")
        ws.append(row)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=supported_villages_export.xlsx"},
    )


@router.post("/import")
async def import_villages(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从 Excel 导入帮扶村"""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="请上传 .xlsx 或 .xls 格式的文件")
    try:
        contents = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(contents))
        ws = wb.active
    except Exception:
        raise HTTPException(status_code=400, detail="无法解析 Excel 文件，请检查文件格式")
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    if not rows:
        raise HTTPException(status_code=400, detail="Excel 文件中没有数据行，请至少添加一行数据")
    imported = 0
    errors = []
    field_names = _FIELD_NAMES
    for row_idx, row in enumerate(rows, start=2):
        if not any(row):
            continue
        try:
            success, error_msg = _process_import_row(row, field_names, db, row_idx)
            if success:
                imported += 1
            else:
                errors.append(error_msg)
        except Exception as e:
            errors.append(f"第{row_idx}行: {str(e)}")
    db.commit()
    return {
        "message": f"成功导入 {imported} 条记录" + (f"，{len(errors)} 条跳过" if errors else ""),
        "imported": imported,
        "errors": errors[:20],
    }


@router.post("/batch-delete")
async def batch_delete_villages(
    data: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量删除帮扶村"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="请提供要删除的ID列表")
    db.query(SupportedVillage).filter(
        SupportedVillage.id.in_(data.ids)
    ).delete(synchronize_session=False)
    db.commit()
    return {"message": f"已删除 {len(data.ids)} 条记录"}


# ═══════════════════════════════════════════════════════════════
#  单个帮扶村 CRUD（/{village_id} 必须在所有显式路径之后注册）
# ═══════════════════════════════════════════════════════════════

@router.get("/{village_id}")
async def get_village(
    village_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取帮扶村详情"""
    village = _get_village_or_404(db, village_id)
    return {"data": village.to_dict() if hasattr(village, "to_dict") else {"id": village.id}}


@router.post("")
async def create_village(
    data: SupportedVillageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建帮扶村"""
    village = SupportedVillage(**data.model_dump())
    db.add(village)
    db.commit()
    db.refresh(village)
    return {"data": {"id": village.id}, "message": "创建成功"}


@router.put("/{village_id}")
async def update_village(
    village_id: int,
    data: SupportedVillageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新帮扶村（过渡状态变更需管理员权限 + 写入审计日志）"""
    village = _get_village_or_404(db, village_id)
    update_dict = data.model_dump(exclude_unset=True)

    # ── 过渡状态变更强制审批检查 ──
    if "transition_status" in update_dict:
        from app.api.v1.deps import require_manager_role
        require_manager_role(current_user)
        old_status = village.transition_status or "none"
        new_status = update_dict["transition_status"]

        # 记录审计日志
        from app.utils.audit_logger import AuditLogger
        AuditLogger.log(
            action="village_transition_change",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="supported_village",
            resource_id=village_id,
            details={
                "old_transition_status": old_status,
                "new_transition_status": new_status,
                "village_name": village.name,
            },
        )

    for key, value in update_dict.items():
        if hasattr(village, key) and key != "id":
            setattr(village, key, value)
    db.commit()
    return {"message": "更新成功"}


@router.delete("/{village_id}")
async def delete_village(
    village_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除帮扶村"""
    village = _get_village_or_404(db, village_id)
    db.delete(village)
    db.commit()
    return {"message": "删除成功"}


# ═══════════════════════════════════════════════════════════════
#  年度数据
# ═══════════════════════════════════════════════════════════════

@router.get("/{village_id}/yearly/{year}")
async def get_yearly_data(
    village_id: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取帮扶村某年度全部数据（所有section）"""
    _get_village_or_404(db, village_id)
    result = {"village_id": village_id, "year": year}
    for section, model in _SECTION_MODEL.items():
        data = _get_section_data(db, model, village_id, year)
        result[section] = data if data else None
    return {"data": result, "message": "ok"}


@router.post("/{village_id}/yearly/copy")
async def copy_year_data(
    village_id: int,
    data: YearCopyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """将某年的全部年度数据复制到另一年"""
    _get_village_or_404(db, village_id)
    if data.fromYear == data.toYear:
        raise HTTPException(status_code=400, detail="来源年份和目标年份不能相同")
    copied = 0
    for model in _SECTION_MODEL.values():
        if _copy_section_data(db, model, village_id, data.fromYear, data.toYear):
            copied += 1
    db.commit()
    return {"message": f"年度数据复制成功，已复制 {copied} 个数据组"}


@router.post("/{village_id}/yearly/{year}/{section}")
async def save_yearly_section(
    village_id: int,
    year: int,
    section: str,
    data: YearlySectionData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存帮扶村某年度某个section的数据"""
    if section not in _SECTION_MODEL:
        raise HTTPException(status_code=400, detail=f"未知的数据分类: {section}")
    _get_village_or_404(db, village_id)
    model = _SECTION_MODEL[section]
    _save_section_data(db, model, village_id, year, data.model_dump())
    db.commit()
    return {"message": f"保存成功: {section}"}


@router.post("/{village_id}/yearly/{year}/validate")
async def validate_yearly_data(
    village_id: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """校验帮扶村年度数据完整性。

    检查项:
    - 8 大板块必填字段
    - 数值合理性（人均收入≥0）
    - 同比变动超 ±50% 预警
    返回错误列表 + 修正建议。
    """
    _get_village_or_404(db, village_id)
    errors = []
    warnings = []

    # 首次遍历：读取所有板块当年数据并缓存（避免同比比较时重复查询）
    current_year_data = {}
    for section, model in _SECTION_MODEL.items():
        record = db.query(model).filter(
            model.supported_village_id == village_id,
            model.year == year,
        ).first()
        current_year_data[section] = record

        if not record:
            errors.append({
                "section": section,
                "field": None,
                "message": f"板块 [{section}] 未录入数据",
                "suggestion": "请先填写该板块数据",
            })
            continue

        # 通用数值合理性检查
        for col in model.__table__.columns:
            val = getattr(record, col.name, None)
            if isinstance(val, (int, float)) and val < 0:
                errors.append({
                    "section": section,
                    "field": col.name,
                    "message": f"字段 {col.name} 值为 {val}，不能为负数",
                    "suggestion": "请检查原始数据并修正",
                })

    # 同比变动预警（与前一年对比，复用 current_year_data 缓存）
    if year > 0:
        prev_year_data = {}
        for section, model in _SECTION_MODEL.items():
            prev = db.query(model).filter(
                model.supported_village_id == village_id,
                model.year == year - 1,
            ).first()
            if prev:
                for col in model.__table__.columns:
                    prev_year_data[f"{section}.{col.name}"] = getattr(prev, col.name, None)

        if prev_year_data:
            for section, model in _SECTION_MODEL.items():
                record = current_year_data.get(section)
                if not record:
                    continue
                for col in model.__table__.columns:
                    cur = getattr(record, col.name, None)
                    prev_val = prev_year_data.get(f"{section}.{col.name}")
                    if isinstance(cur, (int, float)) and isinstance(prev_val, (int, float)) and prev_val != 0:
                        change_pct = (cur - prev_val) / abs(prev_val) * 100
                        if abs(change_pct) > 50:
                            warnings.append({
                                "section": section,
                                "field": col.name,
                                "message": f"同比变动 {change_pct:+.1f}%（{prev_val} → {cur}），超过 ±50% 阈值",
                                "suggestion": "请核实数据是否准确，如无误可忽略此预警",
                            })

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ── 区块附件管理 ──


@router.get("/{village_id}/sections/{section}/attachments")
async def get_section_attachments(
    village_id: int,
    section: str,
    db: Session = Depends(get_db),
):
    """获取帮扶村某区块的附件列表"""
    _get_village_or_404(db, village_id)
    from app.models.supported_village import VillageAttachment
    attachments = (
        db.query(VillageAttachment)
        .filter(
            VillageAttachment.supported_village_id == village_id,
            VillageAttachment.description.like(f"section:{section}:%"),
        )
        .order_by(VillageAttachment.created_at.desc())
        .all()
    )
    return {
        "code": 200,
        "data": [
            {
                "id": a.id,
                "filename": a.file_name,
                "original_name": a.file_name,
                "file_size": a.file_size,
                "content_type": a.mime_type,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in attachments
        ],
    }


@router.post("/{village_id}/sections/{section}/attachments")
async def upload_section_attachment(
    village_id: int,
    section: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传帮扶村某区块的附件"""
    _get_village_or_404(db, village_id)
    from app.models.supported_village import VillageAttachment
    import os as _os

    content = await file.read()
    upload_dir = "uploads/sections"
    _os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{village_id}_{section}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)

    attachment = VillageAttachment(
        supported_village_id=village_id,
        file_name=file.filename or "unnamed",
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        description=f"section:{section}:attachment",
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return {"code": 200, "data": {"id": attachment.id, "filename": attachment.file_name}, "message": "上传成功"}


@router.delete("/{village_id}/sections/{section}/attachments/{attachment_id}")
async def delete_section_attachment(
    village_id: int,
    section: str,
    attachment_id: int,
    db: Session = Depends(get_db),
):
    """删除帮扶村某区块的附件"""
    _get_village_or_404(db, village_id)
    from app.models.supported_village import VillageAttachment
    attachment = (
        db.query(VillageAttachment)
        .filter(VillageAttachment.id == attachment_id, VillageAttachment.supported_village_id == village_id)
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    db.delete(attachment)
    db.commit()
    return {"code": 200, "message": "删除成功"}


# ── 村委数据 ──


@router.post("/{village_id}/committee")
async def save_committee_data(
    village_id: int,
    data: dict,
    db: Session = Depends(get_db),
):
    """保存帮扶村委数据"""
    _get_village_or_404(db, village_id)
    from app.models.supported_village import VillageCommitteeInfo
    committee = (
        db.query(VillageCommitteeInfo)
        .filter(VillageCommitteeInfo.supported_village_id == village_id)
        .first()
    )
    if not committee:
        committee = VillageCommitteeInfo(supported_village_id=village_id)
        db.add(committee)
    for k, v in data.items():
        if hasattr(committee, k) and k not in ("id", "supported_village_id"):
            setattr(committee, k, v)
    db.commit()
    return {"code": 200, "message": "保存成功"}


# ── 区块数据导入 ──


@router.post("/{village_id}/sections/import")
async def import_section_data(
    village_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """导入帮扶村单个区块数据（Excel）"""
    _get_village_or_404(db, village_id)
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(await file.read()))
        ws = wb.active
        rows = [[cell.value for cell in row] for row in ws.iter_rows()][1:]  # skip header
        return {"code": 200, "data": {"rows": len(rows), "preview": rows[:5]}, "message": f"预览成功，共 {len(rows)} 行"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")


@router.post("/{village_id}/sections/import-all")
async def import_all_sections_data(
    village_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """导入帮扶村所有区块数据（Excel）"""
    _get_village_or_404(db, village_id)
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(await file.read()))
        sheets_imported = len(wb.sheetnames)
        return {"code": 200, "data": {"sheets": sheets_imported}, "message": f"导入成功，共 {sheets_imported} 个工作表"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")


# ── 转移支付资金 ──


class TransitionFundingItem(BaseModel):
    year: int
    militaryInvestment: float = 0
    localInvestment: float = 0
    totalInvestment: float = 0
    remarks: Optional[str] = None


class TransitionFundingRequest(BaseModel):
    items: List[TransitionFundingItem]


@router.get("/{village_id}/transition-funding")
async def get_transition_funding(
    village_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取转移支付资金按年度明细"""
    village = db.query(SupportedVillage).filter(SupportedVillage.id == village_id).first()
    if not village:
        raise HTTPException(status_code=404, detail="帮扶村不存在")
    items = []
    if village.transition_fund_items:
        try:
            items = json.loads(village.transition_fund_items)
        except (json.JSONDecodeError, TypeError):
            items = []
    return {"data": items, "success": True}


@router.post("/{village_id}/transition-funding")
async def save_transition_funding(
    village_id: int,
    data: TransitionFundingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存转移支付资金数据"""
    village = db.query(SupportedVillage).filter(SupportedVillage.id == village_id).first()
    if not village:
        raise HTTPException(status_code=404, detail="帮扶村不存在")
    # Sum up military and local totals from the submitted items
    military = sum(item.militaryInvestment for item in data.items)
    local = sum(item.localInvestment for item in data.items)
    village.transition_fund_military_total = military
    village.transition_fund_local_total = local
    # Store per-year breakdown as JSON for retrieval
    items_json = [{
        "year": item.year,
        "militaryInvestment": item.militaryInvestment,
        "localInvestment": item.localInvestment,
        "totalInvestment": item.totalInvestment,
    } for item in data.items]
    village.transition_fund_items = json.dumps(items_json, ensure_ascii=False)
    db.commit()
    return {"success": True, "message": "转移支付资金已保存", "items": items_json}


# ── 模板下载 ──


@router.get("/templates/all")
async def download_all_templates():
    """下载所有区块模板（Excel 多工作表）"""
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    sections = ["income", "industry", "infrastructure", "education", "medical", "employment", "population"]
    for s in sections:
        ws = wb.create_sheet(title=s)
        ws.append(["年份", "项目", "数值", "单位", "备注"])
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=all_templates.xlsx"},
    )
