"""覆盖率攻坚: app/services/docx_service.py 缺口行 227（DocxService.generate_report 代理）."""
from unittest.mock import MagicMock


class TestDocxServiceCompatWrapper:
    def test_generate_report_delegates_to_executive_report(self):
        """DocxService.generate_report 代理到 DocxReportService.generate_executive_report（第 227 行）."""
        from app.services.docx_service import DocxService

        svc = DocxService()
        svc._service = MagicMock()
        svc._service.generate_executive_report.return_value = b"docx-bytes"

        result = svc.generate_report({"year": 2025}, lang="zh")

        assert result == b"docx-bytes"
        svc._service.generate_executive_report.assert_called_once_with({"year": 2025}, lang="zh")

    def test_create_static_returns_wrapper(self):
        """DocxService.create 返回包装器实例."""
        from app.services.docx_service import DocxService

        svc = DocxService.create()
        assert isinstance(svc, DocxService)
        assert svc.db is None
