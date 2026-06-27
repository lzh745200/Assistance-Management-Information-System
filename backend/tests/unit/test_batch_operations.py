"""
Tests for batch_operations.py — batch update, delete, export, validate, status.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from pydantic import ValidationError

BASE = "/api/v1/batch"


# ── batch_update ─────────────────────────────────────────────────────

class TestBatchUpdate:
    def test_requires_auth(self, client):
        resp = client.post(f"{BASE}/update", json={"table_name": "villages", "ids": [1], "updates": {"name": "x"}})
        assert resp.status_code == 401

    def test_invalid_table_name(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/update",
            json={"table_name": "invalid_table", "ids": [1], "updates": {"name": "x"}},
        )
        assert resp.status_code == 422

    def test_invalid_ids_empty(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/update",
            json={"table_name": "villages", "ids": [], "updates": {"name": "x"}},
        )
        assert resp.status_code == 422

    def test_ids_too_many(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/update",
            json={"table_name": "villages", "ids": list(range(1001)), "updates": {"name": "x"}},
        )
        assert resp.status_code == 422

    def test_ids_not_positive(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/update",
            json={"table_name": "villages", "ids": [0, -1], "updates": {"name": "x"}},
        )
        assert resp.status_code == 422

    def test_invalid_updates_forbidden_fields(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/update",
            json={"table_name": "villages", "ids": [1], "updates": {"id": 999}},
        )
        assert resp.status_code == 422

    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_update = AsyncMock(return_value={"success": True, "updated": 1})
            resp = client_with_mocked_auth.post(
                f"{BASE}/update",
                json={"table_name": "villages", "ids": [1], "updates": {"name": "new_name"}},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True

    def test_validation_error_raised(self, client_with_mocked_auth):
        from app.core.exceptions import ValidationError
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_update = AsyncMock(side_effect=ValidationError("bad data"))
            resp = client_with_mocked_auth.post(
                f"{BASE}/update",
                json={"table_name": "villages", "ids": [1], "updates": {"name": "x"}},
            )
            assert resp.status_code >= 400

    def test_database_error_raised(self, client_with_mocked_auth):
        from app.core.exceptions import DatabaseError
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_update = AsyncMock(side_effect=DatabaseError("db error"))
            resp = client_with_mocked_auth.post(
                f"{BASE}/update",
                json={"table_name": "villages", "ids": [1], "updates": {"name": "x"}},
            )
            assert resp.status_code >= 400

    def test_unexpected_error_fallback(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_update = AsyncMock(side_effect=RuntimeError("unexpected"))
            resp = client_with_mocked_auth.post(
                f"{BASE}/update",
                json={"table_name": "villages", "ids": [1], "updates": {"name": "x"}},
            )
            assert resp.status_code == 400


# ── batch_delete ─────────────────────────────────────────────────────

class TestBatchDelete:
    def test_invalid_table_name(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/delete",
            json={"table_name": "bad", "ids": [1]},
        )
        assert resp.status_code == 422

    def test_success_soft_delete(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_delete = AsyncMock(return_value={"success": True, "deleted": 2})
            resp = client_with_mocked_auth.post(
                f"{BASE}/delete",
                json={"table_name": "villages", "ids": [1, 2], "soft_delete": True},
            )
            assert resp.status_code == 200

    def test_success_hard_delete(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_delete = AsyncMock(return_value={"success": True, "deleted": 1})
            resp = client_with_mocked_auth.post(
                f"{BASE}/delete",
                json={"table_name": "villages", "ids": [1], "soft_delete": False},
            )
            assert resp.status_code == 200

    def test_validation_error(self, client_with_mocked_auth):
        from app.core.exceptions import ValidationError
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_delete = AsyncMock(side_effect=ValidationError("bad"))
            resp = client_with_mocked_auth.post(
                f"{BASE}/delete",
                json={"table_name": "villages", "ids": [1]},
            )
            assert resp.status_code >= 400

    def test_database_error(self, client_with_mocked_auth):
        from app.core.exceptions import DatabaseError
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_delete = AsyncMock(side_effect=DatabaseError("db err"))
            resp = client_with_mocked_auth.post(
                f"{BASE}/delete",
                json={"table_name": "villages", "ids": [1]},
            )
            assert resp.status_code >= 400

    def test_unexpected_error(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_delete = AsyncMock(side_effect=RuntimeError("boom"))
            resp = client_with_mocked_auth.post(
                f"{BASE}/delete",
                json={"table_name": "villages", "ids": [1]},
            )
            assert resp.status_code == 400


# ── batch_export ─────────────────────────────────────────────────────

class TestBatchExport:
    def test_invalid_format(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/export",
            json={"table_name": "villages", "ids": [1], "format": "xml"},
        )
        assert resp.status_code == 422

    def test_ids_too_many_for_export(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/export",
            json={"table_name": "villages", "ids": list(range(5001)), "format": "xlsx"},
        )
        assert resp.status_code == 422

    def test_success_xlsx(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_export = AsyncMock(return_value={"success": True, "file": "data.xlsx"})
            resp = client_with_mocked_auth.post(
                f"{BASE}/export",
                json={"table_name": "villages", "ids": [1, 2], "format": "xlsx"},
            )
            assert resp.status_code == 200

    def test_success_csv(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_export = AsyncMock(return_value={"success": True, "file": "data.csv"})
            resp = client_with_mocked_auth.post(
                f"{BASE}/export",
                json={"table_name": "villages", "ids": [1], "format": "csv"},
            )
            assert resp.status_code == 200

    def test_success_json(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_export = AsyncMock(return_value={"success": True, "file": "data.json"})
            resp = client_with_mocked_auth.post(
                f"{BASE}/export",
                json={"table_name": "villages", "ids": [1], "format": "json"},
            )
            assert resp.status_code == 200

    def test_unexpected_error(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.batch_export = AsyncMock(side_effect=RuntimeError("fail"))
            resp = client_with_mocked_auth.post(
                f"{BASE}/export",
                json={"table_name": "villages", "ids": [1], "format": "xlsx"},
            )
            assert resp.status_code == 400


# ── validate_batch ──────────────────────────────────────────────────

class TestValidateBatch:
    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.validate_batch = AsyncMock(return_value={"success": True, "valid": True})
            resp = client_with_mocked_auth.post(
                f"{BASE}/validate?table_name=villages&ids=1&ids=2",
            )
            assert resp.status_code == 200

    def test_unexpected_error(self, client_with_mocked_auth):
        with patch("app.api.v1.batch_operations.batch_service") as mock_svc:
            mock_svc.validate_batch = AsyncMock(side_effect=RuntimeError("fail"))
            resp = client_with_mocked_auth.post(
                f"{BASE}/validate?table_name=villages&ids=1",
            )
            assert resp.status_code == 400


# ── get_batch_status ────────────────────────────────────────────────

class TestGetBatchStatus:
    def test_requires_auth(self, client):
        resp = client.get(f"{BASE}/status")
        assert resp.status_code == 401

    def test_idle_status(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["status"] == "idle"


# ── Pydantic validators (direct unit tests) ─────────────────────────

class TestBatchUpdateRequest:
    def test_valid(self):
        from app.api.v1.batch_operations import BatchUpdateRequest
        req = BatchUpdateRequest(table_name="villages", ids=[1, 2], updates={"name": "x"})
        assert req.table_name == "villages"

    def test_empty_updates_raises(self):
        from app.api.v1.batch_operations import BatchUpdateRequest
        with pytest.raises(ValidationError):
            BatchUpdateRequest(table_name="villages", ids=[1], updates={})


class TestBatchDeleteRequest:
    def test_valid_default_soft_delete(self):
        from app.api.v1.batch_operations import BatchDeleteRequest
        req = BatchDeleteRequest(table_name="villages", ids=[1])
        assert req.soft_delete is True


class TestBatchExportRequest:
    def test_valid(self):
        from app.api.v1.batch_operations import BatchExportRequest
        req = BatchExportRequest(table_name="villages", ids=[1], format="csv")
        assert req.format == "csv"
