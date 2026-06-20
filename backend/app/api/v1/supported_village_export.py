"""
帮扶村数据导出API — 完整实现（基于 SupportedVillageExportService）。
"""

import io
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
router = APIRouter(prefix="/supported-villages/export", tags=["帮扶村数据导出"])


@router.get("/modules")
async def get_export_modules(current_user=Depends(get_current_user)):
    """获取可导出的模块列表"""
    from app.services.supported_village_export_service import MODULE_NAMES
    return {"modules": [{"key": k, "label": v} for k, v in MODULE_NAMES.items()]}


@router.get("/formats")
async def get_export_formats(current_user=Depends(get_current_user)):
    """获取支持的导出格式"""
    return {"formats": [{"key": "xlsx", "label": "Excel (.xlsx)"}, {"key": "csv", "label": "CSV (.csv)"}]}


@router.get("")
async def export_supported_villages(
    year: Optional[int] = Query(None, description="筛选年份"),
    modules: Optional[str] = Query(None, description="导出模块，逗号分隔，如: basic,population,income"),
    format: str = Query("xlsx", description="导出格式: xlsx 或 pdf"),
    village_ids: Optional[str] = Query(None, description="帮扶村ID列表，逗号分隔"),
    department: Optional[str] = Query(None, description="部门筛选"),
    support_unit: Optional[str] = Query(None, description="帮扶单位筛选"),
    tiered_level: Optional[str] = Query(None, description="梯次等级筛选: 示范级 / 达标级 / 基础级"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导出帮扶村数据，返回 Excel 文件下载。"""
    from app.services.supported_village_export_service import SupportedVillageExportService

    svc = SupportedVillageExportService(db)
    mod_list = [m.strip() for m in modules.split(",") if m.strip()] if modules else None
    vid_list = [int(x.strip()) for x in village_ids.split(",") if x.strip()] if village_ids else None

    content, filename, stats = svc.export(
        year=year, modules=mod_list, format=format,
        village_ids=vid_list, department=department, support_unit=support_unit,
        tiered_level=tiered_level,
    )
    content_type = (
        "text/csv; charset=utf-8" if format == "csv"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/preview")
async def preview_export(
    year: Optional[int] = Query(None, description="筛选年份"),
    modules: Optional[str] = Query(None, description="导出模块，逗号分隔"),
    village_ids: Optional[str] = Query(None, description="帮扶村ID列表，逗号分隔"),
    department: Optional[str] = Query(None, description="部门筛选"),
    support_unit: Optional[str] = Query(None, description="帮扶单位筛选"),
    tiered_level: Optional[str] = Query(None, description="梯次等级筛选"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """预览导出数据——返回行数统计，不生成文件。"""
    from app.services.supported_village_export_service import SupportedVillageExportService

    svc = SupportedVillageExportService(db)
    mod_list = [m.strip() for m in modules.split(",") if m.strip()] if modules else None
    vid_list = [int(x.strip()) for x in village_ids.split(",") if x.strip()] if village_ids else None

    villages = svc._query_villages(
        year=year, village_ids=vid_list,
        department=department, support_unit=support_unit,
        tiered_level=tiered_level,
    )
    data = svc._collect_export_data(villages, modules=mod_list, year=year)
    stats = svc._generate_statistics(data)

    return {"success": True, "statistics": stats}
