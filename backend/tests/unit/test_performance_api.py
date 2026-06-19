"""
Tests for app.api.v1.performance — 100% coverage.

Covers all 5 endpoints (all admin-only):
  GET  /performance/slow-queries
  GET  /performance/query-stats
  DELETE /performance/slow-queries
  GET  /performance/cache-stats
  POST /performance/cache/clear
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


def _make_client(is_superuser=False):
    """Build a standalone FastAPI TestClient with auth dependency overridden."""
    from app.api.v1 import deps
    from app.api.v1.performance import router

    app = FastAPI()
    user = MagicMock()
    user.is_superuser = is_superuser
    app.dependency_overrides[deps.get_current_active_user] = lambda: user
    app.include_router(router)
    return TestClient(app)


# ═══════════════════════════════════════════════════════════════════════
# GET /performance/slow-queries
# ═══════════════════════════════════════════════════════════════════════

class TestGetSlowQueries:
    """GET /performance/slow-queries — admin only."""

    # ── auth ──

    def test_non_admin_returns_403(self):
        client = _make_client(is_superuser=False)
        resp = client.get("/performance/slow-queries")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "需要管理员权限"

    # ── success ──

    def test_returns_list_with_total(self):
        client = _make_client(is_superuser=True)
        queries = [
            {"timestamp": "2026-01-01T12:00:00", "query": "SELECT * FROM a",
             "duration_ms": 500.0},
            {"timestamp": "2026-01-01T12:01:00", "query": "SELECT * FROM b",
             "duration_ms": 300.0},
        ]
        with patch("app.api.v1.performance.query_analyzer") as qa:
            qa.get_slow_queries.return_value = queries
            resp = client.get("/performance/slow-queries?limit=50")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert len(data["queries"]) == 2
            assert data["queries"][0]["duration_ms"] == 500.0
            qa.get_slow_queries.assert_called_once_with(
                limit=50, min_duration_ms=None)

    def test_min_duration_filter_is_forwarded(self):
        client = _make_client(is_superuser=True)
        with patch("app.api.v1.performance.query_analyzer") as qa:
            qa.get_slow_queries.return_value = [
                {"timestamp": "2026-01-01", "query": "SELECT 1", "duration_ms": 500.0},
            ]
            resp = client.get(
                "/performance/slow-queries?limit=100&min_duration_ms=200.0")
            assert resp.status_code == 200
            qa.get_slow_queries.assert_called_once_with(
                limit=100, min_duration_ms=200.0)

    def test_default_limit_and_duration(self):
        client = _make_client(is_superuser=True)
        with patch("app.api.v1.performance.query_analyzer") as qa:
            qa.get_slow_queries.return_value = []
            resp = client.get("/performance/slow-queries")
            assert resp.status_code == 200
            assert resp.json()["total"] == 0
            assert resp.json()["queries"] == []
            qa.get_slow_queries.assert_called_once_with(
                limit=100, min_duration_ms=None)

    def test_limit_minimum_1(self):
        client = _make_client(is_superuser=True)
        with patch("app.api.v1.performance.query_analyzer") as qa:
            qa.get_slow_queries.return_value = [
                {"timestamp": "2026-01-01", "query": "x", "duration_ms": 10.0},
            ]
            resp = client.get("/performance/slow-queries?limit=1")
            assert resp.status_code == 200
            assert resp.json()["total"] == 1

    def test_limit_maximum_1000(self):
        client = _make_client(is_superuser=True)
        with patch("app.api.v1.performance.query_analyzer") as qa:
            qa.get_slow_queries.return_value = []
            resp = client.get("/performance/slow-queries?limit=1000")
            assert resp.status_code == 200

    def test_min_duration_ms_zero(self):
        client = _make_client(is_superuser=True)
        with patch("app.api.v1.performance.query_analyzer") as qa:
            qa.get_slow_queries.return_value = []
            resp = client.get("/performance/slow-queries?min_duration_ms=0")
            assert resp.status_code == 200
            qa.get_slow_queries.assert_called_once_with(
                limit=100, min_duration_ms=0.0)

    # ── validation (422) ──

    def test_limit_below_1_returns_422(self):
        client = _make_client(is_superuser=True)
        resp = client.get("/performance/slow-queries?limit=0")
        assert resp.status_code == 422

    def test_limit_above_1000_returns_422(self):
        client = _make_client(is_superuser=True)
        resp = client.get("/performance/slow-queries?limit=1001")
        assert resp.status_code == 422

    def test_negative_min_duration_returns_422(self):
        client = _make_client(is_superuser=True)
        resp = client.get("/performance/slow-queries?min_duration_ms=-1")
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════
# GET /performance/query-stats
# ═══════════════════════════════════════════════════════════════════════

class TestGetQueryStats:
    """GET /performance/query-stats — admin only."""

    def test_non_admin_returns_403(self):
        client = _make_client(is_superuser=False)
        resp = client.get("/performance/query-stats")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "需要管理员权限"

    def test_returns_full_stats(self):
        client = _make_client(is_superuser=True)
        stats = {
            "total_slow_queries": 10,
            "avg_duration_ms": 250.5,
            "max_duration_ms": 900.0,
            "min_duration_ms": 100.0,
            "p50_duration_ms": 200.0,
            "p95_duration_ms": 800.0,
            "p99_duration_ms": 890.0,
        }
        with patch("app.api.v1.performance.query_analyzer") as qa:
            qa.get_query_stats.return_value = stats
            resp = client.get("/performance/query-stats")
            assert resp.status_code == 200
            data = resp.json()
            assert data == stats
            qa.get_query_stats.assert_called_once()

    def test_empty_stats(self):
        client = _make_client(is_superuser=True)
        empty = {"total_slow_queries": 0, "avg_duration_ms": 0,
                 "max_duration_ms": 0, "min_duration_ms": 0}
        with patch("app.api.v1.performance.query_analyzer") as qa:
            qa.get_query_stats.return_value = empty
            resp = client.get("/performance/query-stats")
            assert resp.status_code == 200
            assert resp.json()["total_slow_queries"] == 0


# ═══════════════════════════════════════════════════════════════════════
# DELETE /performance/slow-queries
# ═══════════════════════════════════════════════════════════════════════

class TestClearSlowQueries:
    """DELETE /performance/slow-queries — admin only."""

    def test_non_admin_returns_403(self):
        client = _make_client(is_superuser=False)
        resp = client.delete("/performance/slow-queries")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "需要管理员权限"

    def test_admin_clears(self):
        client = _make_client(is_superuser=True)
        with patch("app.api.v1.performance.query_analyzer") as qa:
            resp = client.delete("/performance/slow-queries")
            assert resp.status_code == 200
            assert resp.json()["message"] == "慢查询记录已清空"
            qa.clear_slow_queries.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════
# GET /performance/cache-stats
# ═══════════════════════════════════════════════════════════════════════

class TestCacheStats:
    """GET /performance/cache-stats — admin only."""

    def test_non_admin_returns_403(self):
        client = _make_client(is_superuser=False)
        resp = client.get("/performance/cache-stats")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "需要管理员权限"

    def test_healthy_cache(self):
        client = _make_client(is_superuser=True)
        with patch("app.api.v1.performance.redis_adapter") as r:
            r.get_stats.return_value = {"total_keys": 42, "hit_rate": 0.85}
            r.health_check.return_value = {"status": "healthy"}
            resp = client.get("/performance/cache-stats")
            assert resp.status_code == 200
            data = resp.json()
            assert data["stats"] == {"total_keys": 42, "hit_rate": 0.85}
            assert data["health"] == {"status": "healthy"}
            r.get_stats.assert_called_once()
            r.health_check.assert_called_once()

    def test_degraded_cache(self):
        client = _make_client(is_superuser=True)
        with patch("app.api.v1.performance.redis_adapter") as r:
            r.get_stats.return_value = {"total_keys": 0}
            r.health_check.return_value = {"status": "degraded", "reason": "empty"}
            resp = client.get("/performance/cache-stats")
            assert resp.status_code == 200
            assert resp.json()["health"]["status"] == "degraded"


# ═══════════════════════════════════════════════════════════════════════
# POST /performance/cache/clear
# ═══════════════════════════════════════════════════════════════════════

class TestClearCache:
    """POST /performance/cache/clear — admin only."""

    def test_non_admin_returns_403(self):
        client = _make_client(is_superuser=False)
        resp = client.post("/performance/cache/clear")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "需要管理员权限"

    def test_admin_clears_successfully(self):
        client = _make_client(is_superuser=True)
        with patch("app.api.v1.performance.redis_adapter") as r:
            r.clear.return_value = True
            resp = client.post("/performance/cache/clear")
            assert resp.status_code == 200
            assert resp.json()["message"] == "缓存已清空"
            r.clear.assert_called_once()

    def test_admin_clear_failure_500(self):
        client = _make_client(is_superuser=True)
        with patch("app.api.v1.performance.redis_adapter") as r:
            r.clear.return_value = False
            resp = client.post("/performance/cache/clear")
            assert resp.status_code == 500
            assert resp.json()["detail"] == "清空缓存失败"
            r.clear.assert_called_once()
