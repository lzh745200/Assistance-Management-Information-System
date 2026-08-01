"""覆盖 app.middleware.body_size_limit 缺口：非法 content-length 头的容错放行。"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.middleware.body_size_limit import BodySizeLimitMiddleware


class TestInvalidContentLength:
    async def test_non_numeric_content_length_is_ignored(self):
        # content-length 无法解析为 int → except (ValueError, TypeError) 放行（行 75-76）
        mw = BodySizeLimitMiddleware(app=MagicMock(), max_body_size=1024)
        request = SimpleNamespace(
            method="POST",
            url=SimpleNamespace(path="/api/v1/dashboard"),
            headers={"content-length": "not-a-number", "content-type": "application/json"},
        )
        call_next = AsyncMock(return_value="response-ok")

        result = await mw.dispatch(request, call_next)

        assert result == "response-ok"
        call_next.assert_awaited_once_with(request)

    async def test_oversize_content_length_returns_413(self):
        # 对照组：超限但合法的 content-length 仍返回 413
        mw = BodySizeLimitMiddleware(app=MagicMock(), max_body_size=1024)
        request = SimpleNamespace(
            method="POST",
            url=SimpleNamespace(path="/api/v1/dashboard"),
            headers={"content-length": "2048", "content-type": "application/json"},
        )
        call_next = AsyncMock(return_value="response-ok")

        result = await mw.dispatch(request, call_next)

        assert result.status_code == 413
        call_next.assert_not_awaited()
