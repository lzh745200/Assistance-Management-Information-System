"""app.api.v1.permission_package 覆盖补全 — 4 个端点的非管理员 403 分支
(lines 45, 66, 95, 138)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import app.api.v1.permission_package as pp


def _non_admin():
    return SimpleNamespace(id=2, username="bob", role="user", is_superuser=False)


class TestNonAdminForbidden:
    def test_export_forbidden(self):
        with pytest.raises(HTTPException) as exc_info:
            pp.export_permission_package(None, _non_admin(), MagicMock())
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "需要管理员权限"

    def test_download_forbidden(self):
        with pytest.raises(HTTPException) as exc_info:
            pp.download_permission_package("pkg.zip", _non_admin())
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "需要管理员权限"

    async def test_import_forbidden(self):
        file = SimpleNamespace(filename="pkg.zip")
        with pytest.raises(HTTPException) as exc_info:
            await pp.import_permission_package(file, _non_admin(), MagicMock())
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "需要管理员权限"

    def test_confirm_forbidden(self):
        body = pp.PermissionPackageConfirmRequest()
        with pytest.raises(HTTPException) as exc_info:
            pp.confirm_import_permission_package("pkg.zip", body, _non_admin(), MagicMock())
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "需要管理员权限"
