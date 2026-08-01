"""包版本服务。

``check_version`` / ``get_version`` / ``_parse_version`` 为占位 stub，
未接入路由（此前为硬编码 ``"1.0.0"`` 占位实现）。调用方需使用
``app.core.config.Settings.PROJECT_VERSION``（权威版本源）。
``parse_version`` 为纯工具函数，保留可用。
"""

import logging
from typing import Optional, Tuple, Union

logger = logging.getLogger(__name__)


class PackageVersionService:
    """包版本服务。

    .. note::
        ``check_version`` / ``get_version`` / ``_parse_version`` 为占位 stub，
        未接入路由。权威版本源为 ``backend/app/core/config.py`` 的
        ``Settings.PROJECT_VERSION``。
    """

    @staticmethod
    def get_current_version() -> str:
        """返回当前应用版本号（来自 config，权威来源）。"""
        from app.core.config import settings

        version = getattr(settings, "PROJECT_VERSION", "0.0.0")
        return str(version)

    @staticmethod
    def _parse_version(v: Union[str, Tuple[int, ...], None]) -> Union[Tuple[int, ...], str, None]:
        """解析版本号字符串为整数元组；非数字版本返回原值。

        纯工具函数，无副作用。

        Raises:
            NotImplementedError: 占位 stub，未接入路由。
        """
        raise NotImplementedError(
            "PackageVersionService._parse_version 是占位 stub（未接入路由），"
            "真实版本解析请使用 parse_version 工具函数。"
        )

    @staticmethod
    def parse_version(v):
        """解析版本号字符串为整数元组；非数字版本返回原值。

        纯工具函数，保留可用（与 ``_parse_version`` stub 无关）。
        """
        if v is None:
            return None
        if isinstance(v, tuple):
            return tuple(int(x) for x in v)
        if isinstance(v, int):
            return (v,)
        try:
            parts = str(v).split(".")
            if all(p.isdigit() for p in parts):
                return tuple(int(p) for p in parts)
        except Exception as e:  # noqa: BLE001
            logger.debug("版本号解析失败 '%s': %s", v, e)
        return v

    @classmethod
    def check_version(cls) -> dict:
        """检查当前版本状态。

        Raises:
            NotImplementedError: 占位 stub，未接入路由。
        """
        raise NotImplementedError(
            "PackageVersionService.check_version 是占位 stub（未接入路由），"
            "当前版本请读取 app.core.config.Settings.PROJECT_VERSION。"
        )

    @classmethod
    def get_version(cls) -> str:
        """Backward-compat：返回当前应用版本号。

        Raises:
            NotImplementedError: 占位 stub，未接入路由。
        """
        raise NotImplementedError(
            "PackageVersionService.get_version 是占位 stub（未接入路由），"
            "当前版本请读取 app.core.config.Settings.PROJECT_VERSION。"
        )