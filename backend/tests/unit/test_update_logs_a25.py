"""
Tests for update_logs.py — 补齐 403/500 分支覆盖率。
"""

from unittest.mock import MagicMock, patch

BASE = "/api/v1/system/update-logs"


class TestCreateForbidden:
    def test_non_admin_forbidden(self, client_with_mocked_auth):
        with patch("app.core.permission_utils.is_admin", return_value=False):
            resp = client_with_mocked_auth.post(
                BASE, json={"version": "1.1.0", "description": "d"},
            )
        assert resp.status_code == 403

    def test_service_exception_returns_500(self, client_with_mocked_auth):
        mock_svc = MagicMock()
        mock_svc.record_update.side_effect = RuntimeError("boom")
        with patch("app.api.v1.system.update_logs.UpdateLogService", return_value=mock_svc):
            resp = client_with_mocked_auth.post(
                BASE, json={"version": "1.1.0", "description": "d"},
            )
        assert resp.status_code == 500


class TestInitializeBranches:
    def test_non_admin_forbidden(self, client_with_mocked_auth):
        with patch("app.core.permission_utils.is_admin", return_value=False):
            resp = client_with_mocked_auth.post(f"{BASE}/initialize", json={})
        assert resp.status_code == 403

    def test_service_exception_returns_500(self, client_with_mocked_auth):
        mock_svc = MagicMock()
        mock_svc.initialize_version_history.side_effect = RuntimeError("boom")
        with patch("app.api.v1.system.update_logs.UpdateLogService", return_value=mock_svc):
            resp = client_with_mocked_auth.post(f"{BASE}/initialize", json={})
        assert resp.status_code == 500


class TestSyncBranches:
    def test_non_admin_forbidden(self, client_with_mocked_auth):
        with patch("app.core.permission_utils.is_admin", return_value=False):
            resp = client_with_mocked_auth.post(f"{BASE}/sync")
        assert resp.status_code == 403

    def test_service_exception_returns_500(self, client_with_mocked_auth):
        mock_svc = MagicMock()
        mock_svc.sync_version_history.side_effect = RuntimeError("boom")
        with patch("app.api.v1.system.update_logs.UpdateLogService", return_value=mock_svc):
            resp = client_with_mocked_auth.post(f"{BASE}/sync")
        assert resp.status_code == 500


class TestDeleteForbidden:
    def test_non_admin_forbidden(self, client_with_mocked_auth):
        with patch("app.core.permission_utils.is_admin", return_value=False):
            resp = client_with_mocked_auth.delete(f"{BASE}/1")
        assert resp.status_code == 403
