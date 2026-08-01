"""app.api.v1.machine_code 覆盖补全 — 删除组织通行码的非管理员 403 分支 (line 714)."""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mocks():
    db = MagicMock(name="db")
    user = MagicMock(name="user")
    user.id = 2
    user.role = "user"
    user.is_superuser = False
    return db, user


@pytest.fixture
def client(mocks):
    from app.main import app
    from app.core.database import get_db
    from app.core.security import get_current_user

    db, user = mocks
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    tc = TestClient(app, raise_server_exceptions=False)
    yield tc
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


class TestDeleteOrganizationPassCode:
    def test_non_admin_forbidden(self, client):
        resp = client.delete("/api/v1/machine-code/organization/5")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "需要管理员权限"
