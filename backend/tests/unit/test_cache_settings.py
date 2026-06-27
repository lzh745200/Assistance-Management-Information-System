"""Tests for app/core/cache_settings.py — 目标 100% 覆盖。"""
from unittest.mock import patch

import pytest

from app.core.cache_settings import CacheSettings, get_cache_settings


class TestCacheSettingsDefaults:
    def test_default_values(self):
        s = CacheSettings()
        assert s.enabled is True
        assert s.backend == "memory"
        assert s.default_ttl == 3600
        assert s.redis_url is None
        assert s.max_entries == 10_000

    def test_custom_values(self):
        s = CacheSettings(enabled=False, backend="redis", redis_url="redis://localhost", max_entries=5000)
        assert s.enabled is False
        assert s.backend == "redis"
        assert s.redis_url == "redis://localhost"
        assert s.max_entries == 5000


class TestCacheSettingsFromSettings:
    def test_from_settings_success(self):
        mock_settings = type("Settings", (), {
            "CACHE_ENABLED": False,
            "CACHE_BACKEND": "redis",
            "CACHE_DEFAULT_TTL": 7200,
            "REDIS_URL": "redis://prod",
            "CACHE_MAX_SIZE": 20000,
        })()
        with patch("app.core.config.settings", mock_settings, create=True):
            s = CacheSettings.from_settings()
            assert s.enabled is False
            assert s.backend == "redis"
            assert s.default_ttl == 7200
            assert s.redis_url == "redis://prod"
            assert s.max_entries == 20000

    def test_from_settings_uses_defaults_for_missing(self):
        mock_settings = type("Settings", (), {})()
        with patch("app.core.config.settings", mock_settings, create=True):
            s = CacheSettings.from_settings()
            assert s.enabled is True
            assert s.backend == "memory"
            assert s.default_ttl == 3600
            assert s.max_entries == 10_000

    def test_from_settings_fallback_on_exception(self):
        """模拟 from_settings 内部 import 失败的 except 分支。"""
        import app.core.config as cfg
        saved = getattr(cfg, "settings", None)
        try:
            if hasattr(cfg, "settings"):
                del cfg.settings
            from app.core.cache_settings import CacheSettings as CS
            s = CS.from_settings()
            assert s.enabled is True
            assert s.backend == "memory"
        finally:
            if saved is not None:
                cfg.settings = saved


class TestGetCacheSettings:
    def test_returns_singleton(self):
        instance = get_cache_settings()
        assert isinstance(instance, CacheSettings)
        assert get_cache_settings() is instance
