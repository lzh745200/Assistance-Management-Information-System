"""
API 错误处理测试
"""
import pytest
import os
from fastapi import HTTPException
from app.utils import api_error

class TestRaiseAPIError:
    """raise_api_error 函数测试"""

    def test_raise_api_error_production(self, monkeypatch):
        """测试生产环境错误"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        api_error._is_production = None
        
        with pytest.raises(HTTPException) as exc_info:
            api_error.raise_api_error("操作失败", Exception("内部错误详情"))
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "操作失败"
        assert "内部错误详情" not in exc_info.value.detail

    def test_raise_api_error_development(self, monkeypatch):
        """测试开发环境错误"""
        monkeypatch.setenv("ENVIRONMENT", "development")
        api_error._is_production = None
        
        with pytest.raises(HTTPException) as exc_info:
            api_error.raise_api_error("操作失败", Exception("内部错误详情"))
        
        assert exc_info.value.status_code == 500
        assert "内部错误详情" in exc_info.value.detail

    def test_raise_api_error_custom_status(self):
        """测试自定义状态码"""
        with pytest.raises(HTTPException) as exc_info:
            api_error.raise_api_error("未找到", status_code=404)
        
        assert exc_info.value.status_code == 404

    def test_raise_api_error_no_exception(self):
        """测试无异常情况"""
        with pytest.raises(HTTPException) as exc_info:
            api_error.raise_api_error("简单错误")
        
        assert exc_info.value.detail == "简单错误"

class TestHandleServiceError:
    """handle_service_error 函数测试"""

    def test_handle_service_error(self):
        """测试服务错误处理"""
        with pytest.raises(HTTPException) as exc_info:
            api_error.handle_service_error("获取数据", Exception("数据库连接失败"))
        
        assert "获取数据失败" in exc_info.value.detail

    def test_handle_service_error_custom_status(self):
        """测试自定义状态码的服务错误"""
        with pytest.raises(HTTPException) as exc_info:
            api_error.handle_service_error("验证用户", Exception("权限不足"), status_code=403)
        
        assert exc_info.value.status_code in (200, 401, 403, 404)

class TestSafeAPICall:
    """safe_api_call 装饰器测试"""

    @pytest.mark.asyncio
    async def test_safe_api_call_success(self):
        """测试成功调用"""
        @api_error.safe_api_call("测试操作")
        async def success_func():
            return {"result": "success"}
        
        result = await success_func()
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_safe_api_call_exception(self):
        """测试异常处理"""
        @api_error.safe_api_call("测试操作")
        async def fail_func():
            raise Exception("测试异常")
        
        with pytest.raises(HTTPException):
            await fail_func()

    @pytest.mark.asyncio
    async def test_safe_api_call_preserves_http_exception(self):
        """测试保留HTTPException"""
        @api_error.safe_api_call("测试操作")
        async def http_fail():
            raise HTTPException(status_code=404, detail="未找到")
        
        with pytest.raises(HTTPException) as exc_info:
            await http_fail()
        
        assert exc_info.value.status_code == 404

    def test_safe_api_call_sync(self):
        """测试同步函数"""
        @api_error.safe_api_call("同步测试")
        def sync_func():
            return "result"
        
        result = sync_func()
        assert result == "result"

class TestAPIErrorHandler:
    """APIErrorHandler 上下文管理器测试"""

    def test_context_manager_success(self):
        """测试成功情况"""
        with api_error.APIErrorHandler("测试操作"):
            result = 1 + 1
        
        assert result == 2

    def test_context_manager_exception(self):
        """测试异常情况"""
        with pytest.raises(HTTPException):
            with api_error.APIErrorHandler("测试操作"):
                raise Exception("测试异常")

class TestIsProduction:
    """is_production 函数测试"""

    def test_is_production_true(self, monkeypatch):
        """测试生产环境"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        api_error._is_production = None
        
        assert api_error.is_production() is True

    def test_is_production_false(self, monkeypatch):
        """测试开发环境"""
        monkeypatch.setenv("ENVIRONMENT", "development")
        api_error._is_production = None
        
        assert api_error.is_production() is False
