"""补齐 app.services.zero_trust.device_fingerprint 覆盖率缺口（187/315/372-374/378-380 行）."""
from unittest.mock import MagicMock, patch

from app.services.zero_trust.device_fingerprint import (
    DeviceFingerprint,
    DeviceFingerprintService,
    DeviceRiskLevel,
)

_MOD = "app.services.zero_trust.device_fingerprint"


def _device(**overrides):
    device = DeviceFingerprint(
        fingerprint_id="fp-b4b",
        user_agent="TestAgent/1.0",
        ip_address="10.0.0.1",
    )
    for key, value in overrides.items():
        setattr(device, key, value)
    return device


class TestCalculateTrustScore:
    def test_many_fonts_adds_bonus(self):
        svc = DeviceFingerprintService()
        with_fonts = _device(fonts=[f"font-{i}" for i in range(6)])
        without_fonts = _device(fonts=[])
        assert svc._calculate_trust_score(with_fonts) > svc._calculate_trust_score(without_fonts)


class TestGetTrustScore:
    def test_cache_hit_returns_cached_score(self):
        svc = DeviceFingerprintService()
        with patch(f"{_MOD}.default_cache") as cache:
            cache.get.return_value = 0.77
            assert svc.get_trust_score("fp-cached") == 0.77


class TestVerifyDevice:
    def _svc(self, device):
        svc = DeviceFingerprintService()
        svc.is_device_blocked = MagicMock(return_value=False)
        svc.get_device = MagicMock(return_value=device)
        svc._save_device = MagicMock()
        return svc

    def test_high_risk_requires_challenge(self):
        device = _device(risk_level=DeviceRiskLevel.HIGH, trust_score=0.4)
        result = self._svc(device).verify_device("fp-b4b", "user-1")
        assert result["requires_challenge"] is True
        assert result["reason"] == "设备风险较高，需要额外验证"
        assert result["verified"] is False

    def test_low_trust_score_requires_mfa(self):
        device = _device(risk_level=DeviceRiskLevel.MEDIUM, trust_score=0.2)
        result = self._svc(device).verify_device("fp-b4b", "user-1")
        assert result["requires_mfa"] is True
        assert result["reason"] == "设备信任评分不足"
        assert result["verified"] is False
