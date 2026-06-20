"""日志模块 — 向后兼容入口。

P2-1 整改：移除旧的 SafeLogger 实现（与 logging_config.py 重复），统一走
``logging_config.configure_logging`` / ``init_logging``。本模块仅保留模块级
``logger`` 句柄，供 ``from app.core.logging import logger`` 的既有调用方使用。

新代码应直接 ``import logging; logger = logging.getLogger(__name__)``，
或调用 ``app.core.logging_config.init_logging()`` 完成初始化。
"""
import logging

# 兼容既有 ``from app.core.logging import logger`` 调用方
logger = logging.getLogger("assistance_management")


def init_logging() -> None:
    """代理到 logging_config.init_logging（统一入口）。"""
    from app.core.logging_config import init_logging as _init

    _init()


__all__ = ["logger", "init_logging"]
