"""Tests for app.api.v1.data.data.data_packages — key endpoints."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def mock_db():
    s = MagicMock()
    s.query.return_value = s
    s.filter.return_value = s
    s.all.return_value = []
    s.first.return_value = None
    return s


@pytest.fixture
def client(mock_db):
    from app.api.v1 import deps
    app = FastAPI()
    user = MagicMock()
    user.id = 1; user.is_superuser = True; user.role = "admin"
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_db] = lambda: mock_db
    with patch("app.api.v1.data.data.data_packages.DataPackageService", return_value=MagicMock()), \
         patch("app.api.v1.data.data.data_packages.ImportExportHistoryService", return_value=MagicMock()), \
         patch("app.api.v1.data.data.data_packages.OrganizationPermissionService", return_value=MagicMock()):
        from app.api.v1.data.data.data_packages import router
        app.include_router(router)
    return TestClient(app)


class TestListPackages:
    def test_empty(self, client, mock_db):
        mock_db.all.return_value = []
        resp = client.get("/data-packages")
        assert resp.status_code == 200

    def test_with_filters(self, client, mock_db):
        mock_db.all.return_value = []
        resp = client.get("/data-packages?status=completed&type=export&org_id=1")
        assert resp.status_code == 200


class TestPreviewExport:
    def test_preview(self, client):
        resp = client.post("/data-packages/preview", json={"modules": ["villages"]})
        assert resp.status_code == 200

    def test_preview_empty_modules(self, client):
        resp = client.post("/data-packages/preview", json={"modules": []})
        assert resp.status_code in (200, 400)


class TestPreviewPackage:
    def test_preview(self, client, mock_db):
        mock_db.first.return_value = MagicMock()
        resp = client.get("/data-packages/1/preview")
        assert resp.status_code == 200


class TestGetPackage:
    def test_not_found(self, client, mock_db):
        mock_db.first.return_value = None
        resp = client.get("/data-packages/999")
        assert resp.status_code == 404


class TestDeletePackage:
    def test_not_found(self, client, mock_db):
        mock_db.first.return_value = None
        resp = client.delete("/data-packages/999")
        assert resp.status_code == 404


class TestPackageHistory:
    def test_empty(self, client, mock_db):
        resp = client.get("/data-packages/1/history")
        assert resp.status_code == 200


class TestValidatePackage:
    def test_not_found(self, client, mock_db):
        mock_db.first.return_value = None
        resp = client.post("/data-packages/999/validate")
        assert resp.status_code == 404
