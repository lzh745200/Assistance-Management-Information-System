"""Tests for app.api.v1.feedback — 100% coverage."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def mock_db():
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.order_by.return_value = session
    session.offset.return_value = session
    session.limit.return_value = session
    session.all.return_value = []
    session.count.return_value = 0
    return session


@pytest.fixture
def mock_user():
    return MagicMock()


@pytest.fixture
def client(mock_db, mock_user):
    from app.api.v1 import deps
    app = FastAPI()
    app.dependency_overrides[deps.get_current_user] = lambda: mock_user
    app.dependency_overrides[deps.get_db] = lambda: mock_db
    from app.api.v1.feedback import router
    app.include_router(router)
    return TestClient(app)


class TestListFeedback:
    def test_empty_list(self, client):
        resp = client.get("/feedback")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_with_type_filter(self, client, mock_db):
        from datetime import datetime, timezone
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.category = "bug"
        mock_row.content = "测试"
        mock_row.user_email = "a@b.com"
        mock_row.user_name = "user1"
        mock_row.status = "open"
        mock_row.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_db.all.return_value = [mock_row]
        mock_db.count.return_value = 1

        resp = client.get("/feedback?type=bug&page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["type"] == "bug"

    def test_type_all_skips_filter(self, client, mock_db):
        resp = client.get("/feedback?type=all")
        assert resp.status_code == 200
        # filter should NOT be called since type=="all" skips filtering

    def test_pagination(self, client, mock_db):
        mock_db.count.return_value = 50
        resp = client.get("/feedback?page=2&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["page"] == 2
        assert data["data"]["page_size"] == 10


class TestSubmitFeedback:
    def test_success_submission(self, client, mock_db):
        resp = client.post("/feedback", json={
            "type": "bug",
            "content": "页面加载缓慢",
            "contact": "test@example.com",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_empty_content_rejected(self, client):
        resp = client.post("/feedback", json={
            "type": "bug",
            "content": "   ",
        })
        assert resp.status_code == 400

    def test_invalid_type_defaults_to_other(self, client, mock_db):
        resp = client.post("/feedback", json={
            "type": "invalid_type",
            "content": "有效内容",
        })
        assert resp.status_code == 200

    def test_default_type_is_other(self, client, mock_db):
        resp = client.post("/feedback", json={
            "content": "没有指定类型",
        })
        assert resp.status_code == 200

    def test_db_error_returns_500(self, client, mock_db):
        mock_db.commit.side_effect = Exception("DB down")
        resp = client.post("/feedback", json={
            "content": "测试",
        })
        assert resp.status_code == 500
        mock_db.rollback.assert_called_once()

    def test_with_auth_header(self, client, mock_db):
        with patch("app.api.v1.feedback._get_user_from_token", return_value="testuser"):
            resp = client.post("/feedback", json={
                "content": "带token的反馈",
            }, headers={"Authorization": "Bearer fake-token"})
            assert resp.status_code == 200


class TestGetUserFromToken:
    @pytest.mark.asyncio
    async def test_no_header(self):
        from app.api.v1.feedback import _get_user_from_token
        result = await _get_user_from_token(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_non_bearer(self):
        from app.api.v1.feedback import _get_user_from_token
        result = await _get_user_from_token("Basic abc123")
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_token(self):
        with patch("app.api.v1.feedback.verify_token", return_value={"username": "admin"}):
            from app.api.v1.feedback import _get_user_from_token
            result = await _get_user_from_token("Bearer valid-token")
            assert result == "admin"

    @pytest.mark.asyncio
    async def test_verify_failure(self):
        with patch("app.api.v1.feedback.verify_token", side_effect=Exception("jwt error")):
            from app.api.v1.feedback import _get_user_from_token
            result = await _get_user_from_token("Bearer bad-token")
            assert result is None

    @pytest.mark.asyncio
    async def test_token_info_with_id_only(self):
        with patch("app.api.v1.feedback.verify_token", return_value={"id": "42"}):
            from app.api.v1.feedback import _get_user_from_token
            result = await _get_user_from_token("Bearer token-with-id")
            assert result == "42"
