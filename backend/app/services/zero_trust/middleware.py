"""零信任中间件（ASGI）。

本中间件在请求到达业务逻辑前执行轻量级设备指纹记录，
适用于 ``app.add_middleware(ZeroTrustMiddleware)`` 集成。

功能：
1. 从请求头提取 User-Agent 和客户端 IP，生成设备指纹。
2. 将设备指纹存入 ``scope["state"]`` 供后续依赖项使用。
3. 对被封禁设备返回 403 JSON 响应。

设计原则：
- **不阻断正常请求**：仅对已知封禁设备拦截，其余透传。
- **无外部 I/O 阻塞**：指纹生成基于哈希计算，缓存查询走 SimpleCache（内存）。
- **可安全注册或跳过**：即使不注册到应用也不影响功能。
"""

import json
import logging
from typing import Callable

from app.services.zero_trust.device_fingerprint import (
    DeviceRiskLevel,
    device_fingerprint_service,
)

logger = logging.getLogger(__name__)


class ZeroTrustMiddleware:
    """零信任 ASGI 中间件。

    在 ASGI 请求处理链中执行设备指纹验证。对于 HTTP 请求，
    提取设备指纹并存入 scope state；对被封禁设备返回 403。

    用法::

        from app.services.zero_trust.middleware import ZeroTrustMiddleware
        app.add_middleware(ZeroTrustMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """处理 ASGI 请求。

        对非 HTTP 请求（如 WebSocket、lifespan）直接透传。
        对 HTTP 请求执行设备指纹验证后透传。
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 提取请求头信息
        headers = dict(scope.get("headers", []))
        user_agent = headers.get(b"user-agent", b"").decode("utf-8", errors="replace")
        client = scope.get("client")
        ip_address = client[0] if client else "unknown"

        # 生成设备指纹
        fingerprint = device_fingerprint_service.generate_fingerprint(
            user_agent, ip_address
        )

        # 将指纹存入 scope state 供后续依赖使用
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["device_fingerprint"] = fingerprint

        # 检查设备是否被封禁
        if device_fingerprint_service.is_device_blocked(fingerprint):
            logger.warning("已封禁设备访问被拦截: fingerprint=%s, ip=%s", fingerprint, ip_address)
            await self._send_403(send, "设备已被封禁，请联系管理员")
            return

        # 记录调试日志
        trust_score = device_fingerprint_service.get_trust_score(fingerprint)
        if trust_score < 0.3:
            logger.info(
                "低信任设备访问: fingerprint=%s, ip=%s, score=%.2f",
                fingerprint, ip_address, trust_score,
            )

        await self.app(scope, receive, send)

    @staticmethod
    async def _send_403(send, message: str):
        """发送 403 JSON 响应。"""
        body = json.dumps({"detail": message}, ensure_ascii=False).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [
                (b"content-type", b"application/json; charset=utf-8"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({"type": "http.response.body", "body": body})
