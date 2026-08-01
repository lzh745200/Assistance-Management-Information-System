"""app.api.v1.system.system 覆盖补全 — 非 Windows 平台重启走 os.execv 分支 (line 237).

测试不真正触发重启：捕获 background task 闭包后在 mock 环境下执行。
"""
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.api.v1.system.system import restart_system


class TestRestartSystem:
    async def test_non_windows_restart_uses_execv(self, monkeypatch):
        background_tasks = MagicMock(name="background_tasks")
        user = SimpleNamespace(id=1, username="admin", role="admin", is_superuser=True)

        resp = await restart_system(background_tasks=background_tasks, delay_seconds=1, current_user=user)
        assert resp["success"] is True

        # 取出延迟执行的重启闭包，在 mock 环境下执行
        restart_fn = background_tasks.add_task.call_args[0][0]

        execv = MagicMock(name="execv")
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setattr("time.sleep", lambda s: None)
        monkeypatch.setattr("os.execv", execv)
        monkeypatch.setattr("os._exit", lambda code: None)
        from app.core.cache import cache_manager
        monkeypatch.setattr(cache_manager, "close", lambda: None)

        restart_fn()

        # line 237: 非 win32 平台通过 os.execv 替换进程镜像完成重启
        execv.assert_called_once()
        args = execv.call_args[0]
        assert args[0] == sys.executable
        assert args[1][0] == sys.executable
