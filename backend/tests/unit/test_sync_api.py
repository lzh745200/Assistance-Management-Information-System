"""Tests for app.api.v1.sync — 100% coverage."""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def client():
    from app.api.v1 import deps
    from app.core.database import get_db
    app = FastAPI()
    mock_user = MagicMock()
    mock_user.id = 1
    app.dependency_overrides[deps.get_current_user] = lambda: mock_user
    mock_db = MagicMock()
    mock_db.query.return_value.order_by.return_value.first.return_value = None
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    app.dependency_overrides[get_db] = lambda: mock_db
    from app.api.v1.sync import router
    app.include_router(router)
    return TestClient(app)


class TestGetSyncStatus:
    def test_returns_sync_status(self, client):
        resp = client.get("/sync/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["sync_enabled"] is True
        assert data["data"]["sync_status"] == "idle"
        assert data["data"]["pending_changes"] == 0
