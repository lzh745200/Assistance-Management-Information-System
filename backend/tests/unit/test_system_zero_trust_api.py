"""
Tests for zero_trust.py — zero trust security API.
"""

BASE = "/api/v1/system/zero-trust"


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


class TestGetPolicyDetail:
    def test_found(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/policies/ztp-001")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == "ztp-001"

    def test_not_found(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.get(f"{BASE}/policies/nonexistent")
        assert resp.status_code == 404
