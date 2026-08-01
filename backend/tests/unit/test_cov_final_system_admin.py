"""app.api.v1.system.admin 覆盖补全 — 用户不存在时的 404 分支 (lines 437, 456)."""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mocks():
    db = MagicMock(name="db")
    q = MagicMock(name="query")
    q.filter.return_value = q
    q.first.return_value = None  # 用户不存在
    db.query.return_value = q

    user = MagicMock(name="user")
    user.id = 1
    user.role = "admin"
    user.is_superuser = True
    user.username = "admin"
    return db, q, user


@pytest.fixture
def client(mocks):
    from app.main import app
    from app.core.database import get_db
    from app.core.security import get_current_user

    db, _, user = mocks
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    tc = TestClient(app, raise_server_exceptions=False)
    yield tc
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


class TestRevokeUserSession:
    def test_user_not_found(self, client):
        resp = client.post("/api/v1/system/admin/users/9/sessions/sess-abc/revoke")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "用户不存在"


class TestResetUserTwoFactor:
    def test_user_not_found(self, client):
        resp = client.post("/api/v1/system/admin/users/9/two-factor/reset")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "用户不存在"
