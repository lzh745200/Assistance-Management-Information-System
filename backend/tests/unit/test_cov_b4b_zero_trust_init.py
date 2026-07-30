"""补齐 app.services.zero_trust（__init__.py）覆盖率。

测试向后兼容封装类 DeviceFingerprintService 的便捷方法：
- generate_fingerprint_from_request（从请求对象生成指纹）
- assess_risk（根据指纹评估风险等级）
- is_trusted（快速判断设备是否可信）
"""
from types import SimpleNamespace
from unittest.mock import patch

from app.services.zero_trust import (
    DeviceFingerprint,
    DeviceFingerprintService,
    DeviceRiskLevel,
    device_fingerprint_service,
)
from app.services.zero_trust.device_fingerprint import (
    DeviceFingerprintService as RealService,
)


class TestGenerateFingerprintFromRequest:
    """测试 generate_fingerprint_from_request 静态方法。"""

    def test_with_client_host(self):
        request = SimpleNamespace(
            headers={"user-agent": "TestAgent/1.0", "accept": "text/html"},
            client=SimpleNamespace(host="192.168.0.1"),
        )
        fingerprint = DeviceFingerprintService.generate_fingerprint_from_request(request)
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 32

    def test_without_client_uses_unknown(self):
        request = SimpleNamespace(headers={}, client=None)
        fingerprint = DeviceFingerprintService.generate_fingerprint_from_request(request)
        assert len(fingerprint) == 32

    def test_with_missing_attributes(self):
        """request 对象缺少 headers/client 属性时不崩溃。"""
        request = SimpleNamespace()
        fingerprint = DeviceFingerprintService.generate_fingerprint_from_request(request)
        assert len(fingerprint) == 32

    def test_with_none_client(self):
        request = SimpleNamespace(headers={"user-agent": "Agent"}, client=None)
        fingerprint = DeviceFingerprintService.generate_fingerprint_from_request(request)
        assert len(fingerprint) == 32

    def test_consistent_output(self):
        """相同输入产生相同指纹。"""
        request = SimpleNamespace(
            headers={"user-agent": "Agent/1.0"},
            client=SimpleNamespace(host="10.0.0.1"),
        )
        fp1 = DeviceFingerprintService.generate_fingerprint_from_request(request)
        fp2 = DeviceFingerprintService.generate_fingerprint_from_request(request)
        assert fp1 == fp2


class TestAssessRisk:
    """测试 assess_risk 方法。"""

    def test_unknown_device_returns_low(self):
        """未知设备默认返回 LOW（向后兼容旧行为）。"""
        assert device_fingerprint_service.assess_risk("nonexistent_fp") is DeviceRiskLevel.LOW

    def test_known_device_returns_actual_level(self):
        """已知设备返回其实际风险等级。"""
        svc = DeviceFingerprintService()
        # 创建一个已知设备
        svc.create_device_record(
            "test_fp_assess", "Mozilla/5.0 selenium", "1.1.1.1",
        )
        # selenium 在 UA 中 → 信任分降低 → HIGH 或 CRITICAL
        risk = svc.assess_risk("test_fp_assess")
        assert risk in (DeviceRiskLevel.HIGH, DeviceRiskLevel.CRITICAL, DeviceRiskLevel.MEDIUM)


class TestIsTrusted:
    """测试 is_trusted 方法。"""

    def test_unknown_device_returns_true(self):
        """未知设备默认可信（信任分 0.5 ≥ 0.5）。"""
        assert device_fingerprint_service.is_trusted("unknown_fp") is True

    def test_blocked_device_returns_false(self):
        """被封禁设备不可信。"""
        svc = DeviceFingerprintService()
        svc.create_device_record("blocked_fp_test", "Mozilla/5.0", "1.1.1.1")
        svc.block_device("blocked_fp_test", "Test block")
        assert svc.is_trusted("blocked_fp_test") is False

    def test_trusted_device_returns_true(self):
        """信任分 ≥ 0.5 的设备可信。"""
        svc = DeviceFingerprintService()
        svc.create_device_record("trusted_fp_test", "Mozilla/5.0", "1.1.1.1")
        assert svc.is_trusted("trusted_fp_test") is True


class TestInheritance:
    """测试封装类正确继承真实实现。"""

    def test_is_subclass_of_real_service(self):
        assert issubclass(DeviceFingerprintService, RealService)

    def test_has_real_methods(self):
        svc = DeviceFingerprintService()
        assert hasattr(svc, "generate_fingerprint")
        assert hasattr(svc, "create_device_record")
        assert hasattr(svc, "verify_device")
        assert hasattr(svc, "block_device")

    def test_real_generate_fingerprint_still_works(self):
        """真实的 generate_fingerprint(user_agent, ip) 方法仍可用。"""
        svc = DeviceFingerprintService()
        fp = svc.generate_fingerprint("Mozilla/5.0", "192.168.1.1")
        assert len(fp) == 32


class TestModuleExports:
    """测试模块导出。"""

    def test_device_fingerprint_exported(self):
        from app.services.zero_trust import DeviceFingerprint as DF
        assert DF is not None

    def test_device_risk_level_exported(self):
        from app.services.zero_trust import DeviceRiskLevel as DRL
        assert DRL.LOW == "low"
        assert DRL.HIGH == "high"

    def test_singleton_is_correct_type(self):
        assert isinstance(device_fingerprint_service, DeviceFingerprintService)
