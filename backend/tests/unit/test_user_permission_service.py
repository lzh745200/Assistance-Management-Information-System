"""Tests for UserPermissionService — 100% code coverage."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.error_handler import BusinessLogicError
from app.services.user_permission_service import UserPermissionService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return UserPermissionService(db)


def _make_user(**kwargs):
    defaults = dict(
        id=1, username="testuser", full_name="Test User",
        email="test@example.com", role="operator", is_active=True,
        is_superuser=False, organization_id=10, data_scope="org",
    )
    defaults.update(kwargs)
    return MagicMock(**defaults)


def _make_org(**kwargs):
    attrs = dict(
        id=1, name="TestOrg", code="ORG001", parent_id=None,
        level="level_1", type="unit", org_type="department",
        sort_order=0, description="", contact_person="", contact_phone="",
        is_active=True,
    )
    attrs.update(kwargs)
    mock = MagicMock()
    for k, v in attrs.items():
        setattr(mock, k, v)
    return mock


def _make_user_org(**kwargs):
    defaults = dict(
        id=1, user_id=1, organization_id=10, role="member",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return MagicMock(**defaults)


class TestGetUser:
    def test_returns_user(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = "user"
        assert service._get_user(1) == "user"

    def test_returns_none(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert service._get_user(1) is None


class TestAssignUserToOrganization:
    def test_user_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(BusinessLogicError, match="用户不存在"):
            service.assign_user_to_organization(999, 1)

    def test_org_not_found(self, service, db):
        user = _make_user()
        db.query.return_value.filter.return_value.first.side_effect = [user, None]
        with pytest.raises(BusinessLogicError, match="组织不存在"):
            service.assign_user_to_organization(1, 999)

    def test_existing_association_updated(self, service, db):
        user = _make_user()
        org = _make_org()
        existing = _make_user_org(role="member")
        db.query.return_value.filter.return_value.first.side_effect = [user, org, existing]
        result = service.assign_user_to_organization(1, 10, role="admin", is_primary=False)
        assert result.role == "admin"
        db.commit.assert_called_once()

    def test_new_association_without_primary(self, service, db):
        user = _make_user()
        org = _make_org()
        db.query.return_value.filter.return_value.first.side_effect = [user, org, None]
        result = service.assign_user_to_organization(1, 10, role="viewer")
        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result.role == "viewer"

    def test_new_association_with_primary(self, service, db):
        user = _make_user()
        org = _make_org()
        db.query.return_value.filter.return_value.first.side_effect = [user, org, None]
        result = service.assign_user_to_organization(1, 10, role="admin", is_primary=True)
        assert user.organization_id == 10
        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result.role == "admin"


class TestRemoveUserFromOrganization:
    def test_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert service.remove_user_from_organization(1, 999) is False

    def test_remove_non_primary(self, service, db):
        uo = _make_user_org()
        user = _make_user(organization_id=20)
        db.query.return_value.filter.return_value.first.side_effect = [uo, user]
        assert service.remove_user_from_organization(1, 10) is True
        db.delete.assert_called_once_with(uo)
        db.commit.assert_called_once()

    def test_remove_primary_clears_user_org(self, service, db):
        uo = _make_user_org(organization_id=10)
        user = _make_user(organization_id=10)
        db.query.return_value.filter.return_value.first.side_effect = [uo, user]
        assert service.remove_user_from_organization(1, 10) is True
        assert user.organization_id is None
        db.delete.assert_called_once_with(uo)
        db.commit.assert_called_once()


class TestGetUserOrganizations:
    def test_user_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert service.get_user_organizations(1) == []

    def test_returns_orgs(self, service, db):
        user = _make_user()
        db.query.return_value.filter.return_value.first.return_value = user
        uo1 = _make_user_org(organization_id=10, role="admin")
        org1 = _make_org(id=10, name="OrgA")
        uo2 = _make_user_org(organization_id=20, role="member")
        org2 = _make_org(id=20, name="OrgB")
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (uo1, org1),
            (uo2, org2),
        ]
        result = service.get_user_organizations(1)
        assert len(result) == 2
        assert result[0]["name"] == "OrgA"
        assert result[0]["role"] == "admin"
        assert result[0]["is_primary"] is True
        assert result[1]["is_primary"] is False


class TestGetOrganizationUsers:
    def test_without_children(self, service, db):
        u_org = _make_user_org()
        usr = _make_user()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (u_org, usr),
        ]
        result = service.get_organization_users(10)
        assert len(result) == 1
        assert result[0]["username"] == "testuser"

    def test_with_children(self, service, db):
        service._get_child_organization_ids = MagicMock(return_value=[20, 30])
        u_org = _make_user_org()
        usr = _make_user()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (u_org, usr),
        ]
        result = service.get_organization_users(10, include_children=True)
        assert len(result) == 1

    def test_with_children_skips_none_user(self, service, db):
        service._get_child_organization_ids = MagicMock(return_value=[])
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (_make_user_org(), None),
        ]
        result = service.get_organization_users(10, include_children=True)
        assert len(result) == 0


class TestGetChildOrganizationIds:
    def test_no_children(self, service, db):
        db.query.return_value.filter.return_value.all.return_value = []
        assert service._get_child_organization_ids(1) == []

    def test_recursive(self, service, db):
        child1 = _make_org(id=2, parent_id=1)
        child2 = _make_org(id=3, parent_id=2)
        child_of_child2 = _make_org(id=4, parent_id=3)
        grandchild = _make_org(id=5, parent_id=4)

        db.query.return_value.filter.return_value.all.side_effect = [
            [child1],
            [child2],
            [child_of_child2],
            [grandchild],
            [],
        ]
        result = service._get_child_organization_ids(1)
        assert result == [2, 3, 4, 5]


class TestAssignRoleToUser:
    def test_user_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(BusinessLogicError, match="用户不存在"):
            service.assign_role_to_user(999, "role-1")

    def test_role_not_found(self, service, db):
        user = _make_user()
        db.query.return_value.filter.return_value.first.side_effect = [user, None]
        with pytest.raises(BusinessLogicError, match="角色不存在"):
            service.assign_role_to_user(1, "role-999")

    def test_existing_updated(self, service, db):
        user = _make_user()
        role = MagicMock(id="r1")
        existing = MagicMock(user_id=1, role_id="r1", granted_by=None, expires_at=None)
        db.query.return_value.filter.return_value.first.side_effect = [user, role, existing]
        result = service.assign_role_to_user(1, "r1", granted_by=99)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(existing)
        assert result.granted_by == 99

    def test_new(self, service, db):
        user = _make_user()
        role = MagicMock(id="r2")
        db.query.return_value.filter.return_value.first.side_effect = [user, role, None]
        result = service.assign_role_to_user(1, "r2", granted_by=99)
        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result.user_id == 1
        assert result.role_id == "r2"


class TestRemoveRoleFromUser:
    def test_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert service.remove_role_from_user(1, "r1") is False

    def test_removed(self, service, db):
        ur = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = ur
        assert service.remove_role_from_user(1, "r1") is True
        db.delete.assert_called_once_with(ur)
        db.commit.assert_called_once()


class TestGetUserRoles:
    def test_empty(self, service, db):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = []
        assert service.get_user_roles(1) == []

    def test_returns_roles(self, service, db):
        mock_role = MagicMock()
        mock_role.id = "r1"
        mock_role.name = "admin"
        mock_role.description = "Admin"
        mock_role.is_system = True
        ur = MagicMock(role=mock_role, granted_by=1, expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc))
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [ur]
        result = service.get_user_roles(1)
        assert len(result) == 1
        assert result[0]["name"] == "admin"
        assert result[0]["expires_at"] is not None

    def test_skips_none_role(self, service, db):
        ur_no_role = MagicMock(role=None)
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [ur_no_role]
        assert service.get_user_roles(1) == []

    def test_expires_at_none(self, service, db):
        mock_role = MagicMock()
        mock_role.id = "r1"
        mock_role.name = "viewer"
        mock_role.description = "Viewer"
        mock_role.is_system = False
        ur = MagicMock(role=mock_role, granted_by=None, expires_at=None)
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [ur]
        result = service.get_user_roles(1)
        assert result[0]["expires_at"] is None


class TestGrantPermissionToUser:
    def test_user_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(BusinessLogicError, match="用户不存在"):
            service.grant_permission_to_user(999, "perm:read")

    def test_existing_updated(self, service, db):
        user = _make_user()
        existing = MagicMock(permission="perm:read", granted_by=None, expires_at=None)
        db.query.return_value.filter.return_value.first.side_effect = [user, existing]
        result = service.grant_permission_to_user(1, "perm:read", granted_by=99)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(existing)
        assert result.granted_by == 99

    def test_new(self, service, db):
        user = _make_user()
        db.query.return_value.filter.return_value.first.side_effect = [user, None]
        result = service.grant_permission_to_user(1, "perm:write", granted_by=99)
        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result.permission == "perm:write"


class TestRevokePermissionFromUser:
    def test_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert service.revoke_permission_from_user(1, "perm:read") is False

    def test_revoked(self, service, db):
        up = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = up
        assert service.revoke_permission_from_user(1, "perm:read") is True
        db.delete.assert_called_once_with(up)
        db.commit.assert_called_once()


class TestGetUserPermissions:
    def test_direct_permission_active(self, service, db):
        up_active = MagicMock(permission="perm:read", expires_at=None)
        db.query.return_value.filter.return_value.all.side_effect = [
            [up_active],
            [],
            [],
        ]
        result = service.get_user_permissions(1)
        assert "perm:read" in result

    def test_direct_permission_expired(self, service, db):
        up_expired = MagicMock(
            permission="perm:old",
            expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        db.query.return_value.filter.return_value.all.side_effect = [
            [up_expired],
            [],
            [],
        ]
        result = service.get_user_permissions(1)
        assert "perm:old" not in result

    def test_role_permission_active(self, service, db):
        db.query.return_value.filter.return_value.all.side_effect = [
            [],
            [MagicMock(role_id="r1", expires_at=None)],
            [MagicMock(permission="role:perm1")],
        ]
        result = service.get_user_permissions(1)
        assert "role:perm1" in result

    def test_role_permission_expired(self, service, db):
        expired_ur = MagicMock(
            role_id="r1",
            expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        db.query.return_value.filter.return_value.all.side_effect = [
            [],
            [expired_ur],
            [],
        ]
        result = service.get_user_permissions(1)
        assert len(result) == 0

    def test_role_permission_with_expires_at_none_and_role_perms_empty(self, service, db):
        ur_no_expiry = MagicMock(role_id="r2", expires_at=None)
        db.query.return_value.filter.return_value.all.side_effect = [
            [],
            [ur_no_expiry],
            [],
        ]
        result = service.get_user_permissions(1)
        assert result == []


class TestCheckUserPermission:
    def test_has_permission(self, service, db):
        service.get_user_permissions = MagicMock(return_value=["perm:read"])
        assert service.check_user_permission(1, "perm:read") is True

    def test_no_permission(self, service, db):
        service.get_user_permissions = MagicMock(return_value=["perm:read"])
        assert service.check_user_permission(1, "perm:write") is False


class TestCheckUserDataScope:
    def test_user_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert service.check_user_data_scope(999) is False

    def test_superuser(self, service, db):
        user = _make_user(is_superuser=True)
        db.query.return_value.filter.return_value.first.return_value = user
        assert service.check_user_data_scope(1, 999) is True

    def test_no_target_org_has_org(self, service, db):
        user = _make_user(organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        assert service.check_user_data_scope(1) is True

    def test_no_target_org_no_org(self, service, db):
        user = _make_user(organization_id=None)
        db.query.return_value.filter.return_value.first.return_value = user
        assert service.check_user_data_scope(1) is False

    def test_data_scope_all(self, service, db):
        user = _make_user(data_scope="all")
        db.query.return_value.filter.return_value.first.return_value = user
        assert service.check_user_data_scope(1, 999) is True

    def test_data_scope_org_match(self, service, db):
        user = _make_user(data_scope="org", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        assert service.check_user_data_scope(1, 10) is True

    def test_data_scope_org_no_match(self, service, db):
        user = _make_user(data_scope="org", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        assert service.check_user_data_scope(1, 20) is False

    def test_data_scope_org_children_direct(self, service, db):
        user = _make_user(data_scope="org_children", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        assert service.check_user_data_scope(1, 10) is True

    def test_data_scope_org_children_via_child(self, service, db):
        user = _make_user(data_scope="org_children", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        service._get_child_organization_ids = MagicMock(return_value=[20, 30])
        assert service.check_user_data_scope(1, 20) is True

    def test_data_scope_org_children_no_match(self, service, db):
        user = _make_user(data_scope="org_children", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        service._get_child_organization_ids = MagicMock(return_value=[20, 30])
        assert service.check_user_data_scope(1, 40) is False

    def test_data_scope_self(self, service, db):
        user = _make_user(data_scope="self")
        db.query.return_value.filter.return_value.first.return_value = user
        assert service.check_user_data_scope(1, 10) is False

    def test_data_scope_unknown(self, service, db):
        user = _make_user(data_scope="unknown_value")
        db.query.return_value.filter.return_value.first.return_value = user
        assert service.check_user_data_scope(1, 10) is False


class TestGetOrganizationTree:
    def test_user_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert service.get_organization_tree(user_id=1) == []

    def test_superuser_no_parent(self, service, db):
        user = _make_user(is_superuser=True)
        db.query.return_value.filter.return_value.first.return_value = user
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = service.get_organization_tree(user_id=1)
        assert result == []

    def test_data_scope_org_parent_mismatch(self, service, db):
        user = _make_user(data_scope="org", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        result = service.get_organization_tree(parent_id=20, user_id=1)
        assert result == []

    def test_data_scope_org_parent_match(self, service, db):
        user = _make_user(data_scope="org", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = service.get_organization_tree(parent_id=10, user_id=1)
        assert result == []

    def test_data_scope_org_children_parent_allowed(self, service, db):
        user = _make_user(data_scope="org_children", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        service._get_child_organization_ids = MagicMock(return_value=[20, 30])
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = service.get_organization_tree(parent_id=20, user_id=1)
        assert result == []

    def test_data_scope_org_children_parent_not_allowed(self, service, db):
        user = _make_user(data_scope="org_children", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        service._get_child_organization_ids = MagicMock(return_value=[20, 30])
        result = service.get_organization_tree(parent_id=40, user_id=1)
        assert result == []

    def test_data_scope_self(self, service, db):
        user = _make_user(data_scope="self")
        db.query.return_value.filter.return_value.first.return_value = user
        result = service.get_organization_tree(user_id=1)
        assert result == []

    def test_no_user_id(self, service, db):
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = service.get_organization_tree()
        assert result == []

    def test_non_superuser_data_scope_org_no_parent(self, service, db):
        user = _make_user(data_scope="org", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = service.get_organization_tree(user_id=1)
        assert result == []

    def test_tree_building_iterates_orgs(self, service, db):
        user = _make_user(is_superuser=True)
        db.query.return_value.filter.return_value.first.return_value = user
        org = _make_org(id=5)
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [org]
        original = service.get_organization_tree
        depth = [0]

        def side_effect(parent_id=None, user_id=None):
            if depth[0] > 0:
                return []
            depth[0] += 1
            try:
                return original(parent_id=parent_id, user_id=user_id)
            finally:
                depth[0] -= 1

        with patch.object(service, "get_organization_tree", side_effect=side_effect):
            result = service.get_organization_tree(user_id=1)
        assert len(result) == 1
        assert result[0]["id"] == 5
        assert result[0]["has_children"] is False


class TestGetUserAccessibleOrganizations:
    def test_user_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert service.get_user_accessible_organizations(1) == []

    def test_is_superuser_field(self, service, db):
        user = _make_user(is_superuser=True)
        db.query.return_value.filter.return_value.first.return_value = user
        db.query.return_value.filter.return_value.all.return_value = [MagicMock(id=1), MagicMock(id=2)]
        result = service.get_user_accessible_organizations(1)
        assert result == [1, 2]

    def test_is_superuser_function(self, service, db):
        user = _make_user(is_superuser=True, data_scope="self")
        db.query.return_value.filter.return_value.first.return_value = user
        db.query.return_value.filter.return_value.all.return_value = [MagicMock(id=3)]
        result = service.get_user_accessible_organizations(1)
        assert result == [3]

    def test_data_scope_all(self, service, db):
        user = _make_user(data_scope="all")
        db.query.return_value.filter.return_value.first.return_value = user
        db.query.return_value.filter.return_value.all.return_value = [MagicMock(id=5)]
        result = service.get_user_accessible_organizations(1)
        assert result == [5]

    def test_data_scope_org_with_org(self, service, db):
        user = _make_user(data_scope="org", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        result = service.get_user_accessible_organizations(1)
        assert result == [10]

    def test_data_scope_org_no_org(self, service, db):
        user = _make_user(data_scope="org", organization_id=None)
        db.query.return_value.filter.return_value.first.return_value = user
        result = service.get_user_accessible_organizations(1)
        assert result == []

    def test_data_scope_org_children_with_org(self, service, db):
        user = _make_user(data_scope="org_children", organization_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        service._get_child_organization_ids = MagicMock(return_value=[20, 30])
        result = service.get_user_accessible_organizations(1)
        assert result == [10, 20, 30]

    def test_data_scope_org_children_no_org(self, service, db):
        user = _make_user(data_scope="org_children", organization_id=None)
        db.query.return_value.filter.return_value.first.return_value = user
        result = service.get_user_accessible_organizations(1)
        assert result == []

    def test_data_scope_self(self, service, db):
        user = _make_user(data_scope="self")
        db.query.return_value.filter.return_value.first.return_value = user
        result = service.get_user_accessible_organizations(1)
        assert result == []

    def test_unknown_data_scope(self, service, db):
        user = _make_user(data_scope="invalid")
        db.query.return_value.filter.return_value.first.return_value = user
        result = service.get_user_accessible_organizations(1)
        assert result == []
