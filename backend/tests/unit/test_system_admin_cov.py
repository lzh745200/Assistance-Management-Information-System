"""app.api.v1.system.admin 覆盖率攻坚测试

覆盖缺口：
- 284-285：/clear-cache 中 dashboard 缓存清理失败的 warning 降级
- 349-387：POST /db-optimize 全分支（非sqlite 400 / :memory: 400 /
  文件不存在 404 / 真SQLite文件执行 WAL checkpoint+optimize 成功）
"""

import sqlite3
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_current_active_user, get_current_user

BASE = "/api/v1/system/admin"


@pytest.fixture
def client():
    from app.main import app

    original = app.dependency_overrides.copy()
    admin = SimpleNamespace(id=1, username="admin", role="admin", is_superuser=True)
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_current_active_user] = lambda: admin
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides = original


class TestCacheClearDegrade:
    def test_dashboard_invalidate_failure_degrades(self, client):
        """284-285：dashboard 缓存清理抛异常 → warning 降级，端点仍成功"""
        with patch(
            "app.api.v1.data.data.dashboard.invalidate_dashboard_cache",
            side_effect=Exception("diskcache locked"),
        ):
            resp = client.post(f"{BASE}/clear-cache")
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestDbOptimize:
    def _engine(self, url: str):
        return patch("app.core.database.engine", SimpleNamespace(url=url))

    def test_non_sqlite_400(self, client):
        with self._engine("postgresql://u:p@host/db"):
            resp = client.post(f"{BASE}/db-optimize")
        assert resp.status_code == 400

    def test_memory_db_400(self, client):
        with self._engine("sqlite:///:memory:"):
            resp = client.post(f"{BASE}/db-optimize")
        assert resp.status_code == 400

    def test_missing_file_404(self, client, tmp_path):
        db_path = tmp_path / "no_such.db"
        with self._engine(f"sqlite:///{db_path}"):
            resp = client.post(f"{BASE}/db-optimize")
        assert resp.status_code == 404

    def test_optimize_success_real_sqlite(self, client, tmp_path):
        """349-387：真 SQLite 文件执行 WAL checkpoint + PRAGMA optimize"""
        db_path = tmp_path / "real.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
        conn.executemany("INSERT INTO t (v) VALUES (?)", [(f"row{i}",) for i in range(100)])
        conn.commit()
        conn.close()

        with self._engine(f"sqlite:///{db_path}"):
            resp = client.post(f"{BASE}/db-optimize")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["size_before_kb"] > 0
        assert "size_after_kb" in data
        assert "saved_kb" in data

    def test_url_parse_variants(self, client, tmp_path):
        """URL 三分支解析：:// / 冒号直写"""
        db_path = tmp_path / "v.db"
        sqlite3.connect(str(db_path)).close()
        # '://' 两斜杠变体（sqlite://path → 取 // 之后）
        with self._engine(f"sqlite://{db_path}"):
            resp = client.post(f"{BASE}/db-optimize")
        assert resp.status_code == 200

    def test_url_colon_variant(self, client, tmp_path):
        """sqlite:path 单冒号变体"""
        db_path = tmp_path / "v2.db"
        sqlite3.connect(str(db_path)).close()
        with self._engine(f"sqlite:{db_path}"):
            resp = client.post(f"{BASE}/db-optimize")
        assert resp.status_code == 200

    def test_url_bare_path_variant(self, client, tmp_path):
        """裸 'sqlite' 串（无冒号）→ else 分支 db_path='sqlite' → 文件不存在 404"""
        with self._engine("sqlite"):
            resp = client.post(f"{BASE}/db-optimize")
        assert resp.status_code == 404
