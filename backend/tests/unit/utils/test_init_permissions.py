"""
权限和角色初始化测试

测试 app/utils/init_permissions.py 模块
"""
import sys
import pytest
from unittest.mock import MagicMock, patch
from app.utils.init_permissions import (
    DEFAULT_PERMISSIONS,
    init_permissions,
    init_roles,
)


class TestDefaultPermissions:
    def test_has_expected_permissions(self):
        names = [p["name"] for p in DEFAULT_PERMISSIONS]
        for name in ["user:create", "user:read", "user:update", "user:delete",
                       "village:create", "village:read", "village:update", "village:delete",
                       "project:create", "project:read", "project:update", "project:delete",
                       "fund:create", "fund:read", "fund:update", "fund:delete",
                       "school:create", "school:read", "school:update", "school:delete",
                       "audit:read"]:
            assert name in names

    def test_each_permission_has_required_fields(self):
        for perm in DEFAULT_PERMISSIONS:
            assert "name" in perm
            assert "resource" in perm
            assert "action" in perm
            assert "description" in perm

    def test_total_permission_count(self):
        assert len(DEFAULT_PERMISSIONS) == 21


class TestInitPermissions:
    @patch.dict('sys.modules', {'app.models.permission': MagicMock(Permission=MagicMock())})
    def test_create_new_permissions(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        count = init_permissions(mock_db)
        assert count == len(DEFAULT_PERMISSIONS)
        assert mock_db.add.call_count == len(DEFAULT_PERMISSIONS)
        mock_db.commit.assert_called_once()

    @patch.dict('sys.modules', {'app.models.permission': MagicMock(Permission=MagicMock())})
    def test_skip_existing_permissions(self):
        mock_db = MagicMock()
        mock_existing = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing
        count = init_permissions(mock_db)
        assert count == 0
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()

    @patch.dict('sys.modules', {'app.models.permission': MagicMock(Permission=MagicMock())})
    def test_mixed_existing_and_new(self):
        mock_db = MagicMock()
        call_count = [0]
        def mock_first():
            call_count[0] += 1
            if call_count[0] <= 5:
                return None
            return MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = mock_first
        count = init_permissions(mock_db)
        assert count == 5
        mock_db.commit.assert_called_once()


class TestInitRoles:
    @patch.dict('sys.modules', {
        'app.models.permission': MagicMock(Permission=MagicMock()),
        'app.models.rbac': MagicMock(RbacRole=MagicMock()),
    })
    def test_create_roles(self):
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None
        count = init_roles(mock_db)
        assert count == 3
        assert mock_db.add.call_count == 3
        mock_db.commit.assert_called_once()

    @patch.dict('sys.modules', {
        'app.models.permission': MagicMock(Permission=MagicMock()),
        'app.models.rbac': MagicMock(RbacRole=MagicMock()),
    })
    def test_skip_existing_roles(self):
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        count = init_roles(mock_db)
        assert count == 0
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()
