"""备份调度器单元测试"""
import pytest

def test_scheduler_exists():
    from app.services.backup_scheduler import scheduler
    assert scheduler is not None

def test_auto_backup_job_callable():
    from app.services.backup_scheduler import auto_backup_job
    assert callable(auto_backup_job)

def test_auto_backup_job_callable():
    from app.services.backup_scheduler import auto_backup_job
    assert callable(auto_backup_job)
