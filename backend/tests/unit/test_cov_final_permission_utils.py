"""覆盖 app.core.permission_utils 缺口：require_admin 带参装饰器模式与组织回退 None。"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.permission_utils import get_org_with_fallback, require_admin


class TestRequireAdminDecoratorFactory:
    """require_admin(error_message=...) → decorator（行 85-87）。"""

    async def test_decorated_allows_admin(self):
        @require_admin(error_message="仅管理员可操作")
        async def admin_action(current_user=None):
            return "done"

        admin = SimpleNamespace(role="admin", is_superuser=False)
        assert await admin_action(current_user=admin) == "done"

    async def test_decorated_rejects_non_admin(self):
        @require_admin(error_message="仅管理员可操作")
        async def admin_action(current_user=None):
            return "done"

        user = SimpleNamespace(role="user", is_superuser=False)
        with pytest.raises(HTTPException) as exc_info:
            await admin_action(current_user=user)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "仅管理员可操作"


class TestGetOrgWithFallback:
    def test_new_style_without_any_org_source_returns_none(self):
        # current_user 无 organization_id/org_id 属性、无回调 → 行 199 返回 None
        result = get_org_with_fallback(current_user=SimpleNamespace())
        assert result is None
