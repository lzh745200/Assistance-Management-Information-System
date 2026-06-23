"""
Middleware模块全面测试
覆盖app/middleware/下的所有模块
"""

import pytest

from unittest.mock import patch, MagicMock
from unittest.mock import MagicMock  # auto-added

# 注：app.middleware.auth 与 app.middleware.rbac 模块已移除
# （认证改由 app.core.security 依赖注入；RBAC 改由 app.core.rbac 依赖注入），
# 原 TestAuthMiddleware / TestRBACMiddleware 死代码已删除。


class TestAuditMiddleware:
    """测试审计中间件"""

    def test_audit_middleware_import(self):
        """测试审计中间件导入"""
        from app.core.audit_middleware import AuditMiddleware
        assert AuditMiddleware is not None

    def test_audit_middleware_initialization(self):
        """测试审计中间件初始化"""
        from app.core.audit_middleware import AuditMiddleware
        middleware = AuditMiddleware(MagicMock())
        assert middleware is not None

class TestCacheMiddleware:
    """测试缓存中间件"""

    def test_cache_middleware_import(self):
        """测试缓存中间件导入"""
        from app.middleware.cache_middleware import CacheMiddleware
        assert CacheMiddleware is not None

    def test_cache_middleware_initialization(self):
        """测试缓存中间件初始化"""
        from app.middleware.cache_middleware import CacheMiddleware
        middleware = CacheMiddleware(MagicMock())
        assert middleware is not None

# 注：app.middleware.prometheus_middleware 模块已移除
# （指标改由 app.middleware.metrics_middleware 提供），
# 原 TestPrometheusMiddleware 死代码已删除。

class TestAuditContext:
    """测试审计上下文"""

    def test_audit_context_import(self):
        """测试审计上下文导入"""
        from app.middleware.audit_context import AuditContext
        assert AuditContext is not None

    def test_get_current_user(self):
        """测试获取当前用户"""
        from app.middleware.audit_context import get_current_user
        assert callable(get_current_user)

    def test_get_request_id(self):
        """测试获取请求ID"""
        from app.middleware.audit_context import get_request_id
        assert callable(get_request_id)

class TestAPIVersion:
    """测试API版本中间件"""

    def test_api_version_middleware_import(self):
        """测试API版本中间件导入"""
        from app.middleware.api_version import APIVersionMiddleware
        assert APIVersionMiddleware is not None

    def test_api_version_middleware_initialization(self):
        """测试API版本中间件初始化"""
        from app.middleware.api_version import APIVersionMiddleware
        middleware = APIVersionMiddleware(MagicMock())
        assert middleware is not None
