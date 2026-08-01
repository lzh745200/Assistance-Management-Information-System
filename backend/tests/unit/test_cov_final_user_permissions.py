"""app.api.v1.user_permissions 覆盖补全 — 授予权限时业务异常转 400 分支 (lines 317-318)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.user_permissions import GrantPermissionRequest, grant_permission_to_user
from app.core.error_handler import BusinessLogicError


class TestGrantPermissionToUser:
    async def test_business_logic_error_becomes_400(self):
        svc = MagicMock(name="service")
        svc.check_user_permission.return_value = False
        svc.grant_permission_to_user.side_effect = BusinessLogicError("重复授权")

        user = SimpleNamespace(id=1, username="admin", role="user", is_superuser=True)
        request = GrantPermissionRequest(user_id=2, permission="village:view")

        with patch("app.api.v1.user_permissions.UserPermissionService", return_value=svc):
            with pytest.raises(HTTPException) as exc_info:
                await grant_permission_to_user(request=request, db=MagicMock(), current_user=user)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "重复授权"
