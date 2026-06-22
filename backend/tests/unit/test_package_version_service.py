"""Tests for app.services.package_version_service

check_version / get_version / _parse_version 已改为 raise NotImplementedError
（此前为硬编码 "1.0.0" 占位 stub，未接入路由）。
parse_version 为纯工具函数，保留可用。
"""

import pytest
from app.services.package_version_service import PackageVersionService


class TestCheckVersion:
    def test_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            PackageVersionService.check_version()


class TestParseVersion:
    def test_valid_numeric_version_returns_tuple(self):
        result = PackageVersionService.parse_version("1.2.3")
        assert result == (1, 2, 3)

    def test_valid_two_part_version(self):
        result = PackageVersionService.parse_version("3.4")
        assert result == (3, 4)

    def test_single_digit_version(self):
        result = PackageVersionService.parse_version("5")
        assert result == (5,)

    def test_non_numeric_version_returns_original(self):
        result = PackageVersionService.parse_version("1.2.3a")
        assert result == "1.2.3a"

    def test_empty_string_returns_empty_string(self):
        result = PackageVersionService.parse_version("")
        assert result == ""

    def test_none_returns_none(self):
        # None.split() raises AttributeError, caught by except Exception → returns None
        result = PackageVersionService.parse_version(None)
        assert result is None

    def test_special_chars_returns_original(self):
        result = PackageVersionService.parse_version("v1.0")
        assert result == "v1.0"


class TestGetVersion:
    def test_raises_not_implemented(self):
        svc = PackageVersionService()
        with pytest.raises(NotImplementedError):
            svc.get_version()


class TestParseVersionCompat:
    def test_raises_not_implemented(self):
        svc = PackageVersionService()
        with pytest.raises(NotImplementedError):
            svc._parse_version("1.2.3")
