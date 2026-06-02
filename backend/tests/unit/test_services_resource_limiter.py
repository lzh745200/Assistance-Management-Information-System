"""
资源限流服务测试
"""
import pytest

class TestResourceLimiter:
    """测试资源限流器"""

    def test_resource_limiter_import(self):
        """测试资源限流器导入"""
        from app.services.resource_limiter import ResourceLimiter
        assert ResourceLimiter is not None
