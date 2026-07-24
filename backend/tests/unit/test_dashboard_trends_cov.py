"""app.api.v1.data.data.dashboard_trends 覆盖率攻坚测试

覆盖点：
- _yoy：prev==0 且 cur==0、prev==0 且 cur!=0、常规四舍五入
- GET /dashboard/kpi-trends：全查询序列（8 次 scalar）+ 无 per_capita_income 分支 + 异常回退
- GET /dashboard/yearly-trends：多年循环 + 无 per_capita_income 分支 + 异常回退
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import app.api.v1.data.data.dashboard_trends as dt
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.unified_data_scope import get_org_scope

BASE = "/api/v1/dashboard"


# ==================== 公共设施 ====================


def _make_db(scalars):
    """构造按序返回 scalar 的 mock db"""
    q = MagicMock()
    q.filter.return_value = q
    q.scalar.side_effect = list(scalars)
    db = MagicMock()
    db.query = MagicMock(return_value=q)
    return db, q


class _Scope:
    """data_scope.filter_by_org_ids 原样返回 query"""

    @staticmethod
    def filter_by_org_ids(q, *args, **kwargs):
        return q


@pytest.fixture
def dt_client():
    from app.main import app

    original = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, username="root")
    app.dependency_overrides[get_org_scope] = lambda: _Scope()
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides = original


def _use_db(client, db):
    client.app.dependency_overrides[get_db] = lambda: db


# ==================== _yoy 纯函数 ====================


class TestYoy:
    def test_prev_zero_cur_zero(self):
        assert dt._yoy(0, 0) == 0.0

    def test_prev_zero_cur_nonzero(self):
        assert dt._yoy(5, 0) == 100.0

    def test_normal_round(self):
        assert dt._yoy(11, 10) == 10.0
        assert dt._yoy(10, 8) == 25.0


# ==================== GET /kpi-trends ====================


class TestKpiTrends:
    def test_full_path(self, dt_client):
        # 8 次 scalar：村cur/村prev/人口cur/人口prev/经费cur/经费prev/收入cur/收入prev
        db, _ = _make_db([10, 8, 1000, 800, 500.0, 400.0, 3.0, 2.5])
        _use_db(dt_client, db)
        resp = dt_client.get(f"{BASE}/kpi-trends")
        assert resp.status_code == 200
        data = resp.json()
        assert data["villages"] == 25.0
        assert data["population"] == 25.0
        assert data["investment"] == 25.0
        assert data["income"] == 20.0
        assert data["current_year"] == data["previous_year"] + 1

    def test_zero_prev_gives_100(self, dt_client):
        db, _ = _make_db([5, 0, 100, 0, 200.0, 0, 1.0, 0])
        _use_db(dt_client, db)
        resp = dt_client.get(f"{BASE}/kpi-trends")
        assert resp.status_code == 200
        data = resp.json()
        assert data["villages"] == 100.0
        assert data["population"] == 100.0

    def test_no_per_capita_income_attr(self, dt_client, monkeypatch):
        # 模型缺少 per_capita_income 属性时，收入恒 0 且不查询（仅 6 次 scalar）
        class FakeVI:
            pass

        monkeypatch.setattr(dt, "VillageIncome", FakeVI)
        db, _ = _make_db([4, 4, 100, 100, 100.0, 100.0])
        _use_db(dt_client, db)
        resp = dt_client.get(f"{BASE}/kpi-trends")
        assert resp.status_code == 200
        data = resp.json()
        assert data["income"] == 0.0
        assert data["villages"] == 0.0

    def test_scalar_none_falls_back_zero(self, dt_client):
        db, _ = _make_db([None, None, None, None, None, None, None, None])
        _use_db(dt_client, db)
        resp = dt_client.get(f"{BASE}/kpi-trends")
        assert resp.status_code == 200
        data = resp.json()
        assert data["villages"] == 0.0
        assert data["population"] == 0.0

    def test_exception_returns_fallback(self, dt_client):
        db = MagicMock()
        db.query = MagicMock(side_effect=RuntimeError("boom"))
        _use_db(dt_client, db)
        resp = dt_client.get(f"{BASE}/kpi-trends")
        assert resp.status_code == 200
        data = resp.json()
        assert data["villages"] == 0
        assert data["population"] == 0
        assert data["income"] == 0
        assert data["investment"] == 0
        assert data["current_year"] == data["previous_year"] + 1


# ==================== GET /yearly-trends ====================


class TestYearlyTrends:
    def test_two_years_full_path(self, dt_client):
        # 每年 4 次 scalar：村/人口/收入/经费，共 2 年
        db, _ = _make_db([
            5, 100, 2000.456, 9000.234,   # 第 1 年
            7, 150, 2500.567, 12000.789,  # 第 2 年
        ])
        _use_db(dt_client, db)
        resp = dt_client.get(f"{BASE}/yearly-trends?years=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["years"]) == 2
        assert data["villages"] == [5, 7]
        assert data["population"] == [100, 150]
        assert data["income"] == [2000.5, 2500.6]
        assert data["investment"] == [9000.2, 12000.8]

    def test_no_per_capita_income_attr(self, dt_client, monkeypatch):
        class FakeVI:
            pass

        monkeypatch.setattr(dt, "VillageIncome", FakeVI)
        # 无收入查询：每年 3 次 scalar（村/人口/经费）
        db, _ = _make_db([3, 50, 1000.0])
        _use_db(dt_client, db)
        resp = dt_client.get(f"{BASE}/yearly-trends?years=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["income"] == [0.0]
        assert data["villages"] == [3]
        assert data["population"] == [50]

    def test_scalar_none_falls_back_zero(self, dt_client):
        db, _ = _make_db([None, None, None, None])
        _use_db(dt_client, db)
        resp = dt_client.get(f"{BASE}/yearly-trends?years=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["villages"] == [0]
        assert data["income"] == [0.0]
        assert data["investment"] == [0.0]

    def test_exception_returns_fallback(self, dt_client):
        db = MagicMock()
        db.query = MagicMock(side_effect=RuntimeError("boom"))
        _use_db(dt_client, db)
        resp = dt_client.get(f"{BASE}/yearly-trends?years=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["years"]) == 3
        assert data["villages"] == [0, 0, 0]
        assert data["population"] == [0, 0, 0]
        assert data["income"] == [0, 0, 0]
        assert data["investment"] == [0, 0, 0]
