"""Tests for app.api.v1.data.data.data_packages."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    from app.core.database import get_db
    from app.core.security import get_current_user

    user = MagicMock()
    user.id = 1; user.is_superuser = True; user.role = "admin"
    mock_db = MagicMock()
    mock_db.query.return_value = mock_db
    mock_db.filter.return_value = mock_db
    mock_db.all.return_value = []
    mock_db.first.return_value = None

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db

    tc = TestClient(app, raise_server_exceptions=False)
    yield tc
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


class TestListPackages:
    def test_empty(self, client):
        resp = client.get("/api/v1/data-packages")
        assert resp.status_code == 200

    def test_with_filters(self, client):
        resp = client.get("/api/v1/data-packages?status=completed&type=export")
        assert resp.status_code == 200


class TestPreviewExport:
    @pytest.mark.skip(reason="DataPackageService complex dependencies")
    def test_preview(self, client):
        pass


class TestGetPackage:
    def test_not_found(self, client):
        resp = client.get("/api/v1/data-packages/99999")
        assert resp.status_code == 404


class TestPreviewPackage:
    def test_not_found(self, client):
        resp = client.get("/api/v1/data-packages/99999/preview")
        assert resp.status_code == 404


class TestDeletePackage:
    def test_not_found(self, client):
        resp = client.delete("/api/v1/data-packages/99999")
        assert resp.status_code == 404


class TestPackageHistory:
    @pytest.mark.skip(reason="ImportExportHistoryService complex dependencies")
    def test_empty(self, client):
        pass


class TestValidatePackage:
    def test_not_found(self, client):
        resp = client.post("/api/v1/data-packages/99999/validate")
        assert resp.status_code == 404


class TestDownloadPackage:
    def test_not_found(self, client):
        resp = client.get("/api/v1/data-packages/99999/download")
        assert resp.status_code == 404
