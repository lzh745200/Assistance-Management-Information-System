"""app.api.v1.monitoring_legacy 覆盖率攻坚测试

直接 async 调用端点函数，覆盖 4 个端点的管理员/非管理员两条分支。
Query 默认值对象必须显式传真实值。
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

import app.api.v1.monitoring_legacy as m

ADMIN = SimpleNamespace(is_superuser=True)
NORMAL = SimpleNamespace(is_superuser=False)


class TestGetApiPerformance:
    async def test_non_superuser_forbidden(self):
        with pytest.raises(HTTPException) as exc_info:
            await m.get_api_performance(hours=24, endpoint=None, current_user=NORMAL, db=MagicMock())
        assert exc_info.value.status_code == 403

    async def test_success(self):
        stats = {"total_requests": 10, "avg_duration": 0.1}
        with patch.object(m.MonitoringService, "get_api_performance_stats", return_value=stats) as fn:
            result = await m.get_api_performance(hours=12, endpoint="/api/x", current_user=ADMIN, db=MagicMock())
        assert result["success"] is True
        assert result["data"] == stats
        assert fn.call_args.args[1:] == (12, "/api/x")


class TestGetEndpointStats:
    async def test_non_superuser_forbidden(self):
        with pytest.raises(HTTPException) as exc_info:
            await m.get_endpoint_stats(hours=24, limit=20, current_user=NORMAL, db=MagicMock())
        assert exc_info.value.status_code == 403

    async def test_success(self):
        stats = [{"endpoint": "/api/x", "count": 3}]
        with patch.object(m.MonitoringService, "get_endpoint_stats", return_value=stats) as fn:
            result = await m.get_endpoint_stats(hours=6, limit=5, current_user=ADMIN, db=MagicMock())
        assert result["success"] is True
        assert result["data"] == {"endpoints": stats}
        assert fn.call_args.args[1:] == (6, 5)


class TestGetErrorStats:
    async def test_non_superuser_forbidden(self):
        with pytest.raises(HTTPException) as exc_info:
            await m.get_error_stats(hours=24, current_user=NORMAL, db=MagicMock())
        assert exc_info.value.status_code == 403

    async def test_success(self):
        stats = {"error_count": 2, "error_rate": 0.01}
        with patch.object(m.MonitoringService, "get_error_stats", return_value=stats) as fn:
            result = await m.get_error_stats(hours=48, current_user=ADMIN, db=MagicMock())
        assert result["success"] is True
        assert result["data"] == stats
        assert fn.call_args.args[1:] == (48,)


class TestGetResourceStats:
    async def test_non_superuser_forbidden(self):
        with pytest.raises(HTTPException) as exc_info:
            await m.get_resource_stats(current_user=NORMAL)
        assert exc_info.value.status_code == 403

    async def test_success(self):
        stats = {"cpu_percent": 12.3, "memory_percent": 45.6}
        with patch.object(m.MonitoringService, "get_resource_stats", return_value=stats) as fn:
            result = await m.get_resource_stats(current_user=ADMIN)
        assert result["success"] is True
        assert result["data"] == stats
        fn.assert_called_once_with()
