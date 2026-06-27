"""
Tests for data_scope.py — DataScope class and get_data_scope dependency.
Covers all code paths: admin, self_only, org, org_children, fallback, tree traversal.
"""
from unittest.mock import MagicMock, patch
import pytest

# ── DataScope class ──────────────────────────────────────────────────

class TestDataScopeInit:
    def test_defaults(self):
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=False)
        assert ds.is_admin is False
        assert ds.org_names == []
        assert ds.org_ids == []
        assert ds.self_only is False
        assert ds.user_id is None

    def test_admin(self):
        ds = type("DataScope", (), {"__init__": lambda s, a, b=None, c=None, d=False, e=None: None}) if False else None
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=True)
        assert ds.is_admin is True
        assert ds.has_full_access() is True

    def test_with_orgs(self):
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=False, org_names=["org1"], org_ids=[1, 2])
        assert ds.org_names == ["org1"]
        assert ds.org_ids == [1, 2]

    def test_self_only(self):
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=False, self_only=True, user_id=42)
        assert ds.self_only is True
        assert ds.user_id == 42


class TestDataScopeFilterByOrgIds:
    def test_admin_returns_unmodified(self):
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=True)
        q = MagicMock()
        result = ds.filter_by_org_ids(q)
        assert result is q

    def test_self_only_with_user_id(self):
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=False, self_only=True, user_id=42)
        q = MagicMock()
        col = MagicMock()
        result = ds.filter_by_org_ids(q, col, created_by_column=col)
        q.filter.assert_called_once()
        assert result == q.filter.return_value

    def test_self_only_no_user_id(self):
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=False, self_only=True, user_id=None)
        q = MagicMock()
        result = ds.filter_by_org_ids(q, MagicMock(), created_by_column=MagicMock())
        q.filter.assert_called_once_with(False)
        assert result == q.filter.return_value

    def test_no_org_ids_returns_false(self):
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=False, org_ids=[])
        q = MagicMock()
        result = ds.filter_by_org_ids(q, MagicMock())
        q.filter.assert_called_once_with(False)

    def test_with_org_ids(self):
        from sqlalchemy import column
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=False, org_ids=[1, 2])
        q = MagicMock()
        col = column("organization_id")
        result = ds.filter_by_org_ids(q, col)
        q.filter.assert_called_once()
        assert result == q.filter.return_value

    def test_multiple_columns(self):
        from sqlalchemy import column
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=False, org_ids=[1])
        q = MagicMock()
        c1, c2 = column("org_id"), column("dept_id")
        result = ds.filter_by_org_ids(q, c1, c2)
        q.filter.assert_called_once()
        assert result == q.filter.return_value

    def test_no_id_columns_no_org_ids(self):
        from app.api.v1.data_scope import DataScope
        ds = DataScope(is_admin=False, org_ids=[])
        q = MagicMock()
        result = ds.filter_by_org_ids(q)
        q.filter.assert_called_once_with(False)


# ── _get_org_subtree ─────────────────────────────────────────────────

class TestGetOrgSubtree:
    def test_org_not_found(self):
        with patch("app.api.v1.data_scope.logger") as mock_log:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            from app.api.v1.data_scope import _get_org_subtree
            ids, names = _get_org_subtree(mock_db, 999)
            assert ids == []
            assert names == []

    def test_org_found(self):
        mock_db = MagicMock()
        org = MagicMock()
        org.id = 1
        org.name = "Root"
        mock_db.query.return_value.filter.return_value.first.return_value = org
        mock_db.query.return_value.filter.return_value.all.return_value = []
        from app.api.v1.data_scope import _get_org_subtree
        ids, names = _get_org_subtree(mock_db, 1)
        assert ids == [1]
        assert names == ["Root"]

    def test_with_children(self):
        mock_db = MagicMock()
        parent = MagicMock()
        parent.id = 1
        parent.name = "Parent"
        child = MagicMock()
        child.id = 2
        child.name = "Child"

        mock_db.query.return_value.filter.return_value.first.side_effect = [parent, child]
        mock_db.query.return_value.filter.return_value.all.side_effect = [[child], []]

        from app.api.v1.data_scope import _get_org_subtree
        ids, names = _get_org_subtree(mock_db, 1)
        assert 1 in ids
        assert 2 in ids

    def test_circular_reference(self):
        mock_db = MagicMock()
        org = MagicMock()
        org.id = 1
        org.name = "Loop"
        mock_db.query.return_value.filter.return_value.first.return_value = org
        mock_db.query.return_value.filter.return_value.all.return_value = []
        from app.api.v1.data_scope import _get_org_subtree
        ids, names = _get_org_subtree(mock_db, 1, _depth=0, _visited={1})
        assert ids == []
        assert names == []

    def test_max_depth(self):
        mock_db = MagicMock()
        org = MagicMock()
        org.id = 1
        org.name = "Deep"
        mock_db.query.return_value.filter.return_value.first.return_value = org
        mock_db.query.return_value.filter.return_value.all.return_value = []
        from app.api.v1.data_scope import _get_org_subtree
        ids, names = _get_org_subtree(mock_db, 1, _depth=11)
        assert ids == []
        assert names == []


# ── get_data_scope dependency ───────────────────────────────────────

class TestGetDataScope:
    @pytest.mark.asyncio
    async def test_admin_role(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "admin"
        user.data_scope = "org"
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            ds = await get_data_scope(current_user=user, db=None)
        assert ds.is_admin is True

    @pytest.mark.asyncio
    async def test_super_admin_role(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "super_admin"
        user.data_scope = "org"
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            ds = await get_data_scope(current_user=user, db=None)
        assert ds.is_admin is True

    @pytest.mark.asyncio
    async def test_is_superuser(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "org"
        with patch("app.api.v1.data_scope.is_superuser", return_value=True):
            ds = await get_data_scope(current_user=user, db=None)
        assert ds.is_admin is True

    @pytest.mark.asyncio
    async def test_data_scope_all(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "all"
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            ds = await get_data_scope(current_user=user, db=None)
        assert ds.is_admin is True

    @pytest.mark.asyncio
    async def test_self_scope(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "self"
        user.id = 42
        user.organization_id = None
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            ds = await get_data_scope(current_user=user, db=None)
        assert ds.is_admin is False
        assert ds.self_only is True
        assert ds.user_id == 42

    @pytest.mark.asyncio
    async def test_org_scope_with_org_id(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "org"
        user.organization_id = 5
        user.department = None
        mock_db = MagicMock()
        org = MagicMock()
        org.name = "TestOrg"
        mock_db.query.return_value.filter.return_value.first.return_value = org
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            ds = await get_data_scope(current_user=user, db=mock_db)
        assert ds.is_admin is False
        assert ds.org_names == ["TestOrg"]
        assert ds.org_ids == [5]

    @pytest.mark.asyncio
    async def test_org_scope_no_org_id_with_dept(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "org"
        user.organization_id = None
        user.department = "SomeDept"
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            ds = await get_data_scope(current_user=user, db=None)
        assert ds.is_admin is False
        assert ds.org_names == ["SomeDept"]

    @pytest.mark.asyncio
    async def test_org_scope_no_org_id_fallback_admin(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "org"
        user.organization_id = None
        user.department = None
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            ds = await get_data_scope(current_user=user, db=None)
        assert ds.is_admin is True

    @pytest.mark.asyncio
    async def test_org_children_default_no_org_id_with_dept(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "org_children"
        user.organization_id = None
        user.department = "Dept"
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            ds = await get_data_scope(current_user=user, db=None)
        assert ds.is_admin is False
        assert ds.org_names == ["Dept"]

    @pytest.mark.asyncio
    async def test_org_children_no_org_id_fallback_admin(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "org_children"
        user.organization_id = None
        user.department = None
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            ds = await get_data_scope(current_user=user, db=None)
        assert ds.is_admin is True

    @pytest.mark.asyncio
    async def test_org_children_with_subtree(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "org_children"
        user.organization_id = 1
        user.department = None
        mock_db = MagicMock()
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            with patch("app.api.v1.data_scope._get_org_subtree", return_value=([1, 2], ["Root", "Child"])):
                ds = await get_data_scope(current_user=user, db=mock_db)
        assert ds.is_admin is False
        assert ds.org_ids == [1, 2]
        assert ds.org_names == ["Root", "Child"]

    @pytest.mark.asyncio
    async def test_org_children_empty_names_with_dept(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "org_children"
        user.organization_id = 1
        user.department = "DeptFallback"
        mock_db = MagicMock()
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            with patch("app.api.v1.data_scope._get_org_subtree", return_value=([1], [])):
                ds = await get_data_scope(current_user=user, db=mock_db)
        assert ds.is_admin is False
        assert ds.org_names == ["DeptFallback"]
        assert ds.org_ids == [1]

    @pytest.mark.asyncio
    async def test_org_children_empty_names_fallback_admin(self):
        from app.api.v1.data_scope import get_data_scope
        user = MagicMock()
        user.role = "user"
        user.data_scope = "org_children"
        user.organization_id = 1
        user.department = None
        mock_db = MagicMock()
        with patch("app.api.v1.data_scope.is_superuser", return_value=False):
            with patch("app.api.v1.data_scope._get_org_subtree", return_value=([1], [])):
                ds = await get_data_scope(current_user=user, db=mock_db)
        assert ds.is_admin is True
