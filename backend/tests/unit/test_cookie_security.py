"""Tests for app.core.cookie_security (100% coverage)."""

from unittest.mock import MagicMock

from fastapi import Response

from app.core.cookie_security import delete_cookie, get_cookie_domain, set_secure_cookie


class TestSetSecureCookie:
    def test_default_params(self):
        response = MagicMock(spec=Response)
        set_secure_cookie(response, "session_id", "abc123")
        response.set_cookie.assert_called_once_with(
            key="session_id",
            value="abc123",
            max_age=86400,
            path="/",
            domain=None,
            secure=True,
            httponly=True,
            samesite="lax",
        )

    def test_custom_all_params(self):
        response = MagicMock(spec=Response)
        set_secure_cookie(
            response,
            "k",
            "v",
            max_age=100,
            path="/app",
            domain="example.com",
            secure=False,
            httponly=False,
            samesite="strict",
        )
        response.set_cookie.assert_called_once_with(
            key="k",
            value="v",
            max_age=100,
            path="/app",
            domain="example.com",
            secure=False,
            httponly=False,
            samesite="strict",
        )


class TestDeleteCookie:
    def test_default_params(self):
        response = MagicMock(spec=Response)
        delete_cookie(response, "session_id")
        response.delete_cookie.assert_called_once_with(key="session_id", path="/", domain=None)

    def test_with_domain_and_path(self):
        response = MagicMock(spec=Response)
        delete_cookie(response, "k", path="/app", domain="example.com")
        response.delete_cookie.assert_called_once_with(key="k", path="/app", domain="example.com")


class TestGetCookieDomain:
    def test_empty_string(self):
        assert get_cookie_domain("") is None

    def test_none(self):
        assert get_cookie_domain(None) is None

    def test_localhost(self):
        assert get_cookie_domain("localhost") is None

    def test_localhost_with_port(self):
        assert get_cookie_domain("localhost:8080") is None

    def test_loopback_ipv4(self):
        assert get_cookie_domain("127.0.0.1") is None
        assert get_cookie_domain("127.0.0.1:3000") is None

    def test_loopback_ipv6_becomes_empty(self):
        result = get_cookie_domain("::1")
        assert result == ""

    def test_bare_ip_rejected(self):
        assert get_cookie_domain("192.168.1.1") is None
        assert get_cookie_domain("10.0.0.1") is None
        assert get_cookie_domain("172.16.0.1") is None

    def test_normal_hostname(self):
        assert get_cookie_domain("example.com") == "example.com"

    def test_hostname_with_port(self):
        assert get_cookie_domain("example.com:443") == "example.com"

    def test_subdomain(self):
        assert get_cookie_domain("api.example.com") == "api.example.com"

    def test_ipv6_returns_first_segment(self):
        result = get_cookie_domain("2001:db8::1")
        assert result == "2001"
