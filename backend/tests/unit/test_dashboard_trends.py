"""dashboard kpi-trends / yearly-trends 端点测试"""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _user():
    return SimpleNamespace(id=1, username="u", role="admin")


def _deps(app, mock_db):
    from app.core.database import get_db
    from app.core.security import get_current_user

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: _user()


def test_kpi_trends_success():
    from app.main import app

    mock_db = MagicMock()
    _deps(app, mock_db)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        with patch(
            "app.api.v1.data.data.dashboard._query_village_stats",
            return_value={"total_villages": 12, "total_population": 3400},
        ), patch(
            "app.api.v1.data.data.dashboard._query_fund_stats",
            return_value={"funds_allocated": 5000.0, "total_funds": 8000.0},
        ), patch(
            "app.api.v1.data.data.dashboard._avg_per_capita_income",
            return_value=8800.5,
        ):
            resp = client.get("/api/v1/dashboard/kpi-trends")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["villages"] == 12
        assert data["population"] == 3400
        assert data["income"] == 8800.5
        assert data["investment"] == 9000.0  # 5000 + 8000/2
    finally:
        app.dependency_overrides.clear()


def test_kpi_trends_exception_fallback():
    from app.main import app

    mock_db = MagicMock()
    _deps(app, mock_db)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        with patch(
            "app.api.v1.data.data.dashboard._query_village_stats",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get("/api/v1/dashboard/kpi-trends")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["villages"] == 0
    finally:
        app.dependency_overrides.clear()


def test_yearly_trends_structure():
    from app.main import app

    mock_db = MagicMock()
    # 各类查询返回合理值
    mock_db.query.return_value.filter.return_value.scalar.return_value = 5
    mock_db.query.return_value.filter.return_value.first.return_value = (100.0, 80.0, 3)

    _deps(app, mock_db)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        with patch(
            "app.api.v1.data.data.dashboard._avg_per_capita_income",
            return_value=7600.0,
        ):
            resp = client.get("/api/v1/dashboard/yearly-trends?years=3")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["years"]) == 3
        assert len(data["villages"]) == 3
        assert len(data["population"]) == 3
        assert len(data["income"]) == 3
        assert len(data["trends"]) == 3
        t0 = data["trends"][0]
        assert "year" in t0
        assert "total_planned" in t0
        assert "total_actual" in t0
        assert "project_count" in t0
        # 年份为最近 3 年
        now = datetime.now().year
        assert data["years"] == [now - 2, now - 1, now]
    finally:
        app.dependency_overrides.clear()


def test_avg_per_capita_income_no_columns():
    from app.api.v1.data.data.dashboard import _avg_per_capita_income

    mock_db = MagicMock()

    class _FakeCols:
        name = "id"

    class _FakeTable:
        columns = [_FakeCols()]

    class _FakeModel:
        __table__ = _FakeTable()

    with patch("app.models.annual_income.AnnualIncome", _FakeModel):
        assert _avg_per_capita_income(mock_db, MagicMock()) == 0.0


def test_avg_per_capita_income_specific_year_missing():
    from app.api.v1.data.data.dashboard import _avg_per_capita_income

    mock_db = MagicMock()

    class _FakeCols:
        name = "per_capita_income_2024"

    class _FakeTable:
        columns = [_FakeCols()]

    class _FakeModel:
        __table__ = _FakeTable()

    with patch("app.models.annual_income.AnnualIncome", _FakeModel):
        # 请求 2025 年但只有 2024 列 → 0
        assert _avg_per_capita_income(mock_db, MagicMock(), year=2025) == 0.0


def test_yearly_trends_exception_fallback():
    from app.main import app

    mock_db = MagicMock()
    _deps(app, mock_db)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        with patch(
            "app.api.v1.data.data.dashboard._avg_per_capita_income",
            side_effect=RuntimeError("boom"),
        ):
            resp = client.get("/api/v1/dashboard/yearly-trends?years=2")
        assert resp.status_code == 200
        assert resp.json()["data"]["trends"] == []
    finally:
        app.dependency_overrides.clear()
