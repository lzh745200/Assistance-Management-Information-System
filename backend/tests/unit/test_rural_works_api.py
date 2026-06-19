"""Tests for app.api.v1.rural_works — all 10 endpoints."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def mock_service():
    svc = MagicMock()
    svc.get_rural_works.return_value = ([], 0)
    svc.get_statistics.return_value = MagicMock(model_dump=lambda: {})
    svc.get_villages_for_select.return_value = []
    svc.generate_work_report.return_value = {}
    svc.get_available_years.return_value = [2024, 2025]
    svc.get_rural_work_by_id.return_value = MagicMock(model_dump=lambda: {"id": 1})
    svc.create_rural_work.return_value = MagicMock(model_dump=lambda: {"id": 1})
    svc.update_rural_work.return_value = MagicMock(model_dump=lambda: {"id": 1})
    svc.delete_rural_work.return_value = True
    svc.batch_delete.return_value = 3
    return svc


@pytest.fixture
def client(mock_service):
    from app.api.v1 import deps
    app = FastAPI()
    user = MagicMock()
    user.id = 1
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_db] = lambda: MagicMock()
    # Patch service construction
    with patch("app.api.v1.rural_works.RuralWorkService", return_value=mock_service):
        from app.api.v1.rural_works import router
        app.include_router(router)
    return TestClient(app)


class TestListRuralWorks:
    def test_default_params(self, client):
        resp = client.get("/rural-works")
        assert resp.status_code == 200

    def test_with_filters(self, client):
        resp = client.get("/rural-works?skip=10&limit=20&status=active&year=2025&search=test&order_by=name&order_desc=false")
        assert resp.status_code == 200


class TestGetStatistics:
    def test_returns_stats(self, client):
        resp = client.get("/rural-works/statistics/summary")
        assert resp.status_code == 200


class TestGetVillagesForSelect:
    def test_returns_list(self, client):
        resp = client.get("/rural-works/villages")
        assert resp.status_code == 200


class TestGenerateReport:
    def test_no_params(self, client):
        resp = client.get("/rural-works/report/generate")
        assert resp.status_code == 200

    def test_with_date_params(self, client):
        resp = client.get("/rural-works/report/generate?year=2025&start_date=2025-01-01&end_date=2025-12-31")
        assert resp.status_code == 200


class TestGetAvailableYears:
    def test_returns_years(self, client):
        resp = client.get("/rural-works/years")
        assert resp.status_code == 200


class TestGetRuralWork:
    def test_found(self, client):
        resp = client.get("/rural-works/1")
        assert resp.status_code == 200

    def test_not_found(self, client, mock_service):
        mock_service.get_rural_work_by_id.return_value = None
        resp = client.get("/rural-works/999")
        assert resp.status_code == 404


class TestCreateRuralWork:
    def test_create(self, client):
        resp = client.post("/rural-works", json={"title": "新工作", "description": "描述"})
        assert resp.status_code == 200


class TestUpdateRuralWork:
    def test_update(self, client):
        resp = client.put("/rural-works/1", json={"title": "更新"})
        assert resp.status_code == 200

    def test_not_found(self, client, mock_service):
        mock_service.update_rural_work.return_value = None
        resp = client.put("/rural-works/999", json={"title": "更新"})
        assert resp.status_code == 404


class TestDeleteRuralWork:
    def test_delete(self, client):
        resp = client.delete("/rural-works/1")
        assert resp.status_code == 200

    def test_not_found(self, client, mock_service):
        mock_service.delete_rural_work.return_value = False
        resp = client.delete("/rural-works/999")
        assert resp.status_code == 404


class TestBatchDelete:
    def test_batch_delete(self, client):
        resp = client.post("/rural-works/batch-delete", json=[1, 2, 3])
        assert resp.status_code == 200

    def test_batch_delete_with_logger_failure(self, client):
        with patch("app.api.v1.rural_works.get_work_log_recorder", side_effect=Exception("no logger")):
            resp = client.post("/rural-works/batch-delete", json=[1])
            assert resp.status_code == 200


class TestParseQueryDate:
    def test_none(self):
        from app.api.v1.rural_works import _parse_query_date
        assert _parse_query_date(None) is None

    def test_empty(self):
        from app.api.v1.rural_works import _parse_query_date
        assert _parse_query_date("") is None
        assert _parse_query_date("   ") is None

    def test_valid_iso(self):
        from app.api.v1.rural_works import _parse_query_date
        result = _parse_query_date("2025-06-15T10:30:00")
        assert isinstance(result, datetime)
        assert result.year == 2025

    def test_valid_date_only(self):
        from app.api.v1.rural_works import _parse_query_date
        result = _parse_query_date("2025-06-15")
        assert isinstance(result, datetime)

    def test_valid_with_space(self):
        from app.api.v1.rural_works import _parse_query_date
        result = _parse_query_date("2025-06-15 10:30:00")
        assert isinstance(result, datetime)

    def test_invalid_returns_none(self):
        from app.api.v1.rural_works import _parse_query_date
        assert _parse_query_date("not-a-date") is None
