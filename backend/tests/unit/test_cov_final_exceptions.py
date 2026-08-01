"""覆盖 app.core.exceptions 缺口：Pydantic 验证错误与全局异常处理器。"""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.exceptions import register_exception_handlers


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    class _Payload(BaseModel):
        x: int

    @app.get("/trigger-validation")
    def _trigger_validation():
        # 端点内抛出 pydantic.ValidationError（非 FastAPI 请求校验错误）
        _Payload(x="not-an-int")

    @app.get("/trigger-generic")
    def _trigger_generic():
        raise RuntimeError("boom")

    return app


class TestExceptionHandlers:
    def test_pydantic_validation_error_returns_422(self):
        client = TestClient(_build_app(), raise_server_exceptions=False)
        resp = client.get("/trigger-validation")
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == 422
        assert body["message"] == "请求参数验证失败"
        assert body["success"] is False
        assert isinstance(body["errors"], list) and body["errors"]

    def test_unhandled_exception_returns_500(self):
        client = TestClient(_build_app(), raise_server_exceptions=False)
        resp = client.get("/trigger-generic")
        assert resp.status_code == 500
        assert resp.json() == {"code": 500, "message": "服务器内部错误", "success": False}
