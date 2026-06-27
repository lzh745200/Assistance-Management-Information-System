"""Tests for app/core/auth_root.py — 目标 100% 覆盖。"""
from app.core.auth_root import auth_router, get_auth_router


class TestAuthRoot:
    def test_router_prefix(self):
        assert auth_router.prefix == "/auth"

    def test_router_tags(self):
        assert "认证" in auth_router.tags

    def test_get_auth_router_returns_singleton(self):
        assert get_auth_router() is auth_router
