"""补齐 app.services.zero_trust（__init__.py）覆盖率缺口（30-34/39/44 行）."""
from types import SimpleNamespace

from app.services.zero_trust import (
    DeviceFingerprintService,
    DeviceRiskLevel,
    device_fingerprint_service,
)


class TestGenerateFingerprint:
    def test_with_client_host(self):
        request = SimpleNamespace(
            headers={"user-agent": "TestAgent/1.0", "accept": "text/html"},
            client=SimpleNamespace(host="192.168.0.1"),
        )
        fingerprint = DeviceFingerprintService.generate_fingerprint(request)
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 32

    def test_without_client_uses_unknown(self):
        request = SimpleNamespace(headers={}, client=None)
        fingerprint = DeviceFingerprintService.generate_fingerprint(request)
        assert len(fingerprint) == 32


class TestAssessRisk:
    def test_returns_low(self):
        assert DeviceFingerprintService.assess_risk("any") is DeviceRiskLevel.LOW


class TestIsTrusted:
    def test_singleton_returns_true(self):
        assert device_fingerprint_service.is_trusted("any") is True
