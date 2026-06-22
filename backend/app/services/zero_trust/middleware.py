"""零信任中间件（stub）。

.. warning::
    本模块为自动生成的占位实现，**尚未接入应用中间件链**（项目中无任何
    ``add_middleware(ZeroTrustMiddleware)`` 调用）。``__call__`` 此前直接
    透传请求，等同于无任何零信任校验。为避免被误用为"已启用"，此处显式
    抛出 :class:`NotImplementedError` 暴露问题。

    完整的零信任中间件实现超出了本次 BugFix 的范围，需后续专项实现：
    在请求处理前执行设备验证、信任分评估、动态策略检查等。
"""

import logging

logger = logging.getLogger(__name__)


class ZeroTrustMiddleware:
    """零信任中间件（未实现）。

    真正的实现应在请求到达业务逻辑前，执行设备绑定校验、信任评分、
    动态访问策略评估等零信任检查，而非直接透传。
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """处理 ASGI 请求。

        Raises:
            NotImplementedError: 本中间件尚未实现，不应被注册到应用。
        """
        raise NotImplementedError(
            "ZeroTrustMiddleware 尚未实现（零信任中间件为占位 stub，"
            "未接入应用中间件链）。请勿在此实现就绪前通过 add_middleware 启用。"
        )
