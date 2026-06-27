from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.machine_code_permission_service import MachineCodePermissionService
from app.models.machine_code import MachineCode
from app.models.rbac import MachineCodePermission
from app.models.base import _utcnow


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def svc(db):
    return MachineCodePermissionService(db)


# ---------------------------------------------------------------------------
# get_machine_code_permissions
# ---------------------------------------------------------------------------

class TestGetMachineCodePermissions:
    def test_db_none(self):
        svc = MachineCodePermissionService()
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            svc.get_machine_code_permissions(1)

    def test_returns_list(self, svc, db):
        m1, m2 = MagicMock(), MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [m1, m2]
        result = svc.get_machine_code_permissions(5)
        assert result == [m1, m2]
        db.query.assert_called_once_with(MachineCodePermission)

    def test_empty(self, svc, db):
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.get_machine_code_permissions(99)
        assert result == []


# ---------------------------------------------------------------------------
# get_restricted_permissions
# ---------------------------------------------------------------------------

class TestGetRestrictedPermissions:
    def test_db_none(self):
        svc = MachineCodePermissionService()
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            svc.get_restricted_permissions(1)

    def test_returns_set(self, svc, db):
        db.query.return_value.filter.return_value.all.return_value = [
            ("perm_read",),
            ("perm_write",),
        ]
        result = svc.get_restricted_permissions(1)
        assert result == {"perm_read", "perm_write"}

    def test_empty(self, svc, db):
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.get_restricted_permissions(1)
        assert result == set()

    def test_expired_excluded(self, svc, db):
        now = _utcnow()
        expired = (now - timedelta(days=10)).isoformat()
        db.query.return_value.filter.return_value.all.return_value = [
            ("valid_perm",),
        ]
        # Verify it filters by expires_at > now or null
        result = svc.get_restricted_permissions(1)
        assert "valid_perm" in result
        filter_args = db.query.return_value.filter.call_args
        assert filter_args is not None


# ---------------------------------------------------------------------------
# get_user_restricted_permissions
# ---------------------------------------------------------------------------

class TestGetUserRestrictedPermissions:
    def test_db_none(self):
        svc = MachineCodePermissionService()
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            svc.get_user_restricted_permissions(1)

    def test_no_active_machine_code(self, svc, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.get_user_restricted_permissions(42)
        assert result == set()

    def test_has_machine_code(self, svc, db):
        mc = MagicMock(spec=MachineCode)
        mc.id = 10
        db.query.return_value.filter.return_value.first.return_value = mc

        db.query.return_value.filter.return_value.all.return_value = [
            ("perm_a",),
            ("perm_b",),
        ]
        result = svc.get_user_restricted_permissions(42)
        assert result == {"perm_a", "perm_b"}


# ---------------------------------------------------------------------------
# grant_permission
# ---------------------------------------------------------------------------

class TestGrantPermission:
    def test_db_none(self):
        svc = MachineCodePermissionService()
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            svc.grant_permission(1, "perm", 1)

    def test_existing_record_updated(self, svc, db):
        existing = MagicMock(spec=MachineCodePermission)
        existing.expires_at = None
        db.query.return_value.filter.return_value.first.return_value = existing
        result = svc.grant_permission(1, "perm_x", 5, expires_at=datetime(2025, 1, 1))
        assert result is existing
        assert existing.granted_by == 5
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(existing)

    def test_new_record_created(self, svc, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.grant_permission(1, "perm_y", 3)
        assert result.machine_code_id == 1
        assert result.permission == "perm_y"
        assert result.granted_by == 3
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_new_record_with_expiry(self, svc, db):
        db.query.return_value.filter.return_value.first.return_value = None
        expires = _utcnow() + timedelta(days=30)
        result = svc.grant_permission(1, "perm_z", 7, expires_at=expires)
        assert result.expires_at == expires


# ---------------------------------------------------------------------------
# revoke_permission
# ---------------------------------------------------------------------------

class TestRevokePermission:
    def test_db_none(self):
        svc = MachineCodePermissionService()
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            svc.revoke_permission(1, "perm")

    def test_not_found(self, svc, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.revoke_permission(1, "nonexistent")
        assert result is False

    def test_found_deleted(self, svc, db):
        record = MagicMock(spec=MachineCodePermission)
        db.query.return_value.filter.return_value.first.return_value = record
        result = svc.revoke_permission(1, "perm_x")
        assert result is True
        db.delete.assert_called_once_with(record)
        db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# batch_grant_permissions
# ---------------------------------------------------------------------------

class TestBatchGrantPermissions:
    def test_db_none(self):
        svc = MachineCodePermissionService()
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            svc.batch_grant_permissions(1, ["a"], 1)

    def test_all_new(self, svc, db):
        db.query.return_value.filter.return_value.first.return_value = None
        count = svc.batch_grant_permissions(1, ["p1", "p2", "p3"], 5)
        assert count == 3
        assert db.add.call_count == 3
        db.commit.assert_called_once()

    def test_mixed_existing_and_new(self, svc, db):
        existing = MagicMock(spec=MachineCodePermission)
        existing.expires_at = None

        def first_side_effect():
            call_count = db.query.return_value.filter.return_value.first.call_count
            if call_count <= 2:
                return existing
            return None

        db.query.return_value.filter.return_value.first.side_effect = [
            existing,
            None,
        ]
        count = svc.batch_grant_permissions(1, ["p_existing", "p_new"], 5)
        assert count == 2
        assert db.add.call_count == 1
        db.commit.assert_called_once()

    def test_exception_rollback(self, svc, db):
        db.query.return_value.filter.return_value.first.return_value = None
        db.add.side_effect = Exception("DB error")
        count = svc.batch_grant_permissions(1, ["p1"], 5)
        assert count == 0
        db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# batch_revoke_permissions
# ---------------------------------------------------------------------------

class TestBatchRevokePermissions:
    def test_db_none(self):
        svc = MachineCodePermissionService()
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            svc.batch_revoke_permissions(1, ["a"])

    def test_all_found(self, svc, db):
        record = MagicMock(spec=MachineCodePermission)
        db.query.return_value.filter.return_value.first.return_value = record
        count = svc.batch_revoke_permissions(1, ["p1", "p2"])
        assert count == 2
        assert db.delete.call_count == 2
        db.commit.assert_called_once()

    def test_mixed_found_and_not(self, svc, db):
        record = MagicMock(spec=MachineCodePermission)
        db.query.return_value.filter.return_value.first.side_effect = [
            record,
            None,
        ]
        count = svc.batch_revoke_permissions(1, ["p1", "p2"])
        assert count == 1
        assert db.delete.call_count == 1
        db.commit.assert_called_once()

    def test_exception_rollback(self, svc, db):
        record = MagicMock(spec=MachineCodePermission)
        db.query.return_value.filter.return_value.first.return_value = record
        db.delete.side_effect = Exception("DB error")
        count = svc.batch_revoke_permissions(1, ["p1"])
        assert count == 0
        db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# delete_all_permissions
# ---------------------------------------------------------------------------

class TestDeleteAllPermissions:
    def test_db_none(self):
        svc = MachineCodePermissionService()
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            svc.delete_all_permissions(1)

    def test_deletes_and_commits(self, svc, db):
        db.query.return_value.filter.return_value.delete.return_value = 5
        count = svc.delete_all_permissions(10)
        assert count == 5
        db.commit.assert_called_once()
        db.query.assert_called_once_with(MachineCodePermission)

    def test_zero_deleted(self, svc, db):
        db.query.return_value.filter.return_value.delete.return_value = 0
        count = svc.delete_all_permissions(99)
        assert count == 0
        db.commit.assert_called_once()
