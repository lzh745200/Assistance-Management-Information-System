"""Tests for app.utils.permission_filter - zero coverage → 100%"""

import pytest
from unittest.mock import MagicMock
from app.utils.permission_filter import (
    get_org_hierarchy_cached,
    clear_org_hierarchy_cache,
    PermissionFilter,
    with_permission_filter,
    _org_hierarchy_cache,
)


# ---------------------------------------------------------------------------
# get_org_hierarchy_cached
# ---------------------------------------------------------------------------

class TestGetOrgHierarchyCached:
    def setup_method(self):
        clear_org_hierarchy_cache()

    def teardown_method(self):
        clear_org_hierarchy_cache()

    def test_returns_set_with_own_id(self):
        result = get_org_hierarchy_cached(1)
        assert isinstance(result, set)
        assert 1 in result

    def test_caches_result(self):
        get_org_hierarchy_cached(5)
        assert 5 in _org_hierarchy_cache
        result = get_org_hierarchy_cached(5)
        assert result == _org_hierarchy_cache[5]

    def test_different_orgs_independent(self):
        r1 = get_org_hierarchy_cached(10)
        r2 = get_org_hierarchy_cached(20)
        assert 10 in r1
        assert 20 in r2
        assert 10 not in r2

    def test_negative_id(self):
        result = get_org_hierarchy_cached(-1)
        assert -1 in result


class TestClearOrgHierarchyCache:
    def test_clears_all_entries(self):
        get_org_hierarchy_cached(1)
        get_org_hierarchy_cached(2)
        assert len(_org_hierarchy_cache) == 2
        clear_org_hierarchy_cache()
        assert len(_org_hierarchy_cache) == 0

    def test_idempotent(self):
        clear_org_hierarchy_cache()
        clear_org_hierarchy_cache()
        assert len(_org_hierarchy_cache) == 0


# ---------------------------------------------------------------------------
# PermissionFilter.__init__
# ---------------------------------------------------------------------------

class TestPermissionFilterInit:
    def test_stores_user(self):
        user = MagicMock()
        f = PermissionFilter(user)
        assert f.user is user

    def test_default_user_is_none(self):
        f = PermissionFilter()
        assert f.user is None


# ---------------------------------------------------------------------------
# PermissionFilter.apply_org_filter
# ---------------------------------------------------------------------------

class TestPermissionFilterApplyOrgFilter:
    def test_no_user_returns_query_unchanged(self):
        f = PermissionFilter()
        query = MagicMock()
        model = MagicMock()
        result = f.apply_org_filter(query, model)
        assert result is query

    def test_admin_user_skips_filter(self):
        user = MagicMock()
        user.role = "admin"
        f = PermissionFilter(user)
        query = MagicMock()
        model = MagicMock()
        result = f.apply_org_filter(query, model)
        assert result is query

    def test_super_admin_skips_filter(self):
        user = MagicMock()
        user.role = "super_admin"
        f = PermissionFilter(user)
        query = MagicMock()
        model = MagicMock()
        result = f.apply_org_filter(query, model)
        assert result is query

    def test_regular_user_filters_by_org(self):
        user = MagicMock()
        user.role = "user"
        user.organization_id = 42
        f = PermissionFilter(user)
        query = MagicMock()
        query.filter.return_value = "filtered"
        model = MagicMock()
        # Make organization_id accessible as column
        type(model).organization_id = MagicMock()

        result = f.apply_org_filter(query, model)
        query.filter.assert_called_once()
        assert result == "filtered"

    def test_regular_user_no_org_id_skips_filter(self):
        user = MagicMock()
        user.role = "user"
        user.organization_id = None
        f = PermissionFilter(user)
        query = MagicMock()
        model = MagicMock()
        result = f.apply_org_filter(query, model)
        assert result is query

    def test_regular_user_no_org_field_on_model(self):
        user = MagicMock()
        user.role = "user"
        user.organization_id = 5
        f = PermissionFilter(user)
        query = MagicMock()
        model = MagicMock()
        del model.organization_id
        result = f.apply_org_filter(query, model)
        assert result is query

    def test_custom_org_field_name(self):
        user = MagicMock()
        user.role = "user"
        user.organization_id = 7
        f = PermissionFilter(user)
        query = MagicMock()
        query.filter.return_value = "custom_filtered"
        model = MagicMock()
        type(model).dept_id = MagicMock()

        result = f.apply_org_filter(query, model, org_field="dept_id")
        query.filter.assert_called_once()
        assert result == "custom_filtered"

    def test_user_without_role_attr(self):
        # Use an object without 'role' or 'organization_id' attribute
        class BareUser:
            pass
        f = PermissionFilter(BareUser())
        query = MagicMock()
        model = MagicMock()
        result = f.apply_org_filter(query, model)
        assert result is query


# ---------------------------------------------------------------------------
# PermissionFilter.can_access
# ---------------------------------------------------------------------------

class TestPermissionFilterCanAccess:
    def test_no_user_returns_false(self):
        f = PermissionFilter()
        assert f.can_access(100) is False

    def test_admin_always_true(self):
        user = MagicMock()
        user.role = "admin"
        f = PermissionFilter(user)
        assert f.can_access(999) is True

    def test_super_admin_always_true(self):
        user = MagicMock()
        user.role = "super_admin"
        f = PermissionFilter(user)
        assert f.can_access(1) is True

    def test_regular_user_same_org_returns_true(self):
        user = MagicMock()
        user.role = "user"
        user.organization_id = 42
        f = PermissionFilter(user)
        assert f.can_access(42) is True

    def test_regular_user_different_org_returns_false(self):
        user = MagicMock()
        user.role = "user"
        user.organization_id = 42
        f = PermissionFilter(user)
        assert f.can_access(99) is False

    def test_user_no_org_id_returns_false(self):
        user = MagicMock()
        user.role = "user"
        user.organization_id = None
        f = PermissionFilter(user)
        assert f.can_access(1) is False

    def test_user_without_role_attr(self):
        class BareUser:
            pass
        f = PermissionFilter(BareUser())
        assert f.can_access(1) is False


# ---------------------------------------------------------------------------
# with_permission_filter decorator
# ---------------------------------------------------------------------------

class TestWithPermissionFilter:
    def test_injects_filter_into_kwargs(self):
        @with_permission_filter
        def my_func(user=None, **kwargs):
            return {"user": user, "filter": kwargs.get("filter")}

        mock_user = MagicMock()
        mock_user.role = "admin"
        result = my_func(user=mock_user)
        assert result["user"] is mock_user
        assert isinstance(result["filter"], PermissionFilter)
        assert result["filter"].user is mock_user

    def test_uses_existing_filter_if_provided(self):
        existing_filter = PermissionFilter()

        @with_permission_filter
        def my_func(user=None, **kwargs):
            return kwargs.get("filter")

        mock_user = MagicMock()
        result = my_func(user=mock_user, filter=existing_filter)
        assert result is existing_filter

    def test_finds_user_in_args(self):
        @with_permission_filter
        def my_func(db, current_user, **kwargs):
            return {"user": current_user, "filter": kwargs.get("filter")}

        mock_user = MagicMock()
        mock_user.role = "operator"
        mock_user.is_superuser = False
        db = MagicMock()
        result = my_func(db, mock_user)
        assert result["user"] is mock_user
        assert isinstance(result["filter"], PermissionFilter)

    def test_no_user_found_creates_filter_with_none_user(self):
        @with_permission_filter
        def my_func(db, **kwargs):
            return kwargs.get("filter")

        # Plain object without role/is_superuser
        result = my_func("just_a_string")
        assert isinstance(result, PermissionFilter)
        assert result.user is None

    def test_preserves_function_name(self):
        @with_permission_filter
        def my_custom_name(**kwargs):
            pass

        assert my_custom_name.__name__ == "my_custom_name"

    def test_preserves_docstring(self):
        @with_permission_filter
        def my_doc_func(**kwargs):
            """My docstring."""
            pass

        assert my_doc_func.__doc__ == "My docstring."

    def test_passes_through_return_value(self):
        @with_permission_filter
        def adder(a, b, **kwargs):
            return a + b

        assert adder(1, 2) == 3

    def test_extracts_user_from_current_user_kwarg(self):
        @with_permission_filter
        def my_func(current_user=None, **kwargs):
            return kwargs.get("filter")

        mock_user = MagicMock()
        mock_user.role = "user"
        mock_user.organization_id = 5
        result = my_func(current_user=mock_user)
        assert result.user is mock_user

    def test_no_args_no_kwargs(self):
        @with_permission_filter
        def noop(**kwargs):
            return kwargs.get("filter")

        result = noop()
        assert isinstance(result, PermissionFilter)
        assert result.user is None
