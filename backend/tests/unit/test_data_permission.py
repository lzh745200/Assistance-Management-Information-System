"""Tests for app.core.data_permission — 100% coverage."""

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.core.data_permission import (
    DataScope,
    get_data_scope,
    apply_scope_to_query,
    check_record_access,
    filter_by_data_scope,
    apply_data_scope,
    require_data_permission,
)


# ---------------------------------------------------------------------------
# get_data_scope
# ---------------------------------------------------------------------------

class TestGetDataScope:
    def test_none_user_returns_own(self):
        assert get_data_scope(None) == DataScope.OWN

    def test_superuser_returns_all(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = True
        user.role = "user"
        assert get_data_scope(user) == DataScope.ALL

    def test_super_admin_role_returns_all(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "super_admin"
        assert get_data_scope(user) == DataScope.ALL

    def test_admin_role_returns_own_dept(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "admin"
        assert get_data_scope(user) == DataScope.OWN_DEPT

    def test_manager_role_returns_own_dept(self):
        user = MagicMock(); user.is_superuser = False
        user.role = "manager"
        assert get_data_scope(user) == DataScope.OWN_DEPT

    def test_approval_leader_returns_own_dept(self):
        user = MagicMock(); user.is_superuser = False
        user.role = "approval_leader"
        assert get_data_scope(user) == DataScope.OWN_DEPT

    def test_regular_user_returns_own(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "viewer"
        assert get_data_scope(user) == DataScope.OWN

    def test_no_role_returns_own(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        del user.role
        assert get_data_scope(user) == DataScope.OWN


# ---------------------------------------------------------------------------
# apply_scope_to_query
# ---------------------------------------------------------------------------

class TestApplyScopeToQuery:
    def test_all_scope_returns_unchanged(self):
        query = MagicMock()
        model = MagicMock()
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = True
        user.role = "super_admin"
        result = apply_scope_to_query(query, model, user)
        assert result is query

    def test_own_dept_filters_by_department(self):
        query = MagicMock()
        query.filter.return_value = "dept_filtered"

        class SimpleModel:
            department_id = "dept_col"

        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "admin"
        user.department_id = 42
        result = apply_scope_to_query(query, SimpleModel, user)
        query.filter.assert_called_once()
        assert result == "dept_filtered"

    def test_own_dept_no_department_returns_unfiltered(self):
        query = MagicMock()

        class SimpleModel:
            created_by = "owner_col"

        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "admin"
        user.department_id = None
        user.id = 5
        result = apply_scope_to_query(query, SimpleModel, user)
        # OWN_DEPT scope without department_id → falls through logger.debug
        # scope is still OWN_DEPT, OWN check is False → returns query unchanged
        query.filter.assert_not_called()
        assert result is query

    def test_own_scope_filters_by_owner(self):
        query = MagicMock()
        query.filter.return_value = "own_result"

        class SimpleModel:
            created_by = "owner_col"

        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "viewer"
        user.id = 10
        result = apply_scope_to_query(query, SimpleModel, user)
        query.filter.assert_called_once()
        assert result == "own_result"

    def test_custom_owner_field(self):
        query = MagicMock()
        query.filter.return_value = "custom"

        class SimpleModel:
            user_id = "uid_col"

        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "viewer"
        user.id = 3
        result = apply_scope_to_query(query, SimpleModel, user, owner_field="user_id")
        query.filter.assert_called_once()
        assert result == "custom"


# ---------------------------------------------------------------------------
# check_record_access
# ---------------------------------------------------------------------------

class TestCheckRecordAccess:
    def test_all_scope_always_true(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = True
        user.role = "super_admin"
        record = MagicMock()
        assert check_record_access(record, user) is True

    def test_own_dept_match(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "admin"
        user.department_id = 5
        record = MagicMock()
        record.department_id = 5
        assert check_record_access(record, user) is True

    def test_own_dept_mismatch(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "admin"
        user.department_id = 5
        record = MagicMock()
        record.department_id = 9
        assert check_record_access(record, user) is False

    def test_own_match(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "viewer"
        user.id = 1
        record = MagicMock()
        record.created_by = 1
        assert check_record_access(record, user) is True

    def test_own_mismatch(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "viewer"
        user.id = 1
        record = MagicMock()
        record.created_by = 99
        assert check_record_access(record, user) is False


# ---------------------------------------------------------------------------
# filter_by_data_scope
# ---------------------------------------------------------------------------

class TestFilterByDataScope:
    def test_admin_bypasses(self):
        query = MagicMock()
        model = MagicMock()
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = True
        user.role = "admin"
        result = filter_by_data_scope(query, model, user)
        assert result is query

    def test_non_admin_applies_scope(self):
        query = MagicMock()
        query.filter.return_value = "scoped"

        class SimpleModel:
            created_by = "cb"

        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "viewer"
        user.id = 7
        result = filter_by_data_scope(query, SimpleModel, user)
        assert result == "scoped"


class TestApplyDataScope:
    def test_alias(self):
        assert apply_data_scope is apply_scope_to_query


# ---------------------------------------------------------------------------
# require_data_permission
# ---------------------------------------------------------------------------

class TestRequireDataPermission:
    def test_admin_returns_true(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = True
        user.role = "admin"
        assert require_data_permission(user) is True

    def test_no_db_raises_403(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "viewer"
        with pytest.raises(HTTPException) as exc:
            require_data_permission(user, db=None)
        assert exc.value.status_code == 403

    def test_matching_created_by_returns_true(self):
        user = MagicMock(); user.is_superuser = False
        user.id = 5
        user.is_superuser = False
        user.role = "viewer"
        result = require_data_permission(user, created_by=5, db=MagicMock())
        assert result is True

    def test_mismatched_created_by_raises_403(self):
        user = MagicMock(); user.is_superuser = False
        user.id = 1
        user.is_superuser = False
        user.role = "viewer"
        with pytest.raises(HTTPException) as exc:
            require_data_permission(user, created_by=99, db=MagicMock())
        assert exc.value.status_code == 403

    def test_default_no_match_raises_403(self):
        user = MagicMock(); user.is_superuser = False
        user.id = 1
        user.is_superuser = False
        user.role = "viewer"
        with pytest.raises(HTTPException) as exc:
            require_data_permission(user, db=MagicMock())
        assert exc.value.status_code == 403

    def test_custom_error_message(self):
        user = MagicMock(); user.is_superuser = False
        user.is_superuser = False
        user.role = "viewer"
        with pytest.raises(HTTPException) as exc:
            require_data_permission(user, db=None, error_message="自定义错误")
        assert "自定义错误" in exc.value.detail


class TestDataScopeEnum:
    def test_values(self):
        assert DataScope.ALL.value == "all"
        assert DataScope.OWN_DEPT.value == "own_dept"
        assert DataScope.OWN.value == "own"

    def test_is_string(self):
        # DataScope is a str subclass
        assert isinstance(DataScope.ALL, str)
