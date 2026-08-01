"""app.api.v1.import_export.export 覆盖补全 —
villages/schools 关键词过滤分支 (lines 86, 131)
与 report-word / report-pdf 的 village_summary / annual_summary / school_statistics 分支
(lines 372-375, 407, 411)."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mocks():
    db = MagicMock(name="db")
    q = MagicMock(name="query")
    q.filter.return_value = q
    q.limit.return_value = q
    q.all.return_value = []
    db.query.return_value = q

    user = MagicMock(name="user")
    user.id = 1
    user.role = "admin"
    user.is_superuser = True
    return db, q, user


@pytest.fixture
def client(mocks):
    from app.main import app
    from app.core.database import get_db
    from app.core.security import get_current_user

    db, _, user = mocks
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    tc = TestClient(app, raise_server_exceptions=False)
    yield tc
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def export_svc():
    with patch("app.api.v1.import_export.export.export_service") as m:
        m.export_village_list.return_value = b"village-xlsx"
        m.export_school_list.return_value = b"school-xlsx"
        yield m


@pytest.fixture
def report_svc():
    with patch("app.api.v1.import_export.export.report_export_service") as m:
        m.generate_school_statistics_report_data.return_value = {"year": 2025}
        m.generate_village_summary_report_data.return_value = {"year": 2025}
        m.generate_annual_summary_report_data.return_value = {"year": 2025}
        m.export_word.return_value = b"docx-bytes"
        m.export_pdf.return_value = b"pdf-bytes"
        yield m


class TestExportVillagesSchools:
    def test_villages_with_keyword(self, client, export_svc, mocks):
        _, q, _ = mocks
        resp = client.get("/api/v1/export/villages", params={"keyword": "幸福"})
        assert resp.status_code == 200
        assert resp.content == b"village-xlsx"
        q.filter.assert_called()  # keyword 过滤分支 (line 86)

    def test_schools_with_keyword(self, client, export_svc, mocks):
        _, q, _ = mocks
        resp = client.get("/api/v1/export/schools", params={"keyword": "希望"})
        assert resp.status_code == 200
        assert resp.content == b"school-xlsx"
        q.filter.assert_called()  # keyword 过滤分支 (line 131)


class TestExportReportWord:
    def test_village_summary_word(self, client, report_svc):
        resp = client.get("/api/v1/export/report-word", params={"report_type": "village_summary"})
        assert resp.status_code == 200
        assert resp.content == b"docx-bytes"
        report_svc.generate_village_summary_report_data.assert_called_once()

    def test_annual_summary_word_else_branch(self, client, report_svc):
        resp = client.get("/api/v1/export/report-word", params={"report_type": "annual_summary"})
        assert resp.status_code == 200
        assert resp.content == b"docx-bytes"
        report_svc.generate_annual_summary_report_data.assert_called_once()


class TestExportReportPdf:
    def test_school_statistics_pdf(self, client, report_svc):
        resp = client.get("/api/v1/export/report-pdf", params={"report_type": "school_statistics"})
        assert resp.status_code == 200
        assert resp.content == b"pdf-bytes"
        report_svc.generate_school_statistics_report_data.assert_called_once()

    def test_annual_summary_pdf_else_branch(self, client, report_svc):
        resp = client.get("/api/v1/export/report-pdf", params={"report_type": "annual_summary"})
        assert resp.status_code == 200
        assert resp.content == b"pdf-bytes"
        report_svc.generate_annual_summary_report_data.assert_called_once()
