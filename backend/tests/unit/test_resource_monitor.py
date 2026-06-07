"""资源监控服务单元测试"""
import pytest

def test_psutil_available_boolean():
    from app.services.resource_monitor import PSUTIL_AVAILABLE
    assert isinstance(PSUTIL_AVAILABLE, bool)

def test_resource_monitor_instantiable():
    from app.services.resource_monitor import ResourceMonitor
    monitor = ResourceMonitor()
    assert monitor is not None

def test_get_current():
    from app.services.resource_monitor import ResourceMonitor
    monitor = ResourceMonitor()
    snapshot = monitor.get_current()
    assert snapshot is not None
    d = snapshot.to_dict()
    assert "cpu_percent" in d or "cpu" in str(d)

def test_get_system_info():
    from app.services.resource_monitor import ResourceMonitor
    monitor = ResourceMonitor()
    info = monitor.get_system_info()
    assert isinstance(info, dict)

def test_check_health():
    from app.services.resource_monitor import ResourceMonitor
    monitor = ResourceMonitor()
    health = monitor.check_health()
    assert isinstance(health, dict)

def test_get_history():
    from app.services.resource_monitor import ResourceMonitor
    monitor = ResourceMonitor()
    history = monitor.get_history(minutes=5)
    assert isinstance(history, list)
