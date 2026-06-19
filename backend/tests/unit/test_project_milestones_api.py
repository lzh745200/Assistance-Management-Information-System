"""Tests for app.api.v1.project_milestones — 9 endpoints."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def mock_db():
    s = MagicMock()
    s.query.return_value = s
    s.filter.return_value = s
    s.order_by.return_value = s
    s.all.return_value = []
    s.first.return_value = None
    return s


def _make_milestone():
    m = MagicMock()
    m.id = 1; m.project_id = 1; m.name = "基础施工"; m.description = "地基"
    m.planned_date = date(2025, 6, 1); m.actual_date = None
    m.responsible_person = "张三"; m.status = "pending"; m.sort_order = 1
    return m


def _make_project():
    p = MagicMock()
    p.id = 1; p.project_name = "道路工程"; p.status = "in_progress"
    return p


@pytest.fixture
def client(mock_db):
    from app.api.v1 import deps
    app = FastAPI()
    user = MagicMock()
    user.id = 1; user.username = "admin"
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_db] = lambda: mock_db
    from app.api.v1.project_milestones import router
    app.include_router(router)
    return TestClient(app)


class TestGetMilestones:
    def test_empty(self, client, mock_db):
        mock_db.all.return_value = []
        resp = client.get("/projects/1/milestones")
        assert resp.status_code == 200

    def test_with_data(self, client, mock_db):
        mock_db.all.return_value = [_make_milestone()]
        resp = client.get("/projects/1/milestones")
        assert resp.status_code == 200


class TestCreateMilestone:
    def test_success(self, client, mock_db):
        mock_db.first.side_effect = [_make_project(), _make_milestone()]
        resp = client.post("/projects/1/milestones", json={
            "name": "新里程碑", "planned_date": "2025-12-31",
            "responsible_person": "李四", "sort_order": 2
        })
        mock_db.add.assert_called_once()

    def test_project_not_found(self, client, mock_db):
        mock_db.first.return_value = None
        resp = client.post("/projects/1/milestones", json={
            "name": "里程碑", "planned_date": "2025-12-31"
        })
        assert resp.status_code == 404


class TestUpdateMilestone:
    def test_success(self, client, mock_db):
        mock_db.first.side_effect = [_make_milestone(), _make_milestone()]
        resp = client.put("/projects/1/milestones/1", json={"name": "更新名称"})
        assert resp.status_code == 200

    def test_not_found(self, client, mock_db):
        mock_db.first.return_value = None
        resp = client.put("/projects/1/milestones/999", json={"name": "更新"})
        assert resp.status_code == 404


class TestDeleteMilestone:
    def test_success(self, client, mock_db):
        mock_db.first.return_value = _make_milestone()
        resp = client.delete("/projects/1/milestones/1")
        assert resp.status_code == 200

    def test_not_found(self, client, mock_db):
        mock_db.first.return_value = None
        resp = client.delete("/projects/1/milestones/999")
        assert resp.status_code == 404


class TestGetTransitionRules:
    def test_returns_rules(self, client, mock_db):
        mock_db.first.return_value = _make_project()
        resp = client.get("/projects/1/transition-rules")
        assert resp.status_code == 200

    def test_project_not_found(self, client, mock_db):
        mock_db.first.return_value = None
        resp = client.get("/projects/1/transition-rules")
        assert resp.status_code == 404


class TestTransitionStatus:
    def test_success(self, client, mock_db):
        mock_db.first.side_effect = [_make_project(), _make_milestone()]
        with patch("app.api.v1.project_milestones.validate_status_transition", return_value=(True, None)):
            resp = client.post("/projects/1/transition", json={
                "target_status": "completed", "comment": "完成"
            })
            mock_db.add.assert_called()  # Should add change log

    def test_project_not_found(self, client, mock_db):
        mock_db.first.return_value = None
        resp = client.post("/projects/1/transition", json={
            "target_status": "completed"
        })
        assert resp.status_code == 404

    def test_invalid_transition(self, client, mock_db):
        mock_db.first.side_effect = [_make_project(), _make_milestone()]
        with patch("app.api.v1.project_milestones.validate_status_transition", return_value=(False, "无效转换")):
            resp = client.post("/projects/1/transition", json={
                "target_status": "invalid"
            })
            assert resp.status_code == 400


class TestGetChangeLogs:
    def test_empty(self, client, mock_db):
        mock_db.all.return_value = []
        resp = client.get("/projects/1/change-logs")
        assert resp.status_code == 200

    def test_with_data(self, client, mock_db):
        log = MagicMock()
        log.id = 1; log.project_id = 1; log.field_name = "status"
        log.old_value = "pending"; log.new_value = "completed"
        log.changed_by = "admin"; log.created_at = datetime(2025, 6, 1)
        mock_db.all.return_value = [log]
        resp = client.get("/projects/1/change-logs")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestUpcomingMilestones:
    def test_empty(self, client, mock_db):
        mock_db.all.return_value = []
        resp = client.get("/projects/dashboard/upcoming-milestones")
        assert resp.status_code == 200

    def test_with_data(self, client, mock_db):
        mock_db.all.return_value = [_make_milestone()]
        resp = client.get("/projects/dashboard/upcoming-milestones?days=30")
        assert resp.status_code == 200


class TestOverdueMilestones:
    def test_empty(self, client, mock_db):
        mock_db.all.return_value = []
        resp = client.get("/projects/dashboard/overdue-milestones")
        assert resp.status_code == 200

    def test_with_data(self, client, mock_db):
        m = _make_milestone()
        m.planned_date = date(2020, 1, 1)  # Very overdue
        mock_db.all.return_value = [m]
        resp = client.get("/projects/dashboard/overdue-milestones")
        assert resp.status_code == 200
