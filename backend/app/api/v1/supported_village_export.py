"""
帮扶村数据导出API

WIP: 路由已注册为501占位 — SupportedVillageExportService 待完整实现。
完整实现约需 300-400 行（openpyxl 多 sheet、数据查询聚合、统计计算）。
前端 API 接线已完成（getExportModules / getExportFormats / previewExport），
产品未启用此功能前 501 是最低风险的兜底策略。

Requirements: 14.1, 14.2, 14.3
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.security import get_current_user
router = APIRouter(prefix="/supported-villages/export", tags=["帮扶村数据导出"])


def _wip_response():
    return JSONResponse(
        status_code=501,
        content={"detail": "该功能正在开发中", "code": "WIP"},
    )


@router.get("/modules")
async def get_export_modules(current_user=Depends(get_current_user)):
    """获取可导出的模块列表（WIP: 501 占位）"""
    return _wip_response()


@router.get("/formats")
async def get_export_formats(current_user=Depends(get_current_user)):
    """获取支持的导出格式（WIP: 501 占位）"""
    return _wip_response()


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
):
    """导出帮扶村数据（WIP: 501 占位）"""
    return _wip_response()


@router.get("/preview")
async def preview_export(
    year: Optional[int] = Query(None, description="筛选年份"),
    modules: Optional[str] = Query(None, description="导出模块，逗号分隔"),
    village_ids: Optional[str] = Query(None, description="帮扶村ID列表，逗号分隔"),
    department: Optional[str] = Query(None, description="部门筛选"),
    support_unit: Optional[str] = Query(None, description="帮扶单位筛选"),
    tiered_level: Optional[str] = Query(None, description="梯次等级筛选"),
    current_user=Depends(get_current_user),
):
    """预览导出数据（WIP: 501 占位）"""
    return _wip_response()
