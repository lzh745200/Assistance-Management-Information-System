"""覆盖 app.middleware.csrf_middleware 缺口：本机内部备份通道豁免（行 128）。"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from starlette.responses import Response

from app.core.config import settings
from app.middleware.csrf_middleware import CSRFMiddleware


class TestInternalBackupBypass:
    async def test_internal_backup_key_bypasses_csrf(self, monkeypatch):
        monkeypatch.setattr(settings, "CSRF_ENABLED", True)
        monkeypatch.setenv("INTERNAL_BACKUP_KEY", "backup-secret")

        mw = CSRFMiddleware(app=MagicMock())
        request = SimpleNamespace(
            method="POST",
            url=SimpleNamespace(path="/api/v1/system/users"),
            headers={"X-Internal-Backup": "backup-secret"},
            cookies={},
        )
        call_next = AsyncMock(return_value=Response("ok"))

        result = await mw.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)
        assert isinstance(result, Response)

    async def test_wrong_internal_key_falls_through_to_403(self, monkeypatch):
        # 对照组：内部密钥不匹配 → 继续 CSRF 校验，缺少 token 返回 403
        monkeypatch.setattr(settings, "CSRF_ENABLED", True)
        monkeypatch.setenv("INTERNAL_BACKUP_KEY", "backup-secret")

        mw = CSRFMiddleware(app=MagicMock())
        request = SimpleNamespace(
            method="POST",
            url=SimpleNamespace(path="/api/v1/system/users"),
            headers={},
            cookies={},
        )
        call_next = AsyncMock(return_value=Response("ok"))

        result = await mw.dispatch(request, call_next)

        assert result.status_code == 403
        call_next.assert_not_awaited()
