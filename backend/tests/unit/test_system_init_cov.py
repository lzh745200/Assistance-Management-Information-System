"""app.api.v1.system.__init__ 覆盖率攻坚测试

18 个子路由的 try/import/except 容错结构：
- 正常路径：18 个子模块全部 import 成功（已被全量套件覆盖）
- 异常路径（本文件）：sys.modules 注入 None 使 import 失败后 reload 包，
  18 个 except 分支逐一执行 logger.warning（覆盖 42-43 ... 178-179 全部 18 组）
"""

import importlib
import sys
from unittest.mock import patch

SUBMODULES = [
    "admin", "audit", "backup", "cache", "config_package", "env",
    "error_report", "health", "help", "i18n", "init", "metrics",
    "monitor", "system", "system_config", "tasks", "update_logs", "zero_trust",
]


def test_all_router_import_failures_degrade(caplog):
    import app.api.v1.system as system_pkg

    injected = {f"app.api.v1.system.{name}": None for name in SUBMODULES}
    with patch.dict(sys.modules, injected):
        with caplog.at_level("WARNING", logger="app.api.v1.system"):
            importlib.reload(system_pkg)

    # 18 个子模块各产生一条加载失败警告
    for name in SUBMODULES:
        assert any(f"加载 system.{name} 路由失败" in r.message for r in caplog.records), name

    # 恢复真实现（patch.dict 已还原 sys.modules，重新 reload 回正常路由）
    importlib.reload(system_pkg)
    assert len(system_pkg.router.routes) > 0


def test_normal_reload_registers_routers():
    """正常路径：全部子路由注册成功（防御 reload 后状态完好）"""
    import app.api.v1.system as system_pkg

    importlib.reload(system_pkg)
    assert len(system_pkg.router.routes) > 0
