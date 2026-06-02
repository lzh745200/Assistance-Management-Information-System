"""报表导出服务 — 委托给 ExcelExportService。"""
import logging

from app.services.export_service import ExcelExportService

logger = logging.getLogger(__name__)


class ReportExportService:
    """报表导出服务（单例）"""

    @staticmethod
    async def export_to_excel(data: list, columns: list, filename: str) -> bytes:
        return ExcelExportService.export(data, columns, filename)

    # ── Word/PDF 导出（委托给 export_service） ──

    def generate_summary_report_data(self, db, year: int) -> dict:
        """生成汇总报表数据"""
        logger.warning("generate_summary_report_data 尚未实现，返回空数据")
        return {"year": year, "sections": []}

    def generate_fund_detail_report_data(self, db, year: int) -> dict:
        """生成经费明细报表数据"""
        logger.warning("generate_fund_detail_report_data 尚未实现，返回空数据")
        return {"year": year, "items": []}

    def generate_project_progress_report_data(self, db, year: int) -> dict:
        """生成项目进度报表数据"""
        logger.warning("generate_project_progress_report_data 尚未实现，返回空数据")
        return {"year": year, "projects": []}

    def export_word(self, report_type: str, data: dict) -> bytes:
        """导出 Word 文档"""
        logger.warning("export_word 尚未实现")
        return b""

    def export_pdf(self, report_type: str, data: dict) -> bytes:
        """导出 PDF 文档"""
        logger.warning("export_pdf 尚未实现")
        return b""


# 向后兼容单例
report_export_service = ReportExportService()
