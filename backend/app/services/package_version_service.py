"""Package version service（stub — 未接入路由）。

.. warning::
    本服务为占位实现，**尚未被任何路由调用**。``check_version`` / ``get_version``
    此前硬编码返回 ``"1.0.0"``，与项目实际版本（``config.PROJECT_VERSION``，
    当前为 ``1.4.1``）不符，存在误导风险。

    完整实现（读取 ``config.PROJECT_VERSION`` 并与最新发布版本比对）超出本次
    BugFix 范围。为避免被误用，硬编码方法显式抛出 :class:`NotImplementedError`。

    ``parse_version`` 为纯工具函数（无副作用、无硬编码），保留可用。
"""

import logging

logger = logging.getLogger(__name__)

_NOT_IMPL_MSG = (
    "PackageVersionService.%s 尚未实现（版本检查为硬编码占位 stub，未接入路由）。"
    "完整实现应读取 config.PROJECT_VERSION 并与最新发布版本比对，"
    "超出本次 BugFix 范围。"
)


class PackageVersionService:
    """包版本服务（部分未实现）。

    ``parse_version`` 为可用的纯工具函数；``check_version`` / ``get_version``
    为硬编码 stub，已标注 :class:`NotImplementedError`。
    """

    @staticmethod
    def check_version():
        """检查版本（未实现 — 此前硬编码返回 "1.0.0"）。

        Raises:
            NotImplementedError: 本方法为硬编码占位，未接入路由。
        """
        raise NotImplementedError(_NOT_IMPL_MSG % "check_version")

    @staticmethod
    def parse_version(v):
        """Parse version string, return tuple of ints or original.

        纯工具函数，无副作用，保留可用。
        """
        try:
            parts = v.split(".")
            if all(p.isdigit() for p in parts):
                return tuple(int(p) for p in parts)
        except Exception:
            pass
        return v


def get_version(self):
    """Backward-compat（未实现 — 此前硬编码返回 "1.0.0"）。

    Raises:
        NotImplementedError: 本方法为硬编码占位，未接入路由。
    """
    raise NotImplementedError(_NOT_IMPL_MSG % "get_version")


def _parse_version(self, v):
    """Backward-compat（未实现 — 此前为无操作透传）。

    Raises:
        NotImplementedError: 本方法为占位透传，未接入路由。
    """
    raise NotImplementedError(_NOT_IMPL_MSG % "_parse_version")


PackageVersionService.get_version = get_version
PackageVersionService._parse_version = _parse_version
