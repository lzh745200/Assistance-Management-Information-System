"""覆盖 app.core.prophet_status 缺口：prophet 导入抛出非 ImportError 的异常分支。

模块级 try/except 在 import 时执行，因此在一个全新的模块对象中重新执行源码
（不触碰 sys.modules 中已加载的 app.core.prophet_status，避免影响其他测试）。
"""
import importlib.util
import sys
from pathlib import Path

import app.core.prophet_status as _loaded


class _Boom:
    """任意属性访问都抛 RuntimeError（模拟 prophet 包初始化阶段崩溃）。"""

    def __getattr__(self, name):
        raise RuntimeError("prophet native lib broken")


class TestProphetInitException:
    def test_non_import_error_during_prophet_import_is_logged_and_disabled(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "prophet", _Boom())
        spec = importlib.util.spec_from_file_location(
            "app.core.prophet_status", Path(_loaded.__file__)
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.FORCE_DISABLE is False
        assert module.PROPHET_AVAILABLE is False
        assert module.is_prophet_available() is False
