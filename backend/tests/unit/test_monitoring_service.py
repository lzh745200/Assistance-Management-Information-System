"""监控服务单元测试"""
import pytest

def test_service_exists():
    from app.services.monitoring_service import MonitoringService
    assert MonitoringService is not None

def test_instantiable():
    from app.services.monitoring_service import MonitoringService
    svc = MonitoringService()
    assert svc is not None
