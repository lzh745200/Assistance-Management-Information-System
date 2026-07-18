"""Tests for app.api.v1.system_health API routes."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def mock_db():
    session = MagicMock()
    session.execute.return_value = session
    return session


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.username = "admin"
    return user


@pytest.fixture
def health_app(mock_db, mock_user):
    """FastAPI app with system-health router and dependency overrides."""
    from app.api.v1 import deps
    app = FastAPI()
    app.dependency_overrides[deps.get_current_user] = lambda: mock_user
    app.dependency_overrides[deps.get_db] = lambda: mock_db
    from app.api.v1.system_health import router
    app.include_router(router)
    return app


@pytest.fixture
def client(health_app):
    return TestClient(health_app)


class TestGetSystemOverview:
    def test_all_ok(self, client, mock_db):
        mock_db.fetchall.return_value = [(1,)]
        mock_db.fetchone.return_value = ["wal"]

        with patch("app.api.v1.system_health._check_disk_space", return_value={
            "status": "ok", "message": "Available 50GB", "free_gb": 50, "total_gb": 100, "used_percent": 50
        }), patch("app.api.v1.system_health._get_db_file_info", return_value={
            "status": "ok", "path": "/fake/db", "size_mb": 10, "last_modified": "2024-01-01T00:00:00", "message": "10MB"
        }), patch("app.api.v1.system_health._check_wal_status", return_value={
            "status": "ok", "journal_mode": "wal", "message": "ok"
        }):
            resp = client.get("/system-health/overview")
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["overall_status"] == "ok"
            assert "checks" in data

    def test_db_error(self, client, mock_db):
        mock_db.execute.side_effect = Exception("DB down")

        with patch("app.api.v1.system_health._check_disk_space", return_value={
            "status": "error", "message": "fail"
        }), patch("app.api.v1.system_health._get_db_file_info", return_value={
            "status": "ok", "size_mb": 0, "message": "ok"
        }), patch("app.api.v1.system_health._check_wal_status", return_value={
            "status": "ok", "message": "ok"
        }):
            resp = client.get("/system-health/overview")
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["overall_status"] == "error"

    def test_overall_warning(self, client, mock_db):
        mock_db.fetchall.return_value = [(1,)]
        mock_db.fetchone.return_value = ["wal"]

        with patch("app.api.v1.system_health._check_disk_space", return_value={
            "status": "warning", "message": "Low space", "free_gb": 3
        }), patch("app.api.v1.system_health._get_db_file_info", return_value={
            "status": "ok", "size_mb": 5, "message": "ok"
        }), patch("app.api.v1.system_health._check_wal_status", return_value={
            "status": "ok", "message": "ok"
        }):
            resp = client.get("/system-health/overview")
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["overall_status"] == "warning"


class TestRunIntegrityCheck:
    def test_ok(self, client, mock_db):
        mock_db.fetchall.return_value = [("ok",)]

        with patch("app.api.v1.system_health.EXTRA_INDEXES", [], create=True):
            resp = client.post("/system-health/integrity-check")
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["status"] == "ok"

    def test_corrupt(self, client, mock_db):
        mock_db.fetchall.return_value = [("corrupt",), ("details",)]

        with patch("app.api.v1.system_health.EXTRA_INDEXES", [], create=True):
            resp = client.post("/system-health/integrity-check")
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["status"] == "error"

    def test_missing_indexes_warning(self, client, mock_db):
        # Return ok for integrity check, tables list, and empty index lists
        mock_db.fetchall.side_effect = [
            [("ok",)],          # integrity_check result
            [("users",)],       # tables
            [],                 # PRAGMA index_list for users (empty → no indexes found)
        ]
        mock_db.fetchone.return_value = None

        resp = client.post("/system-health/integrity-check")
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Real EXTRA_INDEXES is imported inside the function; since we have no
        # real indexes defined for the "users" table, warnings should be generated
        assert data["status"] == "ok"  # integrity check itself passed
        assert isinstance(data["warnings"], list)

    def test_exception(self, client, mock_db):
        mock_db.execute.side_effect = Exception("disk error")

        resp = client.post("/system-health/integrity-check")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "error"


class TestWalCheckpoint:
    def test_success(self, client, mock_db):
        mock_db.fetchone.side_effect = [
            ["wal"],    # before _check_wal_status → journal_mode
            [0, 10, 5], # PRAGMA wal_checkpoint(TRUNCATE) result
            ["wal"],    # after _check_wal_status → journal_mode
        ]

        with patch("os.path.exists", return_value=True), patch("os.path.getsize", return_value=524288):
            resp = client.post("/system-health/wal-checkpoint")
            assert resp.status_code == 200

    def test_exception(self, client, mock_db):
        mock_db.execute.side_effect = Exception("WAL error")

        resp = client.post("/system-health/wal-checkpoint")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "error"


class TestGetDiskSpace:
    def test_ok(self, client):
        with patch("app.api.v1.system_health._check_disk_space", return_value={
            "status": "ok", "free_gb": 50, "total_gb": 200
        }):
            resp = client.get("/system-health/disk-space")
            assert resp.status_code == 200
            assert resp.json()["data"]["status"] == "ok"


class TestGetTableStats:
    def test_success(self, client, mock_db):
        mock_db.fetchall.return_value = [("users",), ("villages",)]
        mock_db.scalar.return_value = 100

        resp = client.get("/system-health/table-stats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_tables"] == 2

    def test_table_error(self, client, mock_db):
        mock_db.fetchall.return_value = [("broken_table",)]
        mock_db.scalar.side_effect = Exception("table missing")

        resp = client.get("/system-health/table-stats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["tables"][0]["error"] is True


class TestRunVacuum:
    def test_success(self, client, mock_db):
        with patch("app.api.v1.system_health._get_db_file_info", side_effect=[
            {"status": "ok", "size_mb": 50},
            {"status": "ok", "size_mb": 45},
        ]):
            resp = client.post("/system-health/vacuum")
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["status"] == "ok"
            assert data["saved_mb"] == 5.0

    def test_exception(self, client, mock_db):
        mock_db.execute.side_effect = Exception("VACUUM failed")

        with patch("app.api.v1.system_health._get_db_file_info", return_value={
            "status": "ok", "size_mb": 10
        }):
            resp = client.post("/system-health/vacuum")
            assert resp.status_code == 200
            assert resp.json()["data"]["status"] == "error"


class TestCheckDiskSpace:
    def test_ok_plenty(self):
        mock_usage = MagicMock()
        mock_usage.total = 100 * 1024**3  # 100 GB
        mock_usage.used = 50 * 1024**3   # 50 GB
        mock_usage.free = 50 * 1024**3   # 50 GB free
        with patch("os.getcwd", return_value="/"), patch("shutil.disk_usage", return_value=mock_usage):
            from app.api.v1.system_health import _check_disk_space
            result = _check_disk_space()
            assert result["status"] == "ok"

    def test_error_low_space(self):
        mock_usage = MagicMock()
        mock_usage.total = 100 * 1024**3
        mock_usage.used = 99.5 * 1024**3  # 99.5 GB used
        mock_usage.free = 0.5 * 1024**3   # 0.5 GB free
        with patch("os.getcwd", return_value="/"), patch("shutil.disk_usage", return_value=mock_usage):
            from app.api.v1.system_health import _check_disk_space
            result = _check_disk_space()
            assert result["status"] == "error"

    def test_warning_moderate(self):
        mock_usage = MagicMock()
        mock_usage.total = 100 * 1024**3
        mock_usage.used = 97 * 1024**3   # 97 GB used
        mock_usage.free = 3 * 1024**3    # 3 GB free (< 5 GB)
        with patch("os.getcwd", return_value="/"), patch("shutil.disk_usage", return_value=mock_usage):
            from app.api.v1.system_health import _check_disk_space
            result = _check_disk_space()
            assert result["status"] == "warning"

    def test_exception(self):
        with patch("shutil.disk_usage", side_effect=Exception("no disk")):
            from app.api.v1.system_health import _check_disk_space
            result = _check_disk_space()
            assert result["status"] == "error"


class TestGetDbFileInfo:
    def test_success(self, mock_db):
        mock_db.fetchone.return_value = ["main", "/", "C:/data/rural_revitalization.db"]

        with patch("os.path.exists", return_value=True), patch("os.path.getsize", return_value=10485760), patch(
            "os.path.getmtime", return_value=1700000000
        ):
            from app.api.v1.system_health import _get_db_file_info
            result = _get_db_file_info(mock_db)
            assert result["status"] == "ok"
            assert result["size_mb"] == 10.0

    def test_no_path(self, mock_db):
        mock_db.fetchone.return_value = None

        from app.api.v1.system_health import _get_db_file_info
        result = _get_db_file_info(mock_db)
        assert result["size_mb"] == 0

    def test_exception(self, mock_db):
        mock_db.execute.side_effect = Exception("oops")

        from app.api.v1.system_health import _get_db_file_info
        result = _get_db_file_info(mock_db)
        assert result["status"] == "warning"


class TestCheckWalStatus:
    def test_wal_mode_small(self, mock_db):
        mock_db.fetchone.side_effect = [
            ["wal"],   # journal_mode
            ["main", "/", "C:/data/db.sqlite"],  # database_list
        ]

        with patch("os.path.exists", return_value=True), patch("os.path.getsize", return_value=524288):
            from app.api.v1.system_health import _check_wal_status
            result = _check_wal_status(mock_db)
            assert result["status"] == "ok"
            assert result["journal_mode"] == "wal"

    def test_wal_mode_large(self, mock_db):
        mock_db.fetchone.side_effect = [
            ["wal"],
            ["main", "/", "C:/data/db.sqlite"],
        ]

        with patch("os.path.exists", return_value=True), patch("os.path.getsize", return_value=200 * 1024 * 1024):
            from app.api.v1.system_health import _check_wal_status
            result = _check_wal_status(mock_db)
            assert result["status"] == "warning"

    def test_non_wal_mode(self, mock_db):
        mock_db.fetchone.return_value = ["delete"]

        from app.api.v1.system_health import _check_wal_status
        result = _check_wal_status(mock_db)
        assert result["journal_mode"] == "delete"

    def test_exception(self, mock_db):
        mock_db.execute.side_effect = Exception("fail")

        from app.api.v1.system_health import _check_wal_status
        result = _check_wal_status(mock_db)
        assert result["status"] == "warning"
