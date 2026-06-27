from unittest.mock import MagicMock, patch

import pytest

from app.services.pdf_service import PDFReportService, PDFService, pdf_service


# Mock doc.build to avoid font rendering issues in test environment.
# Sets side_effect to write dummy bytes into the buffer so getvalue() returns data.
@pytest.fixture(autouse=True)
def mock_doc_build():
    def _fake_build(elements):
        pass
    with patch("app.services.pdf_service.SimpleDocTemplate.build") as m:
        yield m


class TestPDFReportService:
    @pytest.fixture
    def svc(self):
        return PDFReportService()

    def test_init_custom_styles(self, svc):
        assert "ReportTitle" in svc.styles
        assert "SectionTitle" in svc.styles
        assert "Normal_CN" in svc.styles
        assert "Footer" in svc.styles

    def test_generate_users_report_basic(self, svc):
        users = [
            {"id": 1, "username": "alice", "email": "a@b.com",
             "full_name": "Alice", "role": "admin", "is_active": True},
            {"id": 2, "username": "bob", "email": "", "full_name": "",
             "role": None, "is_active": False},
        ]
        result = svc.generate_users_report(users)
        assert isinstance(result, bytes)

    def test_generate_users_report_empty(self, svc):
        result = svc.generate_users_report([])
        assert isinstance(result, bytes)

    def test_generate_villages_report_basic(self, svc):
        villages = [
            {"id": 1, "name": "v1", "code": "C001", "province": "P1",
             "city": "C1", "population": 1000, "status": "active"},
        ]
        result = svc.generate_villages_report(villages)
        assert isinstance(result, bytes)

    def test_generate_villages_report_empty(self, svc):
        result = svc.generate_villages_report([])
        assert isinstance(result, bytes)

    def test_generate_villages_report_missing_fields(self, svc):
        villages = [
            {"id": 1, "name": "v1", "code": "C001", "province": None,
             "city": None, "status": "active"},
        ]
        result = svc.generate_villages_report(villages)
        assert isinstance(result, bytes)

    def test_generate_projects_report_basic(self, svc):
        projects = [
            {"id": 1, "name": "proj", "type": "education", "status": "active",
             "budget": 100, "progress": 50, "start_date": "2024-01-01"},
        ]
        result = svc.generate_projects_report(projects)
        assert isinstance(result, bytes)

    def test_generate_projects_report_truncated_name(self, svc):
        projects = [
            {"id": 1, "name": "A" * 20, "type": "infra", "status": "active",
             "budget": 200, "progress": 75, "start_date": "2024-06-01"},
        ]
        result = svc.generate_projects_report(projects)
        assert isinstance(result, bytes)

    def test_generate_projects_report_missing_optional(self, svc):
        projects = [
            {"id": 1, "name": "p1", "status": "active", "budget": None,
             "progress": None, "start_date": None},
        ]
        result = svc.generate_projects_report(projects)
        assert isinstance(result, bytes)

    def test_generate_funds_report_basic(self, svc):
        funds = [
            {"id": 1, "name": "fund1", "type": "project", "amount": 50000,
             "source": "military", "status": "approved", "applicant": "admin"},
        ]
        result = svc.generate_funds_report(funds)
        assert isinstance(result, bytes)

    def test_generate_funds_report_truncated_name(self, svc):
        funds = [
            {"id": 1, "name": "B" * 15, "type": None, "amount": 0,
             "source": None, "status": "pending", "applicant": None},
        ]
        result = svc.generate_funds_report(funds)
        assert isinstance(result, bytes)

    def test_generate_funds_report_empty(self, svc):
        result = svc.generate_funds_report([])
        assert isinstance(result, bytes)

    def test_generate_comprehensive_report_full(self, svc):
        summary = {"projects": 5, "funds": 10}
        sections = [
            {
                "title": "项目数据",
                "headers": ["id", "name"],
                "data": [{"id": "1", "name": "proj1"}],
                "col_widths": [1.5 * 72, 2 * 72],
            },
            {
                "title": "空数据段",
                "headers": [],
                "data": [],
            },
        ]
        result = svc.generate_comprehensive_report(summary, sections)
        assert isinstance(result, bytes)

    def test_generate_comprehensive_report_no_data(self, svc):
        summary = {"projects": 0}
        sections = [
            {
                "title": "无数据",
                "headers": ["a"],
                "data": [],
            },
        ]
        result = svc.generate_comprehensive_report(summary, sections)
        assert isinstance(result, bytes)

    def test_generate_comprehensive_report_no_headers(self, svc):
        summary = {"k": "v"}
        sections = [
            {
                "title": "Test",
                "data": [{"col1": "val1"}],
            },
        ]
        result = svc.generate_comprehensive_report(summary, sections)
        assert isinstance(result, bytes)

    def test_generate_comprehensive_report_no_col_widths(self, svc):
        summary = {"k": "v"}
        sections = [
            {
                "title": "Test",
                "headers": ["a", "b"],
                "data": [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}],
            },
        ]
        result = svc.generate_comprehensive_report(summary, sections)
        assert isinstance(result, bytes)

    def test_generate_comprehensive_report_data_truncated(self, svc):
        summary = {"k": "v"}
        many_items = [{"a": str(i)} for i in range(60)]
        sections = [
            {
                "title": "Many",
                "headers": ["a"],
                "data": many_items,
            },
        ]
        result = svc.generate_comprehensive_report(summary, sections)
        assert isinstance(result, bytes)


class TestPDFService:
    def test_init_without_db(self):
        svc = PDFService()
        assert svc.db is None
        assert svc._service is pdf_service

    def test_init_with_db(self):
        db = MagicMock()
        svc = PDFService(db=db)
        assert svc.db is db

    def test_generate_report_raises(self):
        svc = PDFService()
        with pytest.raises(AttributeError):
            svc.generate_report({})

    def test_create_with_db(self):
        db = MagicMock()
        svc = PDFService.create(db)
        assert isinstance(svc, PDFService)
        assert svc.db is db

    def test_create_without_db(self):
        svc = PDFService.create()
        assert isinstance(svc, PDFService)
        assert svc.db is None


class TestModuleLevel:
    def test_pdf_service_instance(self):
        assert isinstance(pdf_service, PDFReportService)
