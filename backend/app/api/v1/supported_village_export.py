"""
帮扶村数据导出API

Task 3.3: 实现数据导出服务扩展
- 扩展现有导出服务支持按年份和模块筛选
- 支持Excel和PDF格式

Requirements: 14.1, 14.2, 14.3
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.supported_village_export_service import (
    MODULE_NAMES,
    ExportFormat,
    ExportModule,
    SupportedVillageExportService,
)

router = APIRouter(prefix="/supported-villages/export", tags=["帮扶村数据导出"])


def get_export_service(db: Session = Depends(get_db)) -> SupportedVillageExportService:
    """获取导出服务实例"""
    return SupportedVillageExportService(db)


@router.get("/modules")
async def get_export_modules(current_user=Depends(get_current_user)):
    """
    获取可导出的模块列表

    Returns:
        模块列表及其中文名称
    """
    return {"modules": [{"key": m.value, "name": MODULE_NAMES[m]} for m in ExportModule]}


@router.get("/formats")
async def get_export_formats(current_user=Depends(get_current_user)):
    """
    获取支持的导出格式

    Returns:
        格式列表
    """
    return {
        "formats": [
            {
                "key": ExportFormat.EXCEL.value,
                "name": "Excel (.xlsx)",
                "description": "完整数据导出",
            },
            {
                "key": ExportFormat.PDF.value,
                "name": "PDF (.pdf)",
                "description": "适合打印，最多100条记录",
            },
        ]
    }


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
    service: SupportedVillageExportService = Depends(get_export_service),
):
    """
    导出帮扶村数据

    支持按年份和模块筛选，支持Excel和PDF格式

    Args:
        year: 筛选年份（可选）
        modules: 导出模块列表，逗号分隔（可选，默认导出全部）
            - basic: 基础信息
            - population: 人口数据
            - income: 收入数据
            - funding: 经费投入
            - force: 力量投入
            - industry: 产业帮扶
            - infrastructure: 基础设施
            - party: 党建帮扶
            - medical: 医疗帮扶
            - consumption: 消费帮扶
            - employment: 就业帮扶
            - education: 教育帮扶
            - all: 全部数据
        format: 导出格式 (xlsx / pdf)
        village_ids: 帮扶村ID列表，逗号分隔（可选）
        department: 部门筛选（可选）
        support_unit: 帮扶单位筛选（可选）
        tiered_level: 梯次等级筛选（可选）

    Returns:
        导出的文件

    Requirements: 14.1, 14.2, 14.3
    """
    # 验证格式
    if format not in [f.value for f in ExportFormat]:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")

    # 解析模块列表
    module_list = None
    if modules:
        module_list = [m.strip() for m in modules.split(",") if m.strip()]
        valid_modules = [m.value for m in ExportModule]
        for m in module_list:
            if m not in valid_modules:
                raise HTTPException(status_code=400, detail=f"无效的模块: {m}")

    # 解析帮扶村ID列表
    village_id_list = None
    if village_ids:
        try:
            village_id_list = [int(id.strip()) for id in village_ids.split(",") if id.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="帮扶村ID格式错误")

    # 验证梯次等级
    if tiered_level and tiered_level not in ["示范级", "达标级", "基础级"]:
        raise HTTPException(status_code=400, detail="无效的梯次等级")

    try:
        # 执行导出
        content, filename, statistics = service.export(
            year=year,
            modules=module_list,
            format=format,
            village_ids=village_id_list,
            department=department,
            support_unit=support_unit,
            tiered_level=tiered_level,
        )

        # 设置响应头
        if format == ExportFormat.PDF.value:
            media_type = "application / pdf"
        else:
            media_type = "application / vnd.openxmlformats - officedocument.spreadsheetml.sheet"

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content - Disposition": f"attachment; filename*=UTF - 8''{filename}",
                "X - Export - Statistics": str(statistics.get("total_villages", 0)),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/preview")
async def preview_export(
    year: Optional[int] = Query(None, description="筛选年份"),
    modules: Optional[str] = Query(None, description="导出模块，逗号分隔"),
    village_ids: Optional[str] = Query(None, description="帮扶村ID列表，逗号分隔"),
    department: Optional[str] = Query(None, description="部门筛选"),
    support_unit: Optional[str] = Query(None, description="帮扶单位筛选"),
    tiered_level: Optional[str] = Query(None, description="梯次等级筛选"),
    current_user=Depends(get_current_user),
    service: SupportedVillageExportService = Depends(get_export_service),
):
    """
    预览导出数据（返回统计信息，不生成文件）

    用于在导出前预览将要导出的数据量和统计信息

    Returns:
        统计信息
    """
    # 解析模块列表
    module_list = None
    if modules:
        module_list = [m.strip() for m in modules.split(",") if m.strip()]

    # 解析帮扶村ID列表
    village_id_list = None
    if village_ids:
        try:
            village_id_list = [int(id.strip()) for id in village_ids.split(",") if id.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="帮扶村ID格式错误")

    try:
        # 查询数据并生成统计
        villages = service._query_villages(
            village_ids=village_id_list,
            department=department,
            support_unit=support_unit,
            tiered_level=tiered_level,
        )

        # 如果没有指定模块，使用全部模块
        if not module_list:
            module_list = [m.value for m in ExportModule if m != ExportModule.ALL]

        export_data = service._collect_export_data(villages, year, module_list)
        statistics = service._generate_statistics(export_data, year, module_list)

        # 添加每个模块的记录数
        module_counts = {}
        for module in module_list:
            module_data = export_data["modules"].get(module, [])
            module_name = MODULE_NAMES.get(ExportModule(module), module)
            module_counts[module_name] = len(module_data)

        statistics["module_record_counts"] = module_counts

        return statistics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
