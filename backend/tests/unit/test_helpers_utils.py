"""Tests for app/utils/helpers.py — 100% coverage."""

from datetime import date, datetime
from unittest.mock import patch, MagicMock
import json

import pytest

from app.utils.helpers import (
    generate_random_string,
    generate_code,
    hash_string,
    safe_json_loads,
    safe_json_dumps,
    format_datetime,
    format_date,
    parse_datetime,
    parse_date,
    paginate,
    clean_dict,
    deep_merge,
)


# ============================================================================
# generate_random_string
# ============================================================================

class TestGenerateRandomString:
    def test_default_length(self):
        result = generate_random_string()
        assert len(result) == 16

    def test_custom_length(self):
        result = generate_random_string(32)
        assert len(result) == 32

    def test_zero_length(self):
        result = generate_random_string(0)
        assert result == ""

    def test_contains_only_alphanumeric(self):
        result = generate_random_string(1000)
        assert all(c.isascii() and c.isalnum() for c in result)


# ============================================================================
# generate_code
# ============================================================================

class TestGenerateCode:
    @patch("app.utils.helpers.datetime")
    def test_generates_code(self, mock_dt):
        mock_dt.now.return_value.year = 2025
        result = generate_code("PROJ", 42)
        assert result == "PROJ20250042"

    @patch("app.utils.helpers.datetime")
    def test_zero_padding(self, mock_dt):
        mock_dt.now.return_value.year = 2025
        result = generate_code("FUND", 1)
        assert result == "FUND20250001"

    @patch("app.utils.helpers.datetime")
    def test_large_id(self, mock_dt):
        mock_dt.now.return_value.year = 2025
        result = generate_code("CASE", 99999)
        assert result == "CASE202599999"


# ============================================================================
# hash_string
# ============================================================================

class TestHashString:
    def test_sha256_hash(self):
        result = hash_string("hello")
        assert len(result) == 64
        assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_empty_string(self):
        result = hash_string("")
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_deterministic(self):
        assert hash_string("test") == hash_string("test")


# ============================================================================
# safe_json_loads
# ============================================================================

class TestSafeJsonLoads:
    def test_empty_string_returns_default(self):
        assert safe_json_loads("") is None
        assert safe_json_loads("", []) == []

    def test_none_returns_default(self):
        assert safe_json_loads(None) is None
        assert safe_json_loads(None, {}) == {}

    def test_valid_json_object(self):
        result = safe_json_loads('{"a": 1}')
        assert result == {"a": 1}

    def test_valid_json_array(self):
        result = safe_json_loads('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_invalid_json_with_comma_returns_list(self):
        result = safe_json_loads("a,b,c")
        assert result == ["a", "b", "c"]

    def test_invalid_json_with_comma_and_spaces(self):
        result = safe_json_loads(" a , b , c ")
        assert result == ["a", "b", "c"]

    def test_invalid_json_no_comma_returns_default(self):
        result = safe_json_loads("just a string")
        assert result is None

    def test_invalid_json_with_default(self):
        result = safe_json_loads("not json", default=[])
        assert result == []

    def test_type_error_fallback(self):
        result = safe_json_loads("a,b", default=[])
        assert result == ["a", "b"]


# ============================================================================
# safe_json_dumps
# ============================================================================

class TestSafeJsonDumps:
    def test_dict(self):
        result = safe_json_dumps({"a": 1, "b": 2})
        assert result == '{"a":1,"b":2}' or result == '{"a": 1, "b": 2}'

    def test_list(self):
        result = safe_json_dumps([1, 2, 3])
        assert json.loads(result) == [1, 2, 3]

    def test_ensure_ascii_false(self):
        result = safe_json_dumps({"name": "中文"})
        assert "中文" in result

    def test_datetime_serialization(self):
        d = datetime(2025, 1, 15, 10, 30, 0)
        result = safe_json_dumps(d)
        assert "2025" in result

    def test_type_error_returns_empty_dict(self):
        class Unserializable:
            def __str__(self):
                raise TypeError("cannot str")
        result = safe_json_dumps(Unserializable())
        assert result == "{}"


# ============================================================================
# format_datetime
# ============================================================================

class TestFormatDatetime:
    def test_none_returns_empty(self):
        assert format_datetime(None) == ""

    def test_valid_datetime(self):
        dt = datetime(2025, 6, 15, 14, 30, 0)
        assert format_datetime(dt) == "2025-06-15 14:30:00"

    def test_custom_format(self):
        dt = datetime(2025, 6, 15, 14, 30, 0)
        assert format_datetime(dt, "%Y/%m/%d") == "2025/06/15"


# ============================================================================
# format_date
# ============================================================================

class TestFormatDate:
    def test_none_returns_empty(self):
        assert format_date(None) == ""

    def test_valid_date(self):
        d = date(2025, 6, 15)
        assert format_date(d) == "2025-06-15"

    def test_custom_format(self):
        d = date(2025, 6, 15)
        assert format_date(d, "%d-%m-%Y") == "15-06-2025"


# ============================================================================
# parse_datetime
# ============================================================================

class TestParseDatetime:
    def test_none_returns_none(self):
        assert parse_datetime(None) is None

    def test_empty_string_returns_none(self):
        assert parse_datetime("") is None

    def test_valid_string(self):
        result = parse_datetime("2025-06-15 14:30:00")
        assert result == datetime(2025, 6, 15, 14, 30, 0)

    def test_invalid_format_returns_none(self):
        result = parse_datetime("not a date")
        assert result is None

    def test_custom_format(self):
        result = parse_datetime("2025/06/15 14:30", "%Y/%m/%d %H:%M")
        assert result == datetime(2025, 6, 15, 14, 30)


# ============================================================================
# parse_date
# ============================================================================

class TestParseDate:
    def test_none_returns_none(self):
        assert parse_date(None) is None

    def test_empty_string_returns_none(self):
        assert parse_date("") is None

    def test_valid_string(self):
        result = parse_date("2025-06-15")
        assert result == date(2025, 6, 15)

    def test_invalid_format_returns_none(self):
        result = parse_date("not a date")
        assert result is None

    def test_custom_format(self):
        result = parse_date("15/06/2025", "%d/%m/%Y")
        assert result == date(2025, 6, 15)


# ============================================================================
# paginate
# ============================================================================

class TestPaginate:
    def test_empty_list(self):
        result = paginate([])
        assert result == {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 0,
        }

    def test_single_page(self):
        items = [1, 2, 3]
        result = paginate(items, page_size=20)
        assert result["items"] == [1, 2, 3]
        assert result["total"] == 3
        assert result["total_pages"] == 1

    def test_multi_page(self):
        items = list(range(25))
        result = paginate(items, page=2, page_size=10)
        assert result["items"] == [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        assert result["total"] == 25
        assert result["total_pages"] == 3

    def test_partial_last_page(self):
        items = list(range(12))
        result = paginate(items, page=2, page_size=10)
        assert result["items"] == [10, 11]
        assert result["total_pages"] == 2

    def test_page_out_of_range(self):
        items = [1, 2, 3]
        result = paginate(items, page=10, page_size=10)
        assert result["items"] == []
        assert result["total"] == 3


# ============================================================================
# clean_dict
# ============================================================================

class TestCleanDict:
    def test_removes_none_values(self):
        result = clean_dict({"a": 1, "b": None, "c": "hello", "d": None})
        assert result == {"a": 1, "c": "hello"}

    def test_no_none_values(self):
        result = clean_dict({"a": 1, "b": "hello"})
        assert result == {"a": 1, "b": "hello"}

    def test_all_none_returns_empty(self):
        result = clean_dict({"a": None, "b": None})
        assert result == {}

    def test_empty_dict(self):
        result = clean_dict({})
        assert result == {}


# ============================================================================
# deep_merge
# ============================================================================

class TestDeepMerge:
    def test_basic_merge(self):
        base = {"a": 1, "b": 2}
        update = {"b": 3, "c": 4}
        result = deep_merge(base, update)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_dict_merge(self):
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        update = {"a": {"y": 99, "z": 100}}
        result = deep_merge(base, update)
        assert result == {"a": {"x": 1, "y": 99, "z": 100}, "b": 3}

    def test_overwrite_non_dict_with_dict(self):
        base = {"a": 1}
        update = {"a": {"b": 2}}
        result = deep_merge(base, update)
        assert result == {"a": {"b": 2}}

    def test_original_unchanged(self):
        base = {"a": 1}
        update = {"a": 2}
        deep_merge(base, update)
        assert base == {"a": 1}

    def test_empty_update(self):
        base = {"a": 1}
        result = deep_merge(base, {})
        assert result == {"a": 1}

    def test_empty_base(self):
        result = deep_merge({}, {"a": 1})
        assert result == {"a": 1}
