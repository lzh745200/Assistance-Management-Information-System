"""Tests for app/utils/security_enhanced.py — 100% coverage."""
from unittest.mock import MagicMock, patch


class TestRateLimiter:
    """RateLimiter — compatibility wrapper delegating to resource_limiter singleton."""

    def test_import_and_instantiate_default(self):
        from app.utils.security_enhanced import RateLimiter
        rl = RateLimiter()
        assert rl.max_requests == 60
        assert rl.time_window == 60

    def test_instantiate_custom_values(self):
        from app.utils.security_enhanced import RateLimiter
        rl = RateLimiter(max_requests=100, time_window=30)
        assert rl.max_requests == 100
        assert rl.time_window == 30

    def test_is_allowed_delegates_to_resource_limiter(self):
        from app.utils.security_enhanced import RateLimiter
        with patch("app.utils.security_enhanced._rate_limiter") as mock_rl:
            mock_rl.is_allowed.return_value = True
            rl = RateLimiter()
            result = rl.is_allowed("client-1")
            assert result is True
            mock_rl.is_allowed.assert_called_once_with("client-1")

    def test_is_allowed_returns_false(self):
        from app.utils.security_enhanced import RateLimiter
        with patch("app.utils.security_enhanced._rate_limiter") as mock_rl:
            mock_rl.is_allowed.return_value = False
            rl = RateLimiter()
            result = rl.is_allowed("client-2")
            assert result is False

    def test_get_client_id_delegates_to_get_client_ip(self):
        from app.utils.security_enhanced import RateLimiter
        with patch("app.utils.security_enhanced.get_client_ip") as mock_ip:
            mock_ip.return_value = "192.168.1.1"
            request = MagicMock()
            result = RateLimiter.get_client_id(request)
            assert result == "192.168.1.1"
            mock_ip.assert_called_once_with(request)


class TestRateLimiterSingleton:
    """rate_limiter — module-level singleton."""

    def test_singleton_is_rate_limiter_instance(self):
        from app.utils.security_enhanced import rate_limiter, RateLimiter
        assert isinstance(rate_limiter, RateLimiter)
        assert rate_limiter.max_requests == 60

    def test_singleton_can_check_allowed(self):
        from app.utils.security_enhanced import rate_limiter
        with patch("app.utils.security_enhanced._rate_limiter") as mock_rl:
            mock_rl.is_allowed.return_value = True
            assert rate_limiter.is_allowed("test-key") is True


class TestPasswordValidator:
    """PasswordValidator — compatibility wrapper for PasswordPolicy."""

    def test_validate_password_strength_valid(self):
        from app.utils.security_enhanced import PasswordValidator
        valid, msg = PasswordValidator.validate_password_strength("StrongPass1!")
        assert valid is True
        assert msg == ""

    def test_validate_password_strength_too_short(self):
        from app.utils.security_enhanced import PasswordValidator
        valid, msg = PasswordValidator.validate_password_strength("Ab1!")
        assert valid is False
        assert "长度" in msg

    def test_generate_secure_password_default_length(self):
        from app.utils.security_enhanced import PasswordValidator
        pwd = PasswordValidator.generate_secure_password()
        assert len(pwd) >= 12

    def test_generate_secure_password_custom_length(self):
        from app.utils.security_enhanced import PasswordValidator
        pwd = PasswordValidator.generate_secure_password(length=16)
        assert len(pwd) >= 12


class TestInputSanitizer:
    """InputSanitizer — compatibility wrapper."""

    def test_sanitize_input_basic(self):
        from app.utils.security_enhanced import InputSanitizer
        result = InputSanitizer.sanitize_input("hello'; DROP TABLE;--")
        assert "'" not in result or "''" in result
        assert isinstance(result, str)

    def test_sanitize_input_empty(self):
        from app.utils.security_enhanced import InputSanitizer
        result = InputSanitizer.sanitize_input("")
        assert result == ""


class TestSecurityHeaders:
    """SecurityHeaders — static security headers."""

    def test_security_headers_constant(self):
        from app.utils.security_enhanced import SecurityHeaders
        headers = SecurityHeaders.SECURITY_HEADERS
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-XSS-Protection"] == "1; mode=block"
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_get_security_headers_returns_copy(self):
        from app.utils.security_enhanced import SecurityHeaders
        headers = SecurityHeaders.get_security_headers()
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert isinstance(headers, dict)
        assert len(headers) >= 4


class TestAllExports:
    """__all__ should export expected names."""

    def test_all_contains_expected(self):
        from app.utils.security_enhanced import __all__
        expected = {
            "RateLimiter",
            "rate_limiter",
            "PasswordValidator",
            "InputSanitizer",
            "SecurityHeaders",
            "check_rate_limit",
        }
        for name in expected:
            assert name in __all__, f"{name} missing from __all__"

    def test_check_rate_limit_reexported(self):
        from app.utils.security_enhanced import check_rate_limit
        import inspect
        assert inspect.isfunction(check_rate_limit)
