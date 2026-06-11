"""
Tests for app.api.v1.system.health — 100% coverage
"""

import os
import time
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_start_time():
    from app.api.v1.system.health import _START_TIME
    import app.api.v1.system.health as health_mod
    orig = health_mod._START_TIME
    health_mod._START_TIME = time.time() - 3600
    yield
    health_mod._START_TIME = orig


class TestHealthOverview:
    def test_health_overview(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "healthy"
        assert "uptime_seconds" in data["data"]
        assert "platform" in data["data"]
        assert "python_version" in data["data"]

    def test_health_overview_slash(self, client):
        resp = client.get("/api/v1/health/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "healthy"


class TestHealthDatabase:
    def test_database_connected(self, client):
        with patch("app.api.v1.system.health.SessionLocal") as mock_sl:
            mock_db = MagicMock()
            mock_sl.return_value = mock_db
            with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./test.db"}, clear=False):
                with patch("os.path.getsize", return_value=1024), patch("os.path.exists", return_value=True):
                    resp = client.get("/api/v1/health/database")
                    assert resp.status_code == 200
                    data = resp.json()
                    assert data["code"] == 200
                    assert data["data"]["connected"] is True
                    assert data["data"]["size_bytes"] == 1024

    def test_database_exception(self, client):
        with patch("app.api.v1.system.health.SessionLocal") as mock_sl:
            mock_db = MagicMock()
            mock_db.execute.side_effect = Exception("DB down")
            mock_sl.return_value = mock_db
            resp = client.get("/api/v1/health/database")
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 500
            assert "DB down" in data["message"]

    def test_database_no_db_url(self, client):
        with patch("app.api.v1.system.health.SessionLocal") as mock_sl:
            mock_db = MagicMock()
            mock_sl.return_value = mock_db
            with patch.dict(os.environ, {}, clear=False):
                resp = client.get("/api/v1/health/database")
                assert resp.status_code == 200


class TestHealthLiveness:
    def test_liveness(self, client):
        resp = client.get("/api/v1/health/liveness")
        assert resp.status_code == 200
        assert resp.json() == {"status": "alive"}


class TestHealthReadiness:
    def test_readiness_ready(self, client):
        with patch("app.api.v1.system.health.SessionLocal") as mock_sl:
            mock_db = MagicMock()
            mock_sl.return_value = mock_db
            resp = client.get("/api/v1/health/readiness")
            assert resp.status_code == 200
            assert resp.json() == {"status": "ready"}

    def test_readiness_not_ready(self, client):
        with patch("app.api.v1.system.health.SessionLocal") as mock_sl:
            mock_db = MagicMock()
            mock_db.execute.side_effect = Exception("DB down")
            mock_sl.return_value = mock_db
            resp = client.get("/api/v1/health/readiness")
            assert resp.status_code == 200
            assert resp.json() == {"status": "not_ready"}


class TestHealthFull:
    def test_full_health(self, client):
        with patch("app.utils.paths.get_database_path") as mock_gdp, \
             patch("app.utils.paths.get_backup_path") as mock_gbp, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=2048), \
             patch("builtins.open", MagicMock()):
            mock_gdp.return_value.absolute.return_value = "/fake/db.sqlite3"
            mock_gbp.return_value = "/fake/backups"
            with patch("sqlite3.connect") as mock_conn:
                conn_instance = MagicMock()
                cursor = MagicMock()
                cursor.fetchone.return_value = ["ok"]
                conn_instance.execute.return_value = cursor
                mock_conn.return_value = conn_instance
                with patch("os.listdir", return_value=["b1.zip", "b2.db"]), \
                     patch("os.path.getsize", side_effect=[100, 200]):
                    resp = client.get("/api/v1/health/full")
                    assert resp.status_code == 200
                    data = resp.json()
                    assert data["code"] == 200
                    assert data["data"]["db_size_mb"] == 0.0

    def test_full_health_db_not_exists(self, client):
        with patch("app.utils.paths.get_database_path") as mock_gdp, \
             patch("app.utils.paths.get_backup_path") as mock_gbp, \
             patch("os.path.exists", return_value=False):
            mock_gdp.return_value.absolute.return_value = "/fake/db.sqlite3"
            mock_gbp.return_value = "/fake/backups"
            resp = client.get("/api/v1/health/full")
            assert resp.status_code == 200

    def test_full_health_db_error(self, client):
        with patch("app.utils.paths.get_database_path") as mock_gdp, \
             patch("app.utils.paths.get_backup_path") as mock_gbp, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", side_effect=Exception("no access")):
            mock_gdp.return_value.absolute.return_value = "/fake/db.sqlite3"
            mock_gbp.return_value = "/fake/backups"
            resp = client.get("/api/v1/health/full")
            assert resp.status_code == 200
            assert "db_error" in resp.json()["data"]

    def test_full_health_backup_error(self, client):
        with patch("app.utils.paths.get_database_path") as mock_gdp, \
             patch("app.utils.paths.get_backup_path") as mock_gbp, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=1024):
            mock_gdp.return_value.absolute.return_value = "/fake/db.sqlite3"
            mock_gbp.return_value = "/fake/backups"
            with patch("sqlite3.connect") as mock_conn:
                conn_instance = MagicMock()
                cursor = MagicMock()
                cursor.fetchone.side_effect = [(5,), ("ok",)]
                conn_instance.execute.return_value = cursor
                mock_conn.return_value = conn_instance
                with patch("os.listdir", side_effect=Exception("permission denied")):
                    resp = client.get("/api/v1/health/full")
                    assert resp.status_code == 200
                    data = resp.json()["data"]
                    assert data.get("total_backups") == 0

    def test_full_health_slow_queries(self, client):
        with patch("app.utils.paths.get_database_path") as mock_gdp, \
             patch("app.utils.paths.get_backup_path") as mock_gbp, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=1024):
            mock_gdp.return_value.absolute.return_value = "/fake/db.sqlite3"
            mock_gbp.return_value = "/fake/backups"
            with patch("sqlite3.connect") as mock_conn:
                conn_instance = MagicMock()
                cursor = MagicMock()
                cursor.fetchone.side_effect = [(5,), ("ok",)]
                conn_instance.execute.return_value = cursor
                mock_conn.return_value = conn_instance
                with patch("os.listdir", return_value=[]), \
                     patch("app.core.query_optimizer.get_slow_queries") as mock_sq:
                    mock_sq.return_value = [{"slow": True}, {"slow": False}]
                    resp = client.get("/api/v1/health/full")
                    assert resp.status_code == 200
                    assert resp.json()["data"]["slow_queries_24h"] == 1

    def test_full_health_slow_queries_error(self, client):
        with patch("app.utils.paths.get_database_path") as mock_gdp, \
             patch("app.utils.paths.get_backup_path") as mock_gbp, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=1024):
            mock_gdp.return_value.absolute.return_value = "/fake/db.sqlite3"
            mock_gbp.return_value = "/fake/backups"
            with patch("sqlite3.connect") as mock_conn:
                conn_instance = MagicMock()
                cursor = MagicMock()
                cursor.fetchone.side_effect = [(5,), ("ok",)]
                conn_instance.execute.return_value = cursor
                mock_conn.return_value = conn_instance
                with patch("os.listdir", return_value=[]), \
                     patch("app.core.query_optimizer.get_slow_queries", side_effect=Exception("import error")):
                    resp = client.get("/api/v1/health/full")
                    assert resp.status_code == 200
                    assert resp.json()["data"]["slow_queries_24h"] == 0
