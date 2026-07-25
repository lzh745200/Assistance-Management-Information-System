"""app.api.v1.__init__ 覆盖率攻坚测试

- 11 个显式 try 块的 except 降级分支：sys.modules 注入 None 使 import 失败
- 业务循环的 import 失败（except）与"无 router 对象"（else）两分支：
  分别注入 None 与无 router 的假模块
- 每次异常 reload 后都再正常 reload 恢复真实路由，避免污染其他测试
"""

import importlib
import logging
import sys
import types
from unittest.mock import patch

PKG = "app.api.v1"

EXPLICIT_SUBMODULES = [
    "auth", "data", "import_export", "system",
    "system.health", "system.env", "system.config_package",
    "monitoring.metrics", "monitoring.secrets", "monitoring.data_tier",
    "messages",
]


def _reload():
    import app.api.v1 as v1_pkg
    importlib.reload(v1_pkg)
    return v1_pkg


def test_explicit_import_failures_degrade(caplog, monkeypatch):
    import app.api.v1.monitoring as monitoring_pkg
    import app.api.v1.system as system_pkg

    # “from 父包 import 子模块”形式的导入在父包属性已存在时会绕过
    # sys.modules 中的 None 注入（_handle_fromlist 先查 hasattr），
    # 导致 ImportError 不触发。删除父包属性，强制走子模块导入。
    for _name in ("metrics", "secrets", "data_tier"):
        monkeypatch.delattr(monitoring_pkg, _name, raising=False)
    for _name in ("health", "env", "config_package"):
        monkeypatch.delattr(system_pkg, _name, raising=False)

    injected = {f"{PKG}.{name}": None for name in EXPLICIT_SUBMODULES}
    with patch.dict(sys.modules, injected):
        with caplog.at_level(logging.WARNING, logger=PKG):
            _reload()
    for name in EXPLICIT_SUBMODULES:
        assert any(f"加载 {name} 路由失败" in r.message for r in caplog.records), name
    # 恢复真实现（patch.dict 已还原 sys.modules，重新 reload 回正常路由）
    pkg = _reload()
    assert len(pkg.api_v1_router.routes) > 0


def test_business_module_import_failure_and_no_router(caplog):
    dummy = types.ModuleType(f"{PKG}.policy")  # 无 router 属性 → else 分支
    injected = {f"{PKG}.funds": None, f"{PKG}.policy": dummy}
    with patch.dict(sys.modules, injected):
        with caplog.at_level(logging.WARNING, logger=PKG):
            pkg = _reload()
    assert any("加载 funds 路由失败" in r.message for r in caplog.records)
    assert any("模块 policy 中未找到 router 对象" in r.message for r in caplog.records)
    assert any("以下路由模块加载失败" in r.message for r in caplog.records)
    assert "funds" in pkg._failed_modules
    assert "policy" in pkg._failed_modules
    # 恢复
    pkg = _reload()
    assert pkg._failed_modules == []


def test_normal_reload_registers_all_business_modules():
    pkg = _reload()
    assert pkg._loaded_count == len(pkg._BUSINESS_MODULES)
    assert len(pkg.api_v1_router.routes) > 0
