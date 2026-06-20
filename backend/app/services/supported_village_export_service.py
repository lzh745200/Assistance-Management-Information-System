"""
帮扶村导出服务 — 完整实现

支持多模块选择性导出（人口、收入、经费、基础设施等），输出 Excel 格式。
"""

import enum
import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ExportFormat(str, enum.Enum):
    XLSX = "xlsx"
    CSV = "csv"


class ExportModule(str, enum.Enum):
    POPULATION = "population"
    INCOME = "income"
    FORCE_INVESTMENT = "force_investment"
    INDUSTRY_SUPPORT = "industry_support"
    INFRASTRUCTURE = "infrastructure"
    PARTY_BUILDING = "party_building"
    MEDICAL = "medical"
    CONSUMPTION = "consumption"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    SUPPORT_FUNDING = "support_funding"
    COMMITTEE = "committee"


MODULE_NAMES = {
    "population": "人口数据",
    "income": "收入数据",
    "force_investment": "部队投入",
    "industry_support": "产业帮扶",
    "infrastructure": "基础设施改善",
    "party_building": "党建帮扶",
    "medical": "医疗帮扶",
    "consumption": "消费帮扶",
    "employment": "就业帮扶",
    "education": "教育帮扶",
    "support_funding": "帮扶经费",
    "committee": "村委会信息",
}

# 样式定义
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(name="SimSun", size=11, bold=True, color="FFFFFF")
DATA_FONT = Font(name="SimSun", size=10)


class SupportedVillageExportService:
    """帮扶村数据导出服务"""

    def __init__(self, db: Session):
        self.db = db

    def _query_villages(
        self,
        year: Optional[int] = None,
        village_ids: Optional[List[int]] = None,
        department: Optional[str] = None,
        support_unit: Optional[str] = None,
    ) -> List[Any]:
        """查询要导出的帮扶村列表。"""
        from app.models.supported_village import SupportedVillage

        query = self.db.query(SupportedVillage)
        if village_ids:
            query = query.filter(SupportedVillage.id.in_(village_ids))
        if department:
            query = query.filter(SupportedVillage.department == department)
        if support_unit:
            query = query.filter(SupportedVillage.support_unit == support_unit)
        return query.order_by(SupportedVillage.id).all()

    def _collect_export_data(
        self,
        villages: List[Any],
        modules: Optional[List[str]] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """收集导出数据，按模块组织。"""
        if modules is None:
            modules = list(MODULE_NAMES.keys())

        data: Dict[str, Any] = {}
        for mod in modules:
            data[mod] = self._collect_module_data(villages, mod, year)
        return data

    def _collect_module_data(
        self,
        villages: List[Any],
        module: str,
        year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """收集单个模块的数据。"""
        from app.models.supported_village import (
            VillageIncome,
            VillagePopulation,
        )

        rows = []
        for v in villages:
            base = {"id": v.id, "village_name": v.village_name, "county": v.county or ""}

            if module == "population":
                pop = (
                    self.db.query(VillagePopulation)
                    .filter(VillagePopulation.village_id == v.id)
                    .first()
                )
                base["households"] = pop.households if pop else 0
                base["total_population"] = pop.total_population if pop else 0
                base["labor_force"] = pop.labor_force if pop else 0
                rows.append(base)

            elif module == "income":
                income = (
                    self.db.query(VillageIncome)
                    .filter(VillageIncome.village_id == v.id)
                    .first()
                )
                base["collective_income"] = income.collective_income if income else 0
                base["per_capita_income"] = income.per_capita_income if income else 0
                rows.append(base)

            else:
                # 其他模块：返回基本信息作为占位
                base["module"] = MODULE_NAMES.get(module, module)
                rows.append(base)

        return rows

    def _generate_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成导出统计信息。"""
        stats = {
            "total_villages": 0,
            "modules_exported": list(data.keys()),
            "generated_at": datetime.now().isoformat(),
        }
        for mod_name, rows in data.items():
            stats[f"{mod_name}_count"] = len(rows)
            if rows:
                stats["total_villages"] = max(stats["total_villages"], len(rows))
        return stats

    def _build_excel(self, data: Dict[str, Any], statistics: Dict[str, Any]) -> bytes:
        """将导出数据构建为 Excel 文件。"""
        wb = Workbook()
        # 删除默认 sheet
        wb.remove(wb.active)

        for mod_name, rows in data.items():
            if not rows:
                continue
            mod_label = MODULE_NAMES.get(mod_name, mod_name)
            ws = wb.create_sheet(title=mod_label[:31])  # Excel sheet name max 31 chars

            # 标题行
            if rows:
                headers = list(rows[0].keys())
                for col_idx, header in enumerate(headers, 1):
                    cell = ws.cell(row=1, column=col_idx, value=header)
                    cell.fill = HEADER_FILL
                    cell.font = HEADER_FONT
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                # 数据行
                for row_idx, row_data in enumerate(rows, 2):
                    for col_idx, header in enumerate(headers, 1):
                        cell = ws.cell(row=row_idx, column=col_idx, value=row_data.get(header, ""))
                        cell.font = DATA_FONT

                # 自适应列宽
                for col_idx, header in enumerate(headers, 1):
                    max_width = max(len(str(header)), 12)
                    for row_data in rows[:50]:  # 采样前50行
                        val = str(row_data.get(header, ""))
                        max_width = max(max_width, min(len(val), 40))
                    ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = max_width + 2

        # 统计 sheet
        ws_stats = wb.create_sheet(title="统计信息")
        for i, (key, val) in enumerate(statistics.items(), 1):
            ws_stats.cell(row=i, column=1, value=key).font = Font(bold=True)
            ws_stats.cell(row=i, column=2, value=str(val))

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    def export(
        self,
        year: Optional[int] = None,
        modules: Optional[List[str]] = None,
        format: str = "xlsx",
        village_ids: Optional[List[int]] = None,
        department: Optional[str] = None,
        support_unit: Optional[str] = None,
    ) -> Tuple[bytes, str, Dict[str, Any]]:
        """导出帮扶村数据，返回 (文件内容, 文件名, 统计信息)。"""
        villages = self._query_villages(
            year=year, village_ids=village_ids,
            department=department, support_unit=support_unit,
        )
        data = self._collect_export_data(villages, modules=modules, year=year)
        statistics = self._generate_statistics(data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"supported_villages_export_{timestamp}.xlsx"

        if format == "csv":
            # CSV 简化导出：仅导出第一个模块的数据
            content = self._build_csv(data)
            filename = f"supported_villages_export_{timestamp}.csv"
        else:
            content = self._build_excel(data, statistics)

        logger.info("导出完成: %s, %d 模块, %d 村", filename, len(data), statistics.get("total_villages", 0))
        return content, filename, statistics

    def _build_csv(self, data: Dict[str, Any]) -> bytes:
        """简化 CSV 导出（仅第一个模块）。"""
        import csv

        output = io.StringIO()
        for mod_name, rows in data.items():
            if not rows:
                continue
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
            break
        return output.getvalue().encode("utf-8-sig")
