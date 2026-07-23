"""
简化测试 - app.services.backup_scheduler
使用 conftest fixtures
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.backup_scheduler import (
    auto_backup_job, kpi_precalculate_job, anomaly_detection_job,
    todo_reminder_job, weekly_report_job,
    start_backup_scheduler, stop_backup_scheduler, get_scheduler_status
)

class TestSchedulerFunctionsExist:
    """测试调度器函数存在性"""

    def test_imports(self):
        """测试可以导入所有函数"""
        assert callable(auto_backup_job)
        assert callable(kpi_precalculate_job)
        assert callable(anomaly_detection_job)
        assert callable(todo_reminder_job)
        assert callable(weekly_report_job)
        assert callable(start_backup_scheduler)
        assert callable(stop_backup_scheduler)
        assert callable(get_scheduler_status)

class TestSchedulerControlOnly:
    """只测试调度器控制函数（不需要数据库）"""

    def test_get_scheduler_status(self):
        """测试获取调度器状态"""
        import threading
        mock_timer = MagicMock(spec=threading.Timer)
        mock_timer.name = "test_job"
        mock_timer.is_alive.return_value = True

        with patch('app.services.backup_scheduler._scheduler_started', True), \
             patch('app.services.backup_scheduler._timers', [mock_timer]):
            result = get_scheduler_status()

        assert isinstance(result, dict)
        assert result["running"] is True
        assert len(result["jobs"]) == 1
        assert result["jobs"][0]["id"] == "test_job"

    def test_get_scheduler_status_no_jobs(self):
        """测试获取调度器状态 - 无任务"""
        with patch('app.services.backup_scheduler._scheduler_started', False), \
             patch('app.services.backup_scheduler._timers', []):
            result = get_scheduler_status()

        assert result["running"] is False
        assert result["jobs"] == []

class TestSchedulerJobSignatures:
    """测试任务函数签名"""

    @pytest.mark.asyncio
    async def test_auto_backup_job_signature(self):
        """测试自动备份任务签名"""
        # 检查是协程函数
        import inspect
        assert inspect.iscoroutinefunction(auto_backup_job)

    @pytest.mark.asyncio
    async def test_kpi_job_signature(self):
        """测试KPI任务签名"""
        import inspect
        assert inspect.iscoroutinefunction(kpi_precalculate_job)

    @pytest.mark.asyncio
    async def test_anomaly_job_signature(self):
        """测试异常检测任务签名"""
        import inspect
        assert inspect.iscoroutinefunction(anomaly_detection_job)

    @pytest.mark.asyncio
    async def test_todo_job_signature(self):
        """测试待办任务签名"""
        import inspect
        assert inspect.iscoroutinefunction(todo_reminder_job)

    @pytest.mark.asyncio
    async def test_weekly_job_signature(self):
        """测试周报任务签名"""
        import inspect
        assert inspect.iscoroutinefunction(weekly_report_job)
