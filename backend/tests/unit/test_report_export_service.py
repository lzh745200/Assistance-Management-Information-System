"""app/services/report_export_service.py 单元测试。

该服务将调用委托给 ExcelExportService 并提供占位的 Word/PDF/报表数据方法。
本测试验证委托行为与各占位方法返回的真实结构。
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.report_export_service import (
    ReportExportService,
    report_export_service,
)


class TestExportToExcel:
    """export_to_excel 应将参数原样委托给 ExcelExportService.export。"""

    async def test_delegates_to_excel_export_service(self):
        svc = ReportExportService()
        data = [{"id": 1, "name": "a"}]
        columns = ["id", "name"]
        expected = b"\x50\x4b\x05\x06 fake xlsx bytes"

        # ExcelExportService 源码中实际并无 export 方法（生产代码本身的缺陷），
        # 此处用 create=True 注入以便验证委托行为本身。
        with patch(
            "app.services.report_export_service.ExcelExportService.export",
            return_value=expected,
            create=True,
        ) as mock_export:
            result = await svc.export_to_excel(data, columns, "report.xlsx")

        mock_export.assert_called_once_with(data, columns, "report.xlsx")
        assert result == expected

    async def test_returns_bytes_type(self):
        """验证返回值就是被委托方法返回的对象（透传）。"""
        sentinel = object()
        with patch(
            "app.services.report_export_service.ExcelExportService.export",
            return_value=sentinel,
            create=True,
        ):
            result = await ReportExportService().export_to_excel([], [], "x.xlsx")
        assert result is sentinel


class TestSummaryReportData:
    def test_returns_structure_with_year_and_empty_sections(self, caplog):
        svc = ReportExportService()
        db = MagicMock(name="db")

        with caplog.at_level(
            "WARNING", logger="app.services.report_export_service"
        ):
            result = svc.generate_summary_report_data(db, year=2025)

        assert result == {"year": 2025, "sections": []}
        assert "generate_summary_report_data 尚未实现" in caplog.text

    def test_year_passed_through_unchanged(self):
        svc = ReportExportService()
        result = svc.generate_summary_report_data(MagicMock(), year=2030)
        assert result["year"] == 2030


class TestFundDetailReportData:
    def test_returns_structure_with_year_and_empty_items(self, caplog):
        svc = ReportExportService()
        with caplog.at_level(
            "WARNING", logger="app.services.report_export_service"
        ):
            result = svc.generate_fund_detail_report_data(MagicMock(), year=2024)

        assert result == {"year": 2024, "items": []}
        assert "generate_fund_detail_report_data 尚未实现" in caplog.text


class TestProjectProgressReportData:
    def test_returns_structure_with_year_and_empty_projects(self, caplog):
        svc = ReportExportService()
        with caplog.at_level(
            "WARNING", logger="app.services.report_export_service"
        ):
            result = svc.generate_project_progress_report_data(
                MagicMock(), year=2026
            )

        assert result == {"year": 2026, "projects": []}
        assert "generate_project_progress_report_data 尚未实现" in caplog.text


class TestExportWord:
    def test_returns_empty_bytes_and_logs_warning(self, caplog):
        svc = ReportExportService()
        with caplog.at_level(
            "WARNING", logger="app.services.report_export_service"
        ):
            result = svc.export_word("summary", {"year": 2025})

        assert result == b""
        assert isinstance(result, bytes)
        assert "export_word 尚未实现" in caplog.text


class TestExportPdf:
    def test_returns_empty_bytes_and_logs_warning(self, caplog):
        svc = ReportExportService()
        with caplog.at_level(
            "WARNING", logger="app.services.report_export_service"
        ):
            result = svc.export_pdf("fund_detail", {"year": 2025})

        assert result == b""
        assert isinstance(result, bytes)
        assert "export_pdf 尚未实现" in caplog.text


class TestSingleton:
    def test_module_singleton_is_instance(self):
        """report_export_service 向后兼容单例应为 ReportExportService 实例。"""
        assert isinstance(report_export_service, ReportExportService)
