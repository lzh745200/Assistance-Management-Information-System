"""app.services.rbac_service 覆盖率攻坚测试

补齐缺口：
- _safe_parse_expires 无效字符串（41-42）
- check_permission：db 为 None（168）、机器码限制拒绝（173-182）、角色权限放行（212-221）
- _compute_user_permissions_with_restrictions：白名单交集（328, 332）、机器码限制扣减（337-338）
- _has_admin_role（673-685）、_has_resource_access（727-739）

db 使用 MagicMock 链式查询；MachineCodePermissionService 为外部依赖，patch 掉。
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import app.services.rbac_service as rbac_mod
from app.services.rbac_service import RBACService, _safe_parse_expires


@pytest.fixture(autouse=True)
def _reset_perm_cache():
    """每个用例前后重置请求级机器码权限缓存，避免用例间串扰"""
    rbac_mod._restricted_perms_cache.set(None)
    yield
    rbac_mod._restricted_perms_cache.set(None)


def _query_mock():
    db = MagicMock()
    q = db.query.return_value
    q.filter.return_value = q
    q.join.return_value = q
    q.distinct.return_value = q
    q.order_by.return_value = q
    return db, q


def _patch_mcp(restricted):
    """patch 机器码权限服务，返回指定的受限权限集合"""
    return patch.object(
        rbac_mod,
        "MachineCodePermissionService",
        return_value=SimpleNamespace(get_user_restricted_permissions=lambda uid: restricted),
    )


class TestSafeParseExpires:
    def test_invalid_string_returns_none(self):
        assert _safe_parse_expires("not-a-date") is None


class TestCheckPermission:
    async def test_db_none_returns_false(self):
        svc = RBACService()
        assert await svc.check_permission("1", "user:read", db=None) is False

    async def test_restricted_permission_denied(self):
        svc = RBACService()
        db, q = _query_mock()
        with _patch_mcp({"user:read"}):
            granted = await svc.check_permission("1", "user:read", "village", "5", db=db)
        assert granted is False
        # 受限拒绝也会写访问日志
        db.add.assert_called_once()

    async def test_role_permission_granted(self):
        svc = RBACService()
        db, q = _query_mock()
        # admin 角色计数 0、直接权限计数 0、角色权限计数 1
        q.scalar.side_effect = [0, 0, 1]
        with _patch_mcp(set()):
            granted = await svc.check_permission("1", "user:read", db=db)
        assert granted is True
        db.add.assert_called_once()


class TestComputeUserPermissions:
    async def test_whitelist_intersection_then_machine_restriction(self):
        svc = RBACService()
        db, q = _query_mock()
        q.all.side_effect = [
            [("user:read",), ("village:read",)],  # 直接权限
            [],  # 角色权限
        ]
        q.first.return_value = SimpleNamespace(allowed_permissions_list=["user:read"])
        with _patch_mcp({"user:read"}):
            effective, restricted = await svc.get_user_permissions_with_restrictions("1", db)
        # 白名单交集后剩 user:read，再被机器码限制全部扣掉
        assert effective == set()
        assert restricted == {"user:read"}


class TestHasAdminRole:
    def test_true_and_false(self):
        svc = RBACService()
        db, q = _query_mock()
        q.scalar.side_effect = [1, 0]
        assert svc._has_admin_role("1", db) is True
        assert svc._has_admin_role("1", db) is False


class TestHasResourceAccess:
    def test_true_and_false(self):
        svc = RBACService()
        db, q = _query_mock()
        q.scalar.side_effect = [1, 0]
        assert svc._has_resource_access("1", "village", "5", "write", db) is True
        assert svc._has_resource_access("2", "village", "5", "write", db) is False
