"""双因素认证服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch

class TestGenerateSecret:
    def test_generates_base32(self):
        from app.services.two_factor_service import TwoFactorService
        secret = TwoFactorService.generate_secret()
        assert isinstance(secret, str)
        assert len(secret) >= 16

    def test_secrets_are_different(self):
        from app.services.two_factor_service import TwoFactorService
        s1 = TwoFactorService.generate_secret()
        s2 = TwoFactorService.generate_secret()
        assert s1 != s2

class TestGenerateBackupCodes:
    def test_default_count(self):
        from app.services.two_factor_service import TwoFactorService
        codes = TwoFactorService.generate_backup_codes()
        assert len(codes) == 10
        for c in codes:
            assert isinstance(c, str)

    def test_custom_count(self):
        from app.services.two_factor_service import TwoFactorService
        codes = TwoFactorService.generate_backup_codes(5)
        assert len(codes) == 5

    def test_codes_unique(self):
        from app.services.two_factor_service import TwoFactorService
        codes = TwoFactorService.generate_backup_codes(20)
        assert len(set(codes)) == 20

class TestVerifyTotp:
    def test_verify_totp_method_exists(self):
        from app.services.two_factor_service import TwoFactorService
        svc = TwoFactorService()
        assert callable(svc.verify_totp)
