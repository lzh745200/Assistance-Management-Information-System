"""app.api.v1.monitoring.secrets 覆盖补全 — _require_admin 非管理员 403 分支 (line 19)."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    from app.core.security import get_current_active_user

    user = SimpleNamespace(id=2, username="bob", role="user", is_superuser=False)
    app.dependency_overrides[get_current_active_user] = lambda: user
    tc = TestClient(app, raise_server_exceptions=False)
    yield tc
    app.dependency_overrides.pop(get_current_active_user, None)


class TestRequireAdmin:
    def test_non_admin_forbidden(self, client):
        resp = client.get("/api/v1/secrets/versions")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "需要管理员权限"
