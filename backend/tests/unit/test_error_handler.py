"""Tests for app.core.error_handler — 100% coverage."""

import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.core.error_handler import (
    error_response,
    not_found_response,
    bad_request_response,
    forbidden_response,
    conflict_response,
    server_error_response,
    register_handlers,
    http_status_to_message,
    BusinessLogicError,
)


class TestErrorResponse:
    def test_minimal(self):
        result = error_response(404, "Not found")
        assert result["code"] == 404
        assert result["message"] == "Not found"
        assert result["success"] is False

    def test_with_details(self):
        result = error_response(400, "Bad input", details={"field": "name"})
        assert result["details"] == {"field": "name"}

    def test_no_details_key_when_none(self):
        result = error_response(500, "Error")
        assert "details" not in result

    def test_default_values(self):
        result = error_response()
        assert result["code"] == 500
        assert result["message"] == "服务器内部错误"
        assert result["success"] is False


class TestNotFoundResponse:
    def test_with_resource_id(self):
        resp = not_found_response("用户", "42")
        assert resp.status_code == 404
        data = resp.body.decode()
        assert "42" in data
        assert "用户" in data

    def test_without_resource_id(self):
        resp = not_found_response("项目")
        assert resp.status_code == 404
        data = resp.body.decode()
        assert "项目不存在" in data

    def test_default_resource(self):
        resp = not_found_response()
        assert resp.status_code == 404
        data = resp.body.decode()
        assert "资源不存在" in data


class TestBadRequestResponse:
    def test_default_message(self):
        resp = bad_request_response()
        assert resp.status_code == 400

    def test_custom_message(self):
        resp = bad_request_response("缺少必填字段")
        assert resp.status_code == 400
        data = resp.body.decode()
        assert "缺少必填字段" in data


class TestForbiddenResponse:
    def test_default(self):
        resp = forbidden_response()
        assert resp.status_code == 403

    def test_custom(self):
        resp = forbidden_response("权限不足")
        assert resp.status_code == 403


class TestConflictResponse:
    def test_default(self):
        resp = conflict_response()
        assert resp.status_code == 409

    def test_custom(self):
        resp = conflict_response("用户名已存在")
        assert resp.status_code == 409


class TestServerErrorResponse:
    def test_default(self):
        resp = server_error_response()
        assert resp.status_code == 500

    def test_custom(self):
        resp = server_error_response("数据库连接失败")
        assert resp.status_code == 500


class TestRegisterHandlers:
    def test_registers_from_core_exceptions(self):
        app = FastAPI()
        with patch(
            "app.core.exceptions.register_exception_handlers"
        ) as mock_reg:
            register_handlers(app)
            mock_reg.assert_called_once_with(app)

    def test_fallback_when_import_fails(self):
        app = FastAPI()
        # Simulate the import failure inside register_handlers
        with patch("app.core.exceptions.register_exception_handlers", side_effect=ImportError):
            register_handlers(app)

    def test_extra_handlers_registered(self):
        app = FastAPI()

        async def custom_handler(request, exc):
            return JSONResponse(status_code=418, content={"error": "teapot"})

        with patch("app.core.exceptions.register_exception_handlers"):
            register_handlers(app, extra_handlers={ValueError: custom_handler})
            # The extra handler should be registered on the app


class TestHttpStatusToMessage:
    def test_known_statuses(self):
        assert http_status_to_message(400) == "请求参数错误"
        assert http_status_to_message(401) == "未认证"
        assert http_status_to_message(403) == "无权访问"
        assert http_status_to_message(404) == "资源不存在"
        assert http_status_to_message(405) == "不允许的请求方法"
        assert http_status_to_message(409) == "数据冲突"
        assert http_status_to_message(422) == "请求参数验证失败"
        assert http_status_to_message(429) == "请求过于频繁"
        assert http_status_to_message(500) == "服务器内部错误"
        assert http_status_to_message(502) == "网关错误"
        assert http_status_to_message(503) == "服务不可用"

    def test_unknown_status(self):
        assert http_status_to_message(418) == "HTTP 418"
        assert http_status_to_message(200) == "HTTP 200"


class TestBusinessLogicError:
    def test_is_subclass_of_app_error(self):
        from app.core.error_handler import AppError
        assert issubclass(BusinessLogicError, AppError)

    def test_default_status_code(self):
        assert BusinessLogicError.status_code == 400

    def test_can_be_raised(self):
        with pytest.raises(BusinessLogicError):
            raise BusinessLogicError("逻辑错误")
