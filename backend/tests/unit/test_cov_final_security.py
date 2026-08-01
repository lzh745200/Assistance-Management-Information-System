"""覆盖 app.core.security 缺口：
- 行 49：bcrypt 兼容补丁捕获 ValueError（在全新模块对象中重放模块级代码，不污染 sys.modules）
- 行 363-365：get_current_user 审计归因失败的静默兜底
- 行 552,554：速率限制器过期键清理
"""
import importlib
import sys
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import app.core.security as sec


class TestBcryptCompatPatchValueError:
    """行 48-49：bcrypt>=4.1 时 passlib 补丁触发 ValueError 的兜底日志。

    模块级 try/except 仅在 import 时执行，沿用 test_core_security.py 的
    _reimport_security 模式：mock bcrypt 4.1.0 并让 passlib 导入抛 ValueError，
    重导入后恢复原模块对象，不影响其他测试的依赖覆盖。
    """

    def test_value_error_branch_is_logged(self):
        mock_bcrypt = MagicMock()
        mock_bcrypt.__version__ = "4.1.0"
        orig = sys.modules.pop("app.core.security", None)
        try:
            with patch("app.core.security.logger.debug") as mock_debug:
                orig_import = __import__

                def fake_import(name, *args, **kwargs):
                    if name == "passlib.handlers.bcrypt":
                        raise ValueError("mocked passlib incompat")
                    return orig_import(name, *args, **kwargs)

                with patch.dict("sys.modules", {"bcrypt": mock_bcrypt}, clear=False):
                    with patch("builtins.__import__", side_effect=fake_import):
                        sys.modules.pop("app.core.security", None)
                        importlib.import_module("app.core.security")
            mock_debug.assert_called_once()
            assert "bcrypt版本兼容检测跳过" in mock_debug.call_args.args[0]
        finally:
            sys.modules.pop("app.core.security", None)
            if orig is not None:
                sys.modules["app.core.security"] = orig


class TestGetCurrentUserAuditAttribution:
    async def test_set_current_user_failure_is_swallowed(self, monkeypatch):
        user = SimpleNamespace(id=42, username="admin", token_version_safe=0)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user

        monkeypatch.setattr("app.core.database.SessionLocal", MagicMock(return_value=db))
        monkeypatch.setattr(sec, "decode_token", MagicMock(return_value={"sub": "admin"}))
        monkeypatch.setattr(
            "app.middleware.audit_context.set_current_user",
            MagicMock(side_effect=RuntimeError("ctx down")),
        )

        credentials = SimpleNamespace(credentials="fake-token")
        result = await sec.get_current_user(credentials=credentials)

        assert result is user
        db.close.assert_called_once()


class TestRateLimitCleanup:
    def test_expired_keys_are_removed(self, monkeypatch):
        now = time.time()
        store = {
            "expired-key": [now - 1000.0],
            "empty-key": [],
            "fresh-key": [now],
        }
        monkeypatch.setattr(sec, "_rate_limit_store", store)
        monkeypatch.setattr(sec, "_last_rate_limit_cleanup", 0.0)

        sec._cleanup_expired_rate_keys(now)

        assert "expired-key" not in store
        assert "empty-key" not in store
        assert store["fresh-key"] == [now]
