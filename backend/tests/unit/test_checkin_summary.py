"""驻村工作台(T3.3): 打卡去重 + 月度总结"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _user(role="user"):
    return SimpleNamespace(id=1, role=role, username="u1")


def test_create_checkin_duplicate_rejected(monkeypatch):
    import os as _os

    _os.environ["INTERNAL_BACKUP_KEY"] = "test-internal-key"
    from app.main import app
    from app.core.database import get_db
    from app.core.security import get_current_user

    mock_db = MagicMock()
    # 已存在 checkin 记录
    mock_db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(id=1)

    app.dependency_overrides[get_db] = lambda: mock_db
    with patch("app.core.database.SessionLocal") as mk_sl:
        mk_sl.return_value = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: _user()
    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.post(
            "/api/v1/work-logs",
            json={
                "log_date": "2026-08-02",
                "content": "驻村打卡",
                "category": "checkin",
                "location": "甲村村委会",
            },
            headers={"X-Internal-Backup": "test-internal-key"},
        )
        assert resp.status_code == 400
        assert "打卡" in resp.text
    finally:
        app.dependency_overrides.clear()


def test_create_checkin_first_time_ok(monkeypatch):
    import os as _os

    _os.environ["INTERNAL_BACKUP_KEY"] = "test-internal-key"
    from app.main import app
    from app.core.database import get_db
    from app.core.security import get_current_user

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 5)

    app.dependency_overrides[get_db] = lambda: mock_db
    with patch("app.core.database.SessionLocal") as mk_sl:
        mk_sl.return_value = MagicMock()
    with patch("app.core.database.SessionLocal") as mk_sl:
        mk_sl.return_value = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: _user()
    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.post(
            "/api/v1/work-logs",
            json={
                "log_date": "2026-08-02",
                "content": "驻村打卡",
                "category": "checkin",
                "location": "甲村村委会",
            },
            headers={"X-Internal-Backup": "test-internal-key"},
        )
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_monthly_summary_admin():
    from app.main import app
    from app.core.database import get_db
    from app.core.security import get_current_user

    mock_db = MagicMock()
    logs = [
        SimpleNamespace(id=1, log_date=date(2026, 8, 1), content="走访农户", category="daily", location="甲村"),
        SimpleNamespace(id=2, log_date=date(2026, 8, 2), content="驻村打卡", category="checkin", location="甲村"),
        SimpleNamespace(id=3, log_date=date(2026, 8, 3), content="驻村打卡", category="checkin", location="乙村"),
        SimpleNamespace(id=4, log_date=date(2026, 8, 5), content="项目推进", category="project", location=None),
    ]
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = logs

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: _user("admin")
    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.get("/api/v1/work-logs/monthly-summary?year=2026&month=8")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_logs"] == 4
        assert data["checkin_days"] == 2
        assert data["category_counts"]["checkin"] == 2
        assert "驻村打卡 2 天" in data["summary_text"]
        assert len(data["items"]) == 4
    finally:
        app.dependency_overrides.clear()


def test_monthly_summary_user_sees_own():
    from app.main import app
    from app.core.database import get_db
    from app.core.security import get_current_user

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
    # 需要 or_ 过滤: filter 被调用两次
    mock_db.query.return_value.filter.side_effect = lambda *a, **k: mock_db.query.return_value

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: _user("user")
    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.get("/api/v1/work-logs/monthly-summary?year=2026&month=8")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_logs"] == 0
        assert data["checkin_days"] == 0
    finally:
        app.dependency_overrides.clear()
