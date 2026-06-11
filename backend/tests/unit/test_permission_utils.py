"""100% coverage tests for app.core.permission_utils"""

import json
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from fastapi import HTTPException, status

from app.core.permission_utils import (
    is_superuser,
    is_admin,
    require_admin,
    get_user_org_id,
    get_org_with_fallback,
    require_organization,
    check_org_access,
    require_permission,
    check_permission,
)


class MockUser:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ─────── is_superuser ───────

class TestIsSuperuser:
    def test_none_user(self):
        assert is_superuser(None) is False

    def test_is_superuser_attr_true(self):
        user = MockUser(is_superuser=True)
        assert is_superuser(user) is True

    def test_is_superuser_attr_false_but_role_super_admin(self):
        user = MockUser(is_superuser=False, role="super_admin")
        assert is_superuser(user) is True

    def test_role_super_admin_no_is_superuser_attr(self):
        user = MockUser(role="super_admin")
        assert is_superuser(user) is True

    def test_role_admin_not_superuser(self):
        user = MockUser(role="admin")
        assert is_superuser(user) is False

    def test_no_role_no_is_superuser(self):
        user = MockUser(name="test")
        assert is_superuser(user) is False

    def test_is_superuser_false_no_role(self):
        user = MockUser(is_superuser=False)
        assert is_superuser(user) is False


# ─────── is_admin ───────

class TestIsAdmin:
    def test_none_user(self):
        assert is_admin(None) is False

    def test_superuser_returns_true(self):
        user = MockUser(is_superuser=True)
        assert is_admin(user) is True

    def test_admin_role(self):
        user = MockUser(role="admin")
        assert is_admin(user) is True

    def test_non_admin_role(self):
        user = MockUser(role="viewer")
        assert is_admin(user) is False

    def test_no_role_attr(self):
        user = MockUser(name="test")
        assert is_admin(user) is False


# ─────── require_admin ───────

class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_admin_from_kwargs(self):
        user = MockUser(is_superuser=True)
        func = AsyncMock(return_value="ok")

        wrapped = require_admin(func)
        result = await wrapped(current_user=user)

        assert result == "ok"
        func.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_admin_from_args(self):
        user = MockUser(is_superuser=True)
        func = AsyncMock(return_value="ok")

        wrapped = require_admin(func)
        result = await wrapped(user)

        assert result == "ok"
        func.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_non_admin_raises_403(self):
        user = MockUser(role="viewer")
        func = AsyncMock()

        wrapped = require_admin(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped(current_user=user)

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "需要管理员权限" in exc.value.detail
        func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_user_raises_401(self):
        func = AsyncMock()

        wrapped = require_admin(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped(x=1)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "未提供用户认证信息" in exc.value.detail
        func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_user_in_args_or_kwargs(self):
        func = AsyncMock()

        wrapped = require_admin(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped("string_arg", 42)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        func.assert_not_awaited()


# ─────── get_user_org_id ───────

class TestGetUserOrgId:
    def test_none_user(self):
        assert get_user_org_id(None) is None

    def test_has_organization_id(self):
        user = MockUser(organization_id=5)
        assert get_user_org_id(user) == 5

    def test_organization_id_is_none(self):
        user = MockUser(organization_id=None, org_id=10)
        assert get_user_org_id(user) == 10

    def test_has_org_id(self):
        user = MockUser(org_id=99)
        assert get_user_org_id(user) == 99

    def test_no_org_attrs(self):
        user = MockUser(name="test")
        assert get_user_org_id(user) is None


# ─────── get_org_with_fallback ───────

class TestGetOrgWithFallback:
    def test_none_user(self):
        assert get_org_with_fallback(None) is None

    def test_has_organization(self):
        org = MagicMock()
        user = MockUser(organization=org)
        result = get_org_with_fallback(user)
        assert result is org

    def test_has_organization_id_no_direct(self):
        user = MockUser(organization_id=42)
        with patch("app.core.permission_utils.logger") as mock_log:
            result = get_org_with_fallback(user)
        assert result is None
        mock_log.debug.assert_called_once()

    def test_no_org_attrs(self):
        user = MockUser(name="test")
        assert get_org_with_fallback(user) is None


# ─────── check_org_access ───────

class TestCheckOrgAccess:
    def test_none_user(self):
        assert check_org_access(None, 1) is False

    def test_admin_always_true(self):
        user = MockUser(is_superuser=True)
        assert check_org_access(user, 999) is True

    def test_org_match(self):
        user = MockUser(organization_id=5)
        assert check_org_access(user, 5) is True

    def test_org_mismatch(self):
        user = MockUser(organization_id=5)
        assert check_org_access(user, 10) is False

    def test_no_org_id(self):
        user = MockUser(name="test")
        assert check_org_access(user, 1) is False


# ─────── check_permission ───────

class TestCheckPermission:
    def test_none_user(self):
        assert check_permission(None, "villages", "read") is False

    def test_admin_returns_true(self):
        user = MockUser(is_superuser=True)
        assert check_permission(user, "villages", "read") is True

    def test_no_permissions_attr(self):
        user = MockUser(name="test")
        assert check_permission(user, "villages", "read") is False

    def test_empty_permissions_list(self):
        user = MockUser(permissions=[])
        assert check_permission(user, "villages", "read") is False

    def test_empty_permissions_string(self):
        user = MockUser(permissions="")
        assert check_permission(user, "villages", "read") is False

    def test_permissions_json_list(self):
        user = MockUser(permissions=json.dumps(["villages:read"]))
        assert check_permission(user, "villages", "read") is True

    def test_permissions_json_list_no_match(self):
        user = MockUser(permissions=json.dumps(["villages:write"]))
        assert check_permission(user, "villages", "read") is False

    def test_permissions_json_invalid_fallback_csv(self):
        user = MockUser(permissions="villages:read, projects:write")
        assert check_permission(user, "villages", "read") is True

    def test_permissions_csv_multiple(self):
        user = MockUser(permissions="projects:write, villages:read")
        assert check_permission(user, "villages", "read") is True

    def test_permissions_csv_no_match(self):
        user = MockUser(permissions="projects:write")
        assert check_permission(user, "villages", "read") is False

    def test_permissions_list_type(self):
        user = MockUser(permissions=["villages:read", "projects:write"])
        assert check_permission(user, "villages", "read") is True

    def test_permissions_list_no_match(self):
        user = MockUser(permissions=["projects:write"])
        assert check_permission(user, "villages", "read") is False

    def test_wildcard_all(self):
        user = MockUser(permissions=["*:*"])
        assert check_permission(user, "villages", "delete") is True

    def test_wildcard_resource(self):
        user = MockUser(permissions=["villages:*"])
        assert check_permission(user, "villages", "read") is True
        assert check_permission(user, "projects", "read") is False

    def test_wildcard_action(self):
        user = MockUser(permissions=["*:read"])
        assert check_permission(user, "villages", "read") is True
        assert check_permission(user, "villages", "write") is False

    def test_mixed_wildcards(self):
        user = MockUser(permissions=["villages:read", "*:*", "*:write", "projects:*"])
        assert check_permission(user, "villages", "read") is True
        assert check_permission(user, "projects", "delete") is True

    def test_list_permissions_exact_match(self):
        user = MockUser(permissions=["villages:read"])
        assert check_permission(user, "villages", "read") is True

    def test_json_decode_error_then_csv(self):
        user = MockUser(permissions="not:valid,foo:bar")
        assert check_permission(user, "not", "valid") is True

    def test_json_decode_error_then_csv_no_match(self):
        user = MockUser(permissions="villages:read,projects:write")
        assert check_permission(user, "villages", "write") is False

    def test_permissions_csv_string(self):
        user = MockUser(permissions="villages:read")
        assert check_permission(user, "villages", "read") is True

    @pytest.mark.parametrize("perm,resource,action,expected", [
        ("*:*", "any", "any", True),
        ("villages:*", "villages", "write", True),
        ("*:read", "villages", "read", True),
        ("villages:read", "villages", "read", True),
        ("villages:read", "villages", "write", False),
        ("villages:write", "projects", "write", False),
    ])
    def test_parametrized_permission_checks(self, perm, resource, action, expected):
        user = MockUser(permissions=[perm])
        assert check_permission(user, resource, action) is expected


# ─────── require_organization ───────

class TestRequireOrganization:
    @pytest.mark.asyncio
    async def test_no_func_returns_decorator(self):
        decorator = require_organization(org_param="custom_id")
        assert callable(decorator)

    @pytest.mark.asyncio
    async def test_admin_bypasses_check(self):
        user = MockUser(is_superuser=True)
        func = AsyncMock(return_value="ok")

        wrapped = require_organization(func)
        result = await wrapped(current_user=user, organization_id=5)

        assert result == "ok"
        func.assert_awaited_once_with(current_user=user, organization_id=5)

    @pytest.mark.asyncio
    async def test_org_match_success(self):
        user = MockUser(organization_id=5)
        func = AsyncMock(return_value="ok")

        wrapped = require_organization(func)
        result = await wrapped(current_user=user, organization_id=5)

        assert result == "ok"
        func.assert_awaited_once_with(current_user=user, organization_id=5)

    @pytest.mark.asyncio
    async def test_org_mismatch_raises_403(self):
        user = MockUser(organization_id=5)
        func = AsyncMock()

        wrapped = require_organization(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped(current_user=user, organization_id=99)

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "无权访问其他组织的数据" in exc.value.detail
        func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_current_user_raises_401(self):
        func = AsyncMock()

        wrapped = require_organization(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped(organization_id=5)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "未提供用户认证信息" in exc.value.detail
        func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_current_user_from_args(self):
        user = MockUser(organization_id=5, role="viewer")
        func = AsyncMock(return_value="ok")

        wrapped = require_organization(func)
        result = await wrapped(user, organization_id=5)

        assert result == "ok"
        func.assert_awaited_once_with(user, organization_id=5)

    @pytest.mark.asyncio
    async def test_no_user_in_args_or_kwargs(self):
        func = AsyncMock()

        wrapped = require_organization(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped(organization_id=5)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_org_id_in_kwargs_success(self):
        user = MockUser(organization_id=5)
        func = AsyncMock(return_value="ok")

        wrapped = require_organization(func)
        result = await wrapped(current_user=user)

        assert result == "ok"
        func.assert_awaited_once_with(current_user=user)

    @pytest.mark.asyncio
    async def test_user_has_no_org_id(self):
        user = MockUser(name="test")
        func = AsyncMock(return_value="ok")

        wrapped = require_organization(func)
        result = await wrapped(current_user=user, organization_id=5)

        assert result == "ok"
        func.assert_awaited_once_with(current_user=user, organization_id=5)

    @pytest.mark.asyncio
    async def test_org_param_custom(self):
        user = MockUser(organization_id=10)
        func = AsyncMock(return_value="ok")

        wrapped = require_organization(func, org_param="custom_id")
        result = await wrapped(current_user=user, custom_id=10)

        assert result == "ok"
        func.assert_awaited_once_with(current_user=user, custom_id=10)

    @pytest.mark.asyncio
    async def test_org_param_custom_mismatch(self):
        user = MockUser(organization_id=10)
        func = AsyncMock()

        wrapped = require_organization(func, org_param="custom_id")
        with pytest.raises(HTTPException) as exc:
            await wrapped(current_user=user, custom_id=99)

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_require_organization_no_func_with_decorator(self):
        user = MockUser(organization_id=5)
        func = AsyncMock(return_value="ok")

        wrapped = require_organization(org_param="custom_id")(func)
        result = await wrapped(current_user=user, custom_id=5)

        assert result == "ok"
        func.assert_awaited_once_with(current_user=user, custom_id=5)

    @pytest.mark.asyncio
    async def test_args_lookup_no_user_props(self):
        func = AsyncMock()

        wrapped = require_organization(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped("not_a_user", organization_id=5)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        func.assert_not_awaited()


# ─────── require_permission ───────

class TestRequirePermission:
    @pytest.mark.asyncio
    async def test_has_permission_from_kwargs(self):
        user = MockUser(permissions=["*:*"])
        func = AsyncMock(return_value="ok")

        wrapped = require_permission("villages:write")(func)
        result = await wrapped(current_user=user)

        assert result == "ok"
        func.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_has_permission_from_args(self):
        user = MockUser(permissions=["*:*"], role="viewer")
        func = AsyncMock(return_value="ok")

        wrapped = require_permission("villages:write")(func)
        result = await wrapped(user)

        assert result == "ok"
        func.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_missing_permission_raises_403(self):
        user = MockUser(permissions=["villages:read"])
        func = AsyncMock()

        wrapped = require_permission("villages:write")(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped(current_user=user)

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "缺少权限" in exc.value.detail
        func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_user_raises_401(self):
        func = AsyncMock()

        wrapped = require_permission("villages:write")(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped(x=1)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "未提供用户认证信息" in exc.value.detail
        func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_user_in_args_or_kwargs(self):
        func = AsyncMock()

        wrapped = require_permission("villages:write")(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped("string_arg", 42)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_admin_bypasses_permission_check(self):
        user = MockUser(is_superuser=True)
        func = AsyncMock(return_value="ok")

        wrapped = require_permission("villages:write")(func)
        result = await wrapped(current_user=user)

        assert result == "ok"
        func.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_permissions_attr(self):
        user = MockUser(name="test")
        func = AsyncMock()

        wrapped = require_permission("villages:write")(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped(current_user=user)

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_args_lookup_not_a_user(self):
        func = AsyncMock()

        wrapped = require_permission("villages:write")(func)
        with pytest.raises(HTTPException) as exc:
            await wrapped(42, "hello")

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        func.assert_not_awaited()
