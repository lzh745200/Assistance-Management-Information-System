"""
零信任动态权限评估器测试

测试 app/services/zero_trust/dynamic_permission.py 模块
"""
import pytest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.zero_trust.dynamic_permission import (
    PermissionEvaluator,
    permission_evaluator,
)
from app.services.zero_trust.device_fingerprint import device_fingerprint_service


def _make_user(username="admin", is_superuser=True, role="admin"):
    """创建模拟用户对象。"""
    return SimpleNamespace(
        username=username,
        is_superuser=is_superuser,
        role=role,
    )


class TestPermissionEvaluatorBasic:
    """基础权限评估测试。"""

    @pytest.mark.asyncio
    async def test_authenticated_read_allowed(self):
        """已认证用户的 read 操作允许。"""
        user = _make_user()
        result = await permission_evaluator.evaluate(user, "/api/v1/villages", "read")
        assert result is True

    @pytest.mark.asyncio
    async def test_authenticated_write_allowed(self):
        """已认证用户的 write 操作允许。"""
        user = _make_user()
        result = await permission_evaluator.evaluate(user, "/api/v1/villages", "write")
        assert result is True

    @pytest.mark.asyncio
    async def test_anonymous_read_allowed(self):
        """匿名用户的 read 操作允许。"""
        result = await permission_evaluator.evaluate(None, "/api/v1/public", "read")
        assert result is True

    @pytest.mark.asyncio
    async def test_anonymous_write_denied(self):
        """匿名用户的 write 操作被拒绝。"""
        result = await permission_evaluator.evaluate(None, "/api/v1/villages", "write")
        assert result is False

    @pytest.mark.asyncio
    async def test_anonymous_delete_denied(self):
        """匿名用户的 delete 操作被拒绝。"""
        result = await permission_evaluator.evaluate(None, "/api/v1/villages", "delete")
        assert result is False

    @pytest.mark.asyncio
    async def test_anonymous_admin_denied(self):
        """匿名用户的 admin 操作被拒绝。"""
        result = await permission_evaluator.evaluate(None, "/api/v1/admin", "admin")
        assert result is False


class TestPermissionEvaluatorAdmin:
    """管理员权限评估测试。"""

    @pytest.mark.asyncio
    async def test_admin_allowed_for_superuser(self):
        """超级管理员的 admin 操作允许。"""
        user = _make_user(username="superadmin", is_superuser=True, role="super_admin")
        result = await permission_evaluator.evaluate(user, "/admin/config", "admin")
        assert result is True

    @pytest.mark.asyncio
    async def test_admin_allowed_for_admin_role(self):
        """admin 角色的 admin 操作允许。"""
        user = _make_user(username="admin_user", is_superuser=False, role="admin")
        result = await permission_evaluator.evaluate(user, "/admin/config", "admin")
        assert result is True

    @pytest.mark.asyncio
    async def test_admin_denied_for_regular_user(self):
        """普通用户的 admin 操作被拒绝。"""
        user = _make_user(username="regular", is_superuser=False, role="user")
        result = await permission_evaluator.evaluate(user, "/admin/config", "admin")
        assert result is False

    @pytest.mark.asyncio
    async def test_admin_denied_for_manager(self):
        """manager 角色的 admin 操作被拒绝。"""
        user = _make_user(username="mgr", is_superuser=False, role="manager")
        result = await permission_evaluator.evaluate(user, "/admin/config", "admin")
        assert result is False


class TestPermissionEvaluatorDeviceTrust:
    """设备信任度评估测试。"""

    @pytest.mark.asyncio
    async def test_delete_with_trusted_device(self):
        """高信任设备的 delete 操作允许。"""
        user = _make_user()
        # 未知设备默认信任分 0.5 >= 0.5
        result = await permission_evaluator.evaluate(
            user, "/api/v1/villages/1", "delete", device_fingerprint="trusted_device_fp"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_with_low_trust_device(self):
        """低信任设备的 delete 操作被拒绝。"""
        user = _make_user()
        with patch.object(device_fingerprint_service, "get_trust_score", return_value=0.2):
            result = await permission_evaluator.evaluate(
                user, "/api/v1/villages/1", "delete", device_fingerprint="low_trust_fp"
            )
        assert result is False

    @pytest.mark.asyncio
    async def test_admin_with_low_trust_device(self):
        """低信任设备的 admin 操作被拒绝（即使用户是管理员）。"""
        user = _make_user()
        with patch.object(device_fingerprint_service, "get_trust_score", return_value=0.3):
            result = await permission_evaluator.evaluate(
                user, "/admin/config", "admin", device_fingerprint="low_trust_fp"
            )
        assert result is False

    @pytest.mark.asyncio
    async def test_admin_with_high_trust_device(self):
        """高信任设备的 admin 操作允许。"""
        user = _make_user()
        with patch.object(device_fingerprint_service, "get_trust_score", return_value=0.9):
            result = await permission_evaluator.evaluate(
                user, "/admin/config", "admin", device_fingerprint="high_trust_fp"
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_blocked_device_denied(self):
        """被封禁设备的所有操作被拒绝。"""
        user = _make_user()
        with patch.object(device_fingerprint_service, "is_device_blocked", return_value=True):
            result = await permission_evaluator.evaluate(
                user, "/api/v1/villages", "read", device_fingerprint="blocked_fp"
            )
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_without_fingerprint_allowed(self):
        """无设备指纹时 delete 操作允许（仅基于用户权限）。"""
        user = _make_user()
        result = await permission_evaluator.evaluate(
            user, "/api/v1/villages/1", "delete", device_fingerprint=None
        )
        assert result is True


class TestPermissionEvaluatorGlobal:
    """全局实例测试。"""

    def test_global_instance_exists(self):
        assert permission_evaluator is not None
        assert isinstance(permission_evaluator, PermissionEvaluator)

    @pytest.mark.asyncio
    async def test_global_instance_evaluates(self):
        """全局实例可以正常评估。"""
        user = _make_user()
        result = await permission_evaluator.evaluate(user, "/test", "read")
        assert result is True
