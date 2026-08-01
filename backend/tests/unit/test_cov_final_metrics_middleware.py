"""覆盖 app.middleware.metrics_middleware 缺口：
- 行 65：慢请求记录超过上限时截断
- 行 144-145：非 HTTP scope（websocket/lifespan）直接透传
"""
from unittest.mock import AsyncMock

from app.middleware.metrics_middleware import MetricsMiddleware, _MetricsStore


class TestSlowRequestTruncation:
    def test_slow_requests_truncated_to_max(self):
        store = _MetricsStore()
        store._max_slow = 2

        for i in range(3):
            store.record("GET", f"/path-{i}", 200, 2.5)  # 超过默认慢阈值 1.0s

        assert len(store._slow_requests) == 2
        # 保留最近的两条
        assert store._slow_requests[0][1] == "/path-1"
        assert store._slow_requests[1][1] == "/path-2"


class TestNonHttpScope:
    async def test_websocket_scope_passthrough(self):
        app = AsyncMock()
        mw = MetricsMiddleware(app)
        scope = {"type": "websocket", "path": "/ws"}
        receive, send = AsyncMock(), AsyncMock()

        await mw(scope, receive, send)

        app.assert_awaited_once_with(scope, receive, send)
