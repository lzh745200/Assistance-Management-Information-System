"""Tests for app.api.v1.rural_works — patching service layer."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from fastapi import FastAPI
    from app.api.v1 import deps

    app = FastAPI()
    user = MagicMock()
    user.id = 1; user.username = "admin"; user.is_superuser = True
    mock_db = MagicMock()

    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_db] = lambda: mock_db

    from app.api.v1.rural_works import router
    app.include_router(router)
    return TestClient(app)


class TestListRuralWorks:
    def test_default_params(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.get_rural_works.return_value = ([], 0)
            mock_svc.return_value = inst
            resp = client.get("/api/v1/rural-works")
            assert resp.status_code == 200

    def test_with_filters(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.get_rural_works.return_value = ([], 0)
            mock_svc.return_value = inst
            resp = client.get("/api/v1/rural-works?year=2025&status=active&search=test")
            assert resp.status_code == 200


class TestGetStatistics:
    def test_returns_stats(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.get_statistics.return_value = MagicMock(model_dump=lambda: {"total": 10})
            mock_svc.return_value = inst
            resp = client.get("/api/v1/rural-works/statistics/summary")
            assert resp.status_code == 200


class TestVillagesForSelect:
    def test_returns_list(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.get_villages_for_select.return_value = []
            mock_svc.return_value = inst
            resp = client.get("/api/v1/rural-works/villages")
            assert resp.status_code == 200


class TestGenerateReport:
    def test_no_params(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.generate_work_report.return_value = {}
            mock_svc.return_value = inst
            resp = client.get("/api/v1/rural-works/report/generate")
            assert resp.status_code == 200


class TestAvailableYears:
    def test_returns_years(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.get_available_years.return_value = [2024, 2025]
            mock_svc.return_value = inst
            resp = client.get("/api/v1/rural-works/years")
            assert resp.status_code == 200


class TestGetRuralWork:
    def test_found(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.get_rural_work_by_id.return_value = MagicMock(model_dump=lambda: {"id": 1, "title": "test"})
            mock_svc.return_value = inst
            resp = client.get("/api/v1/rural-works/1")
            assert resp.status_code == 200

    def test_not_found(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.get_rural_work_by_id.return_value = None
            mock_svc.return_value = inst
            resp = client.get("/api/v1/rural-works/999")
            assert resp.status_code == 404


class TestCreateRuralWork:
    def test_create(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.create_rural_work.return_value = MagicMock(model_dump=lambda: {"id": 1})
            mock_svc.return_value = inst
            resp = client.post("/api/v1/rural-works", json={"title": "新工作"})
            assert resp.status_code == 200


class TestUpdateRuralWork:
    def test_update(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.update_rural_work.return_value = MagicMock(model_dump=lambda: {"id": 1})
            mock_svc.return_value = inst
            resp = client.put("/api/v1/rural-works/1", json={"title": "更新"})
            assert resp.status_code == 200

    def test_not_found(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.update_rural_work.return_value = None
            mock_svc.return_value = inst
            resp = client.put("/api/v1/rural-works/999", json={"title": "更新"})
            assert resp.status_code == 404


class TestDeleteRuralWork:
    def test_delete(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.delete_rural_work.return_value = True
            mock_svc.return_value = inst
            resp = client.delete("/api/v1/rural-works/1")
            assert resp.status_code == 200

    def test_not_found(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc:
            inst = MagicMock()
            inst.delete_rural_work.return_value = False
            mock_svc.return_value = inst
            resp = client.delete("/api/v1/rural-works/999")
            assert resp.status_code == 404


class TestBatchDelete:
    def test_batch_delete(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc, \
             patch("app.api.v1.rural_works.get_work_log_recorder", return_value=MagicMock()):
            inst = MagicMock()
            inst.batch_delete.return_value = 3
            mock_svc.return_value = inst
            resp = client.post("/api/v1/rural-works/batch-delete", json=[1, 2, 3])
            assert resp.status_code == 200

    def test_batch_delete_logger_fallback(self, client):
        with patch("app.api.v1.rural_works.RuralWorkService") as mock_svc, \
             patch("app.api.v1.rural_works.get_work_log_recorder", side_effect=Exception("no logger")):
            inst = MagicMock()
            inst.batch_delete.return_value = 1
            mock_svc.return_value = inst
            resp = client.post("/api/v1/rural-works/batch-delete", json=[1])
            assert resp.status_code == 200


class TestParseQueryDate:
    def test_none(self):
        from app.api.v1.rural_works import _parse_query_date
        assert _parse_query_date(None) is None

    def test_empty(self):
        from app.api.v1.rural_works import _parse_query_date
        assert _parse_query_date("") is None

    def test_valid_iso(self):
        from app.api.v1.rural_works import _parse_query_date
        result = _parse_query_date("2025-06-15T10:30:00")
        assert isinstance(result, datetime)

    def test_valid_date_only(self):
        from app.api.v1.rural_works import _parse_query_date
        result = _parse_query_date("2025-06-15")
        assert isinstance(result, datetime)

    def test_invalid(self):
        from app.api.v1.rural_works import _parse_query_date
        assert _parse_query_date("not-a-date") is None
