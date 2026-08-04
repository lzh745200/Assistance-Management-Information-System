"""dashboard.py /summary 缓存命中分支隔离测试。

全量运行中其他测试会先调用 /summary 或修改 dependency_overrides，
导致本分支覆盖不稳定。此文件独立验证缓存命中路径。
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.unified_data_scope import get_org_scope

BASE = "/api/v1/dashboard"


class _Scope:
    org_ids = []

    @staticmethod
    def filter_by_org_ids(q, *args, **kwargs):
        return q

    def has_full_access(self):
        return True


@pytest.fixture
def client():
    from app.main import app

    original = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, username="root")
    app.dependency_overrides[get_org_scope] = lambda: _Scope()
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides = original


class TestDashboardSummaryCache:
    def test_cache_hit_returns_cached(self, client):
        import app.api.v1.data.data.dashboard as dash_mod

        cached_payload = {"success": True, "data": {"cached_marker": 1}}
        with patch.object(dash_mod, "_get_cached", return_value=cached_payload):
            resp = client.get(f"{BASE}/summary")
            assert resp.status_code == 200
            assert resp.json()["data"]["cached_marker"] == 1

    def test_cache_miss_then_queries(self, client):
        import app.api.v1.data.data.dashboard as dash_mod

        db = MagicMock()

        def fake_query(*_args, **_kwargs):
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = None
            q.all.return_value = []
            q.scalar.return_value = 0
            q.order_by.return_value = q
            q.group_by.return_value = q
            q.count.return_value = 0
            return q

        db.query.side_effect = fake_query
        client.app.dependency_overrides[get_db] = lambda: db
        with patch.object(dash_mod, "_get_cached", return_value=None), \
             patch.object(dash_mod, "_set_cached"):
            resp = client.get(f"{BASE}/summary")
            assert resp.status_code == 200
            body = resp.json()
            assert "stats" in body
            assert "recent_activities" in body
