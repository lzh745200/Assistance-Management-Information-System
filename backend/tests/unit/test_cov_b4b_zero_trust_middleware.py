"""补齐 app.services.zero_trust.middleware 覆盖率缺口（13-28 行：模块导入、实例化、__call__ 抛错）."""
import pytest

from app.services.zero_trust.middleware import ZeroTrustMiddleware


class TestZeroTrustMiddleware:
    def test_init_stores_app(self):
        app = object()
        assert ZeroTrustMiddleware(app).app is app

    @pytest.mark.asyncio
    async def test_call_raises_not_implemented(self):
        middleware = ZeroTrustMiddleware(object())
        with pytest.raises(NotImplementedError):
            await middleware({"type": "http"}, None, None)
