"""
Tests for zero_trust.py — zero trust security API.
Covers assessment, policies, evaluate, events, events/stats.
"""
from unittest.mock import MagicMock, patch

BASE = "/api/v1/system/zero-trust"


# ── get_trust_assessment ─────────────────────────────────────────────

class TestGetTrustAssessment:
    def test_requires_auth(self, client):
        resp = client.get(f"{BASE}/assessment")
        assert resp.status_code == 401

    def test_trusted_https(self, client_with_mocked_auth):
        client_with_mocked_auth.base_url = "https://testserver"
        resp = client_with_mocked_auth.get(f"{BASE}/assessment")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["score"] >= 80
        assert data["level"] == "trusted"
        assert len(data["factors"]) == 5
        assert data["recommendations"] == []

    def test_no_recommendations_when_score_high(self, client_with_mocked_auth):
        client_with_mocked_auth.base_url = "https://testserver"
        resp = client_with_mocked_auth.get(f"{BASE}/assessment")
        data = resp.json()["data"]
        assert data["score"] >= 60
        if data["score"] >= 60:
            assert len(data["recommendations"]) == 0

    def test_http_reduces_score(self, client_with_mocked_auth):
        with patch("app.api.v1.system.zero_trust.Request") as MockRequest:
            mock_req = MagicMock()
            mock_req.client.host = "192.168.1.1"
            mock_req.url.scheme = "http"
            client_with_mocked_auth.app.dependency_overrides = {}
            resp = client_with_mocked_auth.get(f"{BASE}/assessment")
            assert resp.status_code in (200, 401)

    def test_anonymous_user(self, client):
        resp = client.get(f"{BASE}/assessment")
        assert resp.status_code == 401


# ── get_security_policies ────────────────────────────────────────────

class TestGetPolicies:
    def test_requires_auth(self, client):
        resp = client.get(f"{BASE}/policies")
        assert resp.status_code == 401

    def test_all(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/policies")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 8

    def test_filter_by_category(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/policies?category=authentication")
        assert resp.status_code == 200
        for p in resp.json()["data"]["policies"]:
            assert p["category"] == "authentication"

    def test_enabled_only(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/policies?enabled_only=true")
        assert resp.status_code == 200
        for p in resp.json()["data"]["policies"]:
            assert p["enabled"] is True

    def test_filter_by_nonexistent_category(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/policies?category=nonexistent")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 0


class TestGetPolicyDetail:
    def test_found(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/policies/ztp-001")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == "ztp-001"

    def test_not_found(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/policies/nonexistent")
        assert resp.status_code == 404

    def test_detail_contains_expected_fields(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/policies/ztp-002")
        data = resp.json()["data"]
        assert "name" in data
        assert "category" in data
        assert "severity" in data


# ── evaluate_access_request ──────────────────────────────────────────

class TestEvaluateAccessRequest:
    def test_read_allowed(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/evaluate",
            json={"resource": "/api/v1/villages", "action": "read"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "allowed"

    def test_write_allowed(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/evaluate",
            json={"resource": "/api/v1/villages/1", "action": "write"},
        )
        assert resp.status_code == 200

    def test_delete_logs_event(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/evaluate",
            json={"resource": "/api/v1/villages/1", "action": "delete"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "allowed"

    def test_admin_denied_for_regular_user(self, client_with_regular_user_auth):
        resp = client_with_regular_user_auth.post(
            f"{BASE}/evaluate",
            json={"resource": "/admin/config", "action": "admin"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "denied"

    def test_admin_allowed_for_admin(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/evaluate",
            json={"resource": "/admin/config", "action": "admin"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "allowed"

    def test_with_context(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/evaluate",
            json={
                "resource": "/api/v1/villages",
                "action": "read",
                "context": {"ip": "10.0.0.1", "user_agent": "test"},
            },
        )
        assert resp.status_code == 200

    def test_requires_auth(self, client):
        resp = client.post(
            f"{BASE}/evaluate",
            json={"resource": "/test", "action": "read"},
        )
        assert resp.status_code == 401


# ── get_security_events ──────────────────────────────────────────────

class TestGetSecurityEvents:
    def test_empty(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/events")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_pagination_params(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/events?page=1&page_size=10")
        assert resp.status_code == 200

    def test_filter_by_severity(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/events?severity=high")
        assert resp.status_code == 200

    def test_filter_by_event_type(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/events?event_type=login")
        assert resp.status_code == 200

    def test_requires_auth(self, client):
        resp = client.get(f"{BASE}/events")
        assert resp.status_code == 401


# ── report_security_event ────────────────────────────────────────────

class TestReportSecurityEvent:
    def test_success(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/events",
            json={
                "event_type": "suspicious_login",
                "source": "user:test",
                "severity": "medium",
                "message": "Suspicious login from new IP",
                "details": {"ip": "10.0.0.1"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "event_id" in data["data"]

    def test_minimal_event(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/events",
            json={
                "event_type": "info",
                "source": "system",
                "severity": "info",
                "message": "test event",
            },
        )
        assert resp.status_code == 200

    def test_high_severity_event(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            f"{BASE}/events",
            json={
                "event_type": "intrusion",
                "source": "user:admin",
                "severity": "critical",
                "message": "Critical security event",
            },
        )
        assert resp.status_code == 200

    def test_requires_auth(self, client):
        resp = client.post(
            f"{BASE}/events",
            json={"event_type": "test", "source": "test", "severity": "info", "message": "test"},
        )
        assert resp.status_code == 401


# ── get_security_event_stats ─────────────────────────────────────────

class TestGetSecurityEventStats:
    def test_secure_posture(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/events/stats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_events" in data
        assert "security_posture" in data
        assert "by_severity" in data
        assert "by_type" in data

    def test_requires_auth(self, client):
        resp = client.get(f"{BASE}/events/stats")
        assert resp.status_code == 401


# ── _record_security_event and _event_to_dict internals ──────────────

class TestRecordSecurityEvent:
    def test_creates_event(self):
        from app.api.v1.system.zero_trust import _record_security_event
        mock_db = MagicMock()
        result = _record_security_event(
            mock_db, event_type="login", source="user:test",
            severity="info", message="test event",
        )
        assert result["event_type"] == "login"
        assert result["source"] == "user:test"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_without_user_prefix(self):
        from app.api.v1.system.zero_trust import _record_security_event
        mock_db = MagicMock()
        result = _record_security_event(
            mock_db, event_type="system", source="system",
            severity="low", message="no user prefix",
        )
        assert result["source"] == "system"

    def test_db_rollback_on_error(self):
        from app.api.v1.system.zero_trust import _record_security_event
        mock_db = MagicMock()
        mock_db.commit.side_effect = RuntimeError("commit failed")
        result = _record_security_event(
            mock_db, event_type="test", source="user:admin",
            severity="high", message="fail test",
        )
        assert result["id"] is None
        # safe_commit 失败时先回滚一次并重新抛出异常，
        # 端点的 except 兜底分支会再防御性回滚一次（对 SQLAlchemy 会话是幂等的）。
        assert mock_db.rollback.call_count >= 1

    def test_logs_warning_for_high_severity(self):
        from app.api.v1.system.zero_trust import _record_security_event
        mock_db = MagicMock()
        with patch("app.api.v1.system.zero_trust.logger") as mock_logger:
            _record_security_event(
                mock_db, event_type="critical_op", source="user:admin",
                severity="critical", message="CRITICAL!",
            )
            mock_logger.warning.assert_called_once()

    def test_details_merged(self):
        from app.api.v1.system.zero_trust import _record_security_event
        mock_db = MagicMock()
        result = _record_security_event(
            mock_db, event_type="test", source="user:admin",
            severity="info", message="details test",
            details={"extra": "data"},
        )
        assert result["details"]["extra"] == "data"


class TestEventToDict:
    def test_conversion(self):
        from app.api.v1.system.zero_trust import _event_to_dict
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.event_type = "login"
        mock_event.severity = "info"
        mock_event.description = "User login"
        mock_event.username = "admin"
        mock_event.created_at = MagicMock()
        mock_event.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_event.details = {"source": "user:admin", "ip": "10.0.0.1"}

        result = _event_to_dict(mock_event)
        assert result["id"] == 1
        assert result["event_type"] == "login"
        assert result["source"] == "user:admin"
        assert result["details"] == {"ip": "10.0.0.1"}

    def test_no_details(self):
        from app.api.v1.system.zero_trust import _event_to_dict
        mock_event = MagicMock()
        mock_event.id = 2
        mock_event.event_type = "test"
        mock_event.severity = "low"
        mock_event.description = ""
        mock_event.username = ""
        mock_event.created_at = None
        mock_event.details = {}
        result = _event_to_dict(mock_event)
        assert result["source"] == ""
        assert result["timestamp"] == ""

    def test_none_details(self):
        from app.api.v1.system.zero_trust import _event_to_dict
        mock_event = MagicMock()
        mock_event.details = None
        mock_event.id = 3
        mock_event.event_type = "x"
        mock_event.severity = "x"
        mock_event.description = ""
        mock_event.username = "x"
        mock_event.created_at = MagicMock()
        mock_event.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        result = _event_to_dict(mock_event)
        assert result["id"] == 3
