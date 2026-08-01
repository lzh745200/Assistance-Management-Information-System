"""app.api.v1.encryption 覆盖补全 — initialize 写工作日志失败的静默降级分支 (lines 105-106)."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mocks():
    db = MagicMock(name="db")
    user = MagicMock(name="user")
    user.id = 1
    user.role = "admin"
    user.is_superuser = True
    user.username = "admin"
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


class TestInitializeEncryption:
    def test_work_log_failure_is_silently_ignored(self, client):
        svc = MagicMock(name="svc")
        svc.get.return_value = None  # 未初始化 → 允许继续
        with patch("app.api.v1.encryption.SystemConfigService", return_value=svc):
            with patch("app.api.v1.encryption.write_work_log", side_effect=RuntimeError("db down")):
                with patch("app.api.v1.encryption.logger") as mock_log:
                    resp = client.post(
                        "/api/v1/encryption/initialize",
                        json={"password": "secret123", "confirm_password": "secret123"},
                    )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        # 工作日志异常被吞掉并记录 debug 日志 (lines 105-106)
        mock_log.debug.assert_called_once()
