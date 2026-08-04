from app.api.v1.data.data.data_packages import (
    get_package_service, get_history_service, get_permission_service,
)
"""增量数据包端点测试(detect-changes/export/import)"""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient


def _user():
    return SimpleNamespace(id=1, username="admin", role="admin", is_superuser=True, org_id=1)


def _setup(app, mock_db, mock_svc):
    from app.core.database import get_db
    from app.core.security import get_current_user

    mock_svc.db = mock_db
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: _user()
    app.dependency_overrides[get_package_service] = lambda: mock_svc
    app.dependency_overrides[get_history_service] = lambda: MagicMock(log_export=AsyncMock())
    app.dependency_overrides[get_permission_service] = lambda: MagicMock(
        can_access_organization=MagicMock(return_value=True),
    )


def test_detect_changes():
    from app.main import app
    mock_db = MagicMock()
    mock_svc = MagicMock()
    # get_package 返回基准包
    base_pkg = SimpleNamespace(created_at=datetime(2026, 7, 1, tzinfo=timezone.utc))
    mock_svc.get_package.return_value = base_pkg
    # count 查询返回 3
    mock_db.query.return_value.filter.return_value.scalar.return_value = 3

    _setup(app, mock_db, mock_svc)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.post(
            "/api/v1/data-packages/incremental/detect-changes",
            json={"data_types": ["villages"], "base_package_id": 5},
            headers={"X-Internal-Backup": "k"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["base_package_id"] == 5
        assert "summary" in data
    finally:
        app.dependency_overrides.clear()


def test_detect_changes_base_missing():
    from app.main import app

    mock_db = MagicMock()
    mock_svc = MagicMock()
    mock_svc.get_package.return_value = None

    _setup(app, mock_db, mock_svc)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.post(
            "/api/v1/data-packages/incremental/detect-changes",
            json={"data_types": ["villages"], "base_package_id": 999},
            headers={"X-Internal-Backup": "k"},
        )
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_incremental_export():
    from app.main import app

    mock_db = MagicMock()
    mock_svc = MagicMock()
    base_pkg = SimpleNamespace(created_at=datetime(2026, 7, 1, tzinfo=timezone.utc))
    mock_svc.get_package.return_value = base_pkg
    mock_svc.export_package = AsyncMock(return_value=SimpleNamespace(
        package_id=9, file_name="INC1.zip", record_counts={"villages": 2},
        total_records=2,
    ))

    _setup(app, mock_db, mock_svc)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.post(
            "/api/v1/data-packages/incremental/export",
            json={"data_types": ["villages"], "base_package_id": 5, "description": "增量"},
            headers={"X-Internal-Backup": "k"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["package_id"] == 9
        assert "download_url" in data
        # 校验 since_time 透传
        _, kwargs = mock_svc.export_package.call_args
        assert kwargs["incremental"] is True
        assert kwargs["since_time"] is not None
    finally:
        app.dependency_overrides.clear()


def test_incremental_import():
    from app.main import app

    mock_db = MagicMock()
    mock_svc = MagicMock()
    pkg = SimpleNamespace(id=7, file_path="/tmp/pkg.zip", file_name="pkg.zip", org_id=1)
    mock_svc.get_package.return_value = pkg
    mock_svc.import_package = AsyncMock(return_value=SimpleNamespace(
        is_valid=True, imported_count=4, message="ok",
    ))

    _setup(app, mock_db, mock_svc)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.post(
            "/api/v1/data-packages/incremental/import",
            json={"package_id": 7, "apply_changes": True},
            headers={"X-Internal-Backup": "k"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["imported"] == 4
        assert data["applied"] is True
        mock_svc.import_package.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_incremental_import_missing():
    from app.main import app

    mock_db = MagicMock()
    mock_svc = MagicMock()
    mock_svc.get_package.return_value = None

    _setup(app, mock_db, mock_svc)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.post(
            "/api/v1/data-packages/incremental/import",
            json={"package_id": 999, "apply_changes": False},
            headers={"X-Internal-Backup": "k"},
        )
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
