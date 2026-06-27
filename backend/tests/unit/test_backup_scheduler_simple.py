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
        # Mock scheduler - running 是只读属性，patch 整个 scheduler
        mock_job = MagicMock()
        mock_job.id = "test_job"
        mock_job.name = "Test Job"
        mock_job.next_run_time = datetime.now()

        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        mock_scheduler.get_jobs.return_value = [mock_job]

        with patch('app.services.backup_scheduler.scheduler', mock_scheduler):
            result = get_scheduler_status()

        assert isinstance(result, dict)
        assert "running" in result
        assert "jobs" in result

    def test_get_scheduler_status_no_jobs(self):
        """测试获取调度器状态 - 无任务"""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_scheduler.get_jobs.return_value = []

        with patch('app.services.backup_scheduler.scheduler', mock_scheduler):
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
