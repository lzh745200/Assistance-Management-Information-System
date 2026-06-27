"""
Tests for user_permissions.py — legacy user permissions management API.
Covers all 14 endpoints: org management, role management, permission management, org tree.
"""
from unittest.mock import MagicMock, patch
import pytest

BASE = "/api/v1/user-permissions"


# ── assign_user_to_organization ─────────────────────────────────────

class TestAssignOrganization:
    def test_requires_auth(self, client):
        resp = client.post(f"{BASE}/assign-organization", json={"user_id": 2, "organization_id": 1})
        assert resp.status_code == 401

    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_user_org = MagicMock()
            mock_user_org.user_id = 2
            mock_user_org.organization_id = 1
            mock_user_org.role = "member"
            mock_svc.assign_user_to_organization.return_value = mock_user_org
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.post(
                f"{BASE}/assign-organization",
                json={"user_id": 2, "organization_id": 1, "role": "member", "is_primary": True},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["data"]["user_id"] == 2

    def test_no_permission(self, client_with_regular_user_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_regular_user_auth.post(
                f"{BASE}/assign-organization",
                json={"user_id": 2, "organization_id": 1},
            )
            assert resp.status_code == 403

    def test_business_logic_error(self, client_with_mocked_auth):
        from app.core.error_handler import BusinessLogicError
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_svc.assign_user_to_organization.side_effect = BusinessLogicError("already exists")
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.post(
                f"{BASE}/assign-organization",
                json={"user_id": 2, "organization_id": 1},
            )
            assert resp.status_code == 400


# ── remove_user_from_organization ──────────────────────────────────

class TestRemoveOrganization:
    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_svc.remove_user_from_organization.return_value = True
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.delete(
                f"{BASE}/remove-organization?user_id=2&organization_id=1",
            )
            assert resp.status_code == 200
            assert resp.json()["success"] is True

    def test_not_found(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_svc.remove_user_from_organization.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.delete(
                f"{BASE}/remove-organization?user_id=999&organization_id=999",
            )
            assert resp.status_code == 404

    def test_no_permission(self, client_with_regular_user_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_regular_user_auth.delete(
                f"{BASE}/remove-organization?user_id=2&organization_id=1",
            )
            assert resp.status_code == 403


# ── get_user_organizations ─────────────────────────────────────────

class TestGetUserOrganizations:
    def test_own_orgs(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.get_user_organizations.return_value = [{"id": 1, "name": "Org1"}]
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.get(f"{BASE}/user-organizations/1")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["count"] == 1

    def test_other_user_no_permission(self, client_with_regular_user_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_regular_user_auth.get(f"{BASE}/user-organizations/999")
            assert resp.status_code == 403


# ── get_organization_users ─────────────────────────────────────────

class TestGetOrganizationUsers:
    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_svc.get_organization_users.return_value = [{"id": 1, "name": "User1"}]
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.get(f"{BASE}/organization-users/1")
            assert resp.status_code == 200
            assert resp.json()["count"] == 1

    def test_with_children(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_svc.get_organization_users.return_value = [{"id": 1}, {"id": 2}]
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.get(f"{BASE}/organization-users/1?include_children=true")
            assert resp.status_code == 200

    def test_no_permission(self, client_with_regular_user_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = False
            mock_svc.check_user_data_scope.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_regular_user_auth.get(f"{BASE}/organization-users/1")
            assert resp.status_code == 403


# ── assign_role_to_user ────────────────────────────────────────────

class TestAssignRole:
    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_user_role = MagicMock()
            mock_user_role.user_id = 2
            mock_user_role.role_id = "admin"
            mock_svc.assign_role_to_user.return_value = mock_user_role
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.post(
                f"{BASE}/assign-role",
                json={"user_id": 2, "role_id": "admin"},
            )
            assert resp.status_code == 200
            assert resp.json()["data"]["role_id"] == "admin"

    def test_with_expiry(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_user_role = MagicMock()
            mock_user_role.user_id = 2
            mock_user_role.role_id = "viewer"
            mock_svc.assign_role_to_user.return_value = mock_user_role
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.post(
                f"{BASE}/assign-role",
                json={"user_id": 2, "role_id": "viewer", "expires_at": "2025-12-31T23:59:59"},
            )
            assert resp.status_code == 200

    def test_no_permission(self, client_with_regular_user_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_regular_user_auth.post(
                f"{BASE}/assign-role",
                json={"user_id": 2, "role_id": "admin"},
            )
            assert resp.status_code == 403

    def test_business_logic_error(self, client_with_mocked_auth):
        from app.core.error_handler import BusinessLogicError
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_svc.assign_role_to_user.side_effect = BusinessLogicError("conflict")
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.post(
                f"{BASE}/assign-role",
                json={"user_id": 2, "role_id": "admin"},
            )
            assert resp.status_code == 400


# ── remove_role_from_user ──────────────────────────────────────────

class TestRemoveRole:
    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_svc.remove_role_from_user.return_value = True
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.delete(f"{BASE}/remove-role?user_id=2&role_id=admin")
            assert resp.status_code == 200

    def test_not_found(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_svc.remove_role_from_user.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.delete(f"{BASE}/remove-role?user_id=2&role_id=nonexistent")
            assert resp.status_code == 404


# ── get_user_roles ─────────────────────────────────────────────────

class TestGetUserRoles:
    def test_own_roles(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.get_user_roles.return_value = [{"role_id": "admin"}]
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.get(f"{BASE}/user-roles/1")
            assert resp.status_code == 200
            assert resp.json()["count"] == 1

    def test_other_user_no_permission(self, client_with_regular_user_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_regular_user_auth.get(f"{BASE}/user-roles/999")
            assert resp.status_code == 403


# ── grant_permission_to_user ───────────────────────────────────────

class TestGrantPermission:
    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_perm = MagicMock()
            mock_perm.user_id = 2
            mock_perm.permission = "villages:write"
            mock_svc.grant_permission_to_user.return_value = mock_perm
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.post(
                f"{BASE}/grant-permission",
                json={"user_id": 2, "permission": "villages:write"},
            )
            assert resp.status_code == 200
            assert resp.json()["data"]["permission"] == "villages:write"

    def test_with_expiry(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_perm = MagicMock()
            mock_perm.user_id = 2
            mock_perm.permission = "temp:access"
            mock_svc.grant_permission_to_user.return_value = mock_perm
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.post(
                f"{BASE}/grant-permission",
                json={"user_id": 2, "permission": "temp:access", "expires_at": "2025-06-01T00:00:00"},
            )
            assert resp.status_code == 200

    def test_no_permission(self, client_with_regular_user_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_regular_user_auth.post(
                f"{BASE}/grant-permission",
                json={"user_id": 2, "permission": "villages:write"},
            )
            assert resp.status_code == 403


# ── revoke_permission_from_user ────────────────────────────────────

class TestRevokePermission:
    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_svc.revoke_permission_from_user.return_value = True
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.delete(
                f"{BASE}/revoke-permission?user_id=2&permission=villages:write",
            )
            assert resp.status_code == 200

    def test_not_found(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            mock_svc.revoke_permission_from_user.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.delete(
                f"{BASE}/revoke-permission?user_id=2&permission=nonexistent",
            )
            assert resp.status_code == 404


# ── get_user_permissions ───────────────────────────────────────────

class TestGetUserPermissions:
    def test_own_permissions(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.get_user_permissions.return_value = [{"permission": "read"}]
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.get(f"{BASE}/user-permissions/1")
            assert resp.status_code == 200
            assert resp.json()["count"] == 1

    def test_other_user_no_permission(self, client_with_regular_user_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = False
            MockService.return_value = mock_svc
            resp = client_with_regular_user_auth.get(f"{BASE}/user-permissions/999")
            assert resp.status_code == 403


# ── check_user_permission ──────────────────────────────────────────

class TestCheckPermission:
    def test_own_check(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.post(
                f"{BASE}/check-permission",
                json={"user_id": 1, "permission": "read"},
            )
            assert resp.status_code == 200
            assert resp.json()["has_permission"] is True

    def test_other_user_no_permission(self, client_with_regular_user_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            MockService.return_value = mock_svc
            resp = client_with_regular_user_auth.post(
                f"{BASE}/check-permission",
                json={"user_id": 999, "permission": "read"},
            )
            assert resp.status_code == 403

    def test_other_user_as_admin(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.check_user_permission.return_value = True
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.post(
                f"{BASE}/check-permission",
                json={"user_id": 999, "permission": "admin:access"},
            )
            assert resp.status_code == 200
            assert resp.json()["has_permission"] is True


# ── organization-tree ──────────────────────────────────────────────

class TestOrganizationTree:
    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.get_organization_tree.return_value = [{"id": 1, "name": "Root"}]
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.get(f"{BASE}/organization-tree")
            assert resp.status_code == 200
            assert resp.json()["success"] is True

    def test_with_parent_id(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.get_organization_tree.return_value = [{"id": 2, "name": "Child"}]
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.get(f"{BASE}/organization-tree?parent_id=1")
            assert resp.status_code == 200


# ── accessible-organizations ───────────────────────────────────────

class TestAccessibleOrganizations:
    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.get_user_accessible_organizations.return_value = [1, 2, 3]
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.get(f"{BASE}/accessible-organizations")
            assert resp.status_code == 200
            assert resp.json()["count"] == 3


# ── root (current user permission info) ────────────────────────────

class TestUserPermissionsRoot:
    def test_success(self, client_with_mocked_auth):
        with patch("app.api.v1.user_permissions.UserPermissionService") as MockService:
            mock_svc = MagicMock()
            mock_svc.get_user_accessible_organizations.return_value = [1]
            MockService.return_value = mock_svc
            resp = client_with_mocked_auth.get(f"{BASE}")
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["user_id"] == 1
            assert data["role"] == "admin"

    def test_requires_auth(self, client):
        resp = client.get(f"{BASE}")
        assert resp.status_code == 401
