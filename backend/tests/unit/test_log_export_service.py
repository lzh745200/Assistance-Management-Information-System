"""日志导出服务单元测试"""
import pytest

def test_service_exists():
    from app.services.log_export_service import LogExportService
    assert LogExportService is not None
