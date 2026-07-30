"""补齐 app.services.zero_trust.middleware 覆盖率。

测试 ZeroTrustMiddleware 的 ASGI 中间件行为：
- 非 HTTP 请求透传
- HTTP 请求提取设备指纹并存入 scope state
- 已封禁设备返回 403
- 正常请求透传
"""
import json

import pytest

from app.services.zero_trust.middleware import ZeroTrustMiddleware
from app.services.zero_trust.device_fingerprint import device_fingerprint_service


class TestZeroTrustMiddlewareInit:
    def test_init_stores_app(self):
        app = object()
        assert ZeroTrustMiddleware(app).app is app


class TestZeroTrustMiddlewareNonHttp:
    """非 HTTP 请求直接透传。"""

    @pytest.mark.asyncio
    async def test_websocket_passthrough(self):
        called = False

        async def app(scope, receive, send):
            nonlocal called
            called = True

        middleware = ZeroTrustMiddleware(app)
        await middleware({"type": "websocket"}, None, None)
        assert called is True

    @pytest.mark.asyncio
    async def test_lifespan_passthrough(self):
        called = False

        async def app(scope, receive, send):
            nonlocal called
            called = True

        middleware = ZeroTrustMiddleware(app)
        await middleware({"type": "lifespan"}, None, None)
        assert called is True


class TestZeroTrustMiddlewareHttp:
    """HTTP 请求处理。"""

    def _make_scope(self, path="/api/v1/test", user_agent="TestAgent/1.0", client_ip="10.0.0.1"):
        return {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [
                (b"user-agent", user_agent.encode()),
            ],
            "client": (client_ip, 12345),
        }

    @pytest.mark.asyncio
    async def test_normal_request_passthrough(self):
        """正常请求透传并记录设备指纹。"""
        received_scope = None

        async def app(scope, receive, send):
            nonlocal received_scope
            received_scope = scope

        middleware = ZeroTrustMiddleware(app)
        scope = self._make_scope()
        await middleware(scope, None, None)

        assert received_scope is not None
        assert "device_fingerprint" in received_scope.get("state", {})
        fp = received_scope["state"]["device_fingerprint"]
        assert isinstance(fp, str)
        assert len(fp) == 32

    @pytest.mark.asyncio
    async def test_no_client_uses_unknown_ip(self):
        """无 client 信息时 IP 设为 unknown。"""
        received_scope = None

        async def app(scope, receive, send):
            nonlocal received_scope
            received_scope = scope

        middleware = ZeroTrustMiddleware(app)
        scope = self._make_scope()
        del scope["client"]
        await middleware(scope, None, None)

        assert received_scope is not None
        assert "device_fingerprint" in received_scope["state"]

    @pytest.mark.asyncio
    async def test_no_headers(self):
        """无 headers 时不崩溃。"""
        received_scope = None

        async def app(scope, receive, send):
            nonlocal received_scope
            received_scope = scope

        middleware = ZeroTrustMiddleware(app)
        scope = {"type": "http", "method": "GET", "path": "/"}
        await middleware(scope, None, None)

        assert received_scope is not None
        assert "device_fingerprint" in received_scope.get("state", {})

    @pytest.mark.asyncio
    async def test_blocked_device_returns_403(self):
        """被封禁设备返回 403 响应。"""
        sent_responses = []

        async def app(scope, receive, send):
            # 不应该到达这里
            sent_responses.append("app_called")

        # 先创建并封禁一个设备
        fp = device_fingerprint_service.generate_fingerprint("BlockedAgent/1.0", "10.0.0.99")
        device_fingerprint_service.block_device(fp, "Test block")
        try:
            middleware = ZeroTrustMiddleware(app)
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/test",
                "headers": [(b"user-agent", b"BlockedAgent/1.0")],
                "client": ("10.0.0.99", 12345),
            }

            async def mock_send(message):
                sent_responses.append(message)

            await middleware(scope, None, mock_send)

            # app 不应该被调用
            assert "app_called" not in sent_responses

            # 应该有 403 响应
            start = sent_responses[0]
            assert start["type"] == "http.response.start"
            assert start["status"] == 403

            body = sent_responses[1]
            assert body["type"] == "http.response.body"
            body_text = json.loads(body["body"].decode("utf-8"))
            assert "设备已被封禁" in body_text["detail"]
        finally:
            # 清理封禁
            from app.services.zero_trust.device_fingerprint import default_cache
            default_cache.delete(f"device_block:{fp}")

    @pytest.mark.asyncio
    async def test_existing_state_preserved(self):
        """scope 中已有 state 字典时保留已有内容。"""
        received_scope = None

        async def app(scope, receive, send):
            nonlocal received_scope
            received_scope = scope

        middleware = ZeroTrustMiddleware(app)
        scope = self._make_scope()
        scope["state"] = {"existing_key": "existing_value"}
        await middleware(scope, None, None)

        assert received_scope["state"]["existing_key"] == "existing_value"
        assert "device_fingerprint" in received_scope["state"]
