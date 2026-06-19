"""Tests for app.services.package_version_service - zero coverage → 100%"""

import pytest
from app.services.package_version_service import PackageVersionService


class TestCheckVersion:
    def test_returns_stub_version_dict(self):
        result = PackageVersionService.check_version()
        assert result == {"latest": "1.0.0", "current": "1.0.0"}


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

    def test_none_raises_attribute_error(self):
        with pytest.raises(AttributeError):
            PackageVersionService.parse_version(None)

    def test_special_chars_returns_original(self):
        result = PackageVersionService.parse_version("v1.0")
        assert result == "v1.0"


class TestGetVersion:
    def test_backward_compat_returns_dict_with_version_key(self):
        result = PackageVersionService.get_version()
        assert result == {"latest": "1.0.0", "current": "1.0.0", "version": "1.0.0"}

    def test_backward_compat_is_callable_as_static(self):
        result = PackageVersionService.get_version()
        assert isinstance(result, dict)
        assert "version" in result


class TestParseVersionCompat:
    def test_backward_compat_returns_input_unchanged(self):
        assert PackageVersionService._parse_version("1.2.3") == "1.2.3"
        assert PackageVersionService._parse_version("anything") == "anything"
        assert PackageVersionService._parse_version(42) == 42
