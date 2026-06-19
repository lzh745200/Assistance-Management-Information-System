"""
Comprehensive tests for backend/app/api/v1/system_config.py helper functions.

Covers all 3 async functions with 100% branch coverage:
- get_system_config(key)
- set_system_config(key, value)
- is_system_initialized()

All tests use mocked SessionLocal / SQLAlchemy sessions (no real database).
"""
import json
import pytest
import asyncio
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """Return a MagicMock simulating a SQLAlchemy Session from SessionLocal()."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    session.count.return_value = 0
    return session


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_row(key, value):
    """Build a mock SystemConfig ORM row with key and value attrs."""
    row = MagicMock()
    row.key = key
    row.value = value
    return row


# ============================================================================
# get_system_config
# ============================================================================

class TestGetSystemConfig:
    """Tests for async def get_system_config(key)."""

    # -- single key, found ---------------------------------------------------

    def test_single_key_found_json(self, mock_db):
        """Valid JSON value -> parsed and returned as {key: dict}."""
        mock_db.first.return_value = _make_row("theme", '{"dark":true}')

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("theme"))

        assert result == {"theme": {"dark": True}}

    def test_single_key_found_plain_string(self, mock_db):
        """Non-JSON string -> raw string returned (json.loads fails)."""
        mock_db.first.return_value = _make_row("app", "MyApp")

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("app"))

        assert result == {"app": "MyApp"}

    def test_single_key_found_none_value(self, mock_db):
        """value is None (falsy) -> returns {key: None}."""
        mock_db.first.return_value = _make_row("flag", None)

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("flag"))

        assert result == {"flag": None}

    def test_single_key_found_empty_string_value(self, mock_db):
        """value is '' (falsy) -> returns {key: None}."""
        mock_db.first.return_value = _make_row("blank", "")

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("blank"))

        assert result == {"blank": None}

    def test_single_key_json_decode_error(self, mock_db):
        """Invalid JSON -> JSONDecodeError caught -> raw string returned."""
        mock_db.first.return_value = _make_row("bad", "{not valid json")

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("bad"))

        assert result == {"bad": "{not valid json"}

    def test_single_key_typeerror_fallback(self, mock_db):
        """json.loads(int) raises TypeError -> raw value returned."""
        mock_db.first.return_value = _make_row("count", 42)

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("count"))

        assert result == {"count": 42}

    # -- single key, not found -----------------------------------------------

    def test_single_key_not_found(self, mock_db):
        """No row matches -> returns {}."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("nonexistent"))

        assert result == {}

    # -- all keys (key=None / falsy key) -------------------------------------

    def test_all_keys_mixed_values(self, mock_db):
        """key=None -> all rows returned; JSON parsed, plain strings raw."""
        mock_db.all.return_value = [
            _make_row("theme", '{"dark":true}'),
            _make_row("locale", "zh-CN"),
            _make_row("empty", None),
        ]

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config())

        assert result == {
            "theme": {"dark": True},
            "locale": "zh-CN",
            "empty": None,
        }

    def test_all_keys_empty_list(self, mock_db):
        """No config rows -> returns {}."""
        mock_db.all.return_value = []

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config())

        assert result == {}

    def test_all_keys_with_json_decode_error(self, mock_db):
        """In all() path, a bad-JSON row falls back to raw string."""
        mock_db.all.return_value = [
            _make_row("good", '{"a":1}'),
            _make_row("bad", "{oops"),
        ]

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config())

        assert result == {
            "good": {"a": 1},
            "bad": "{oops",
        }

    def test_all_keys_with_typeerror_fallback(self, mock_db):
        """In all() path, json.loads(int) raises TypeError -> raw value."""
        mock_db.all.return_value = [
            _make_row("num", 123),
        ]

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config())

        assert result == {"num": 123}

    def test_empty_string_key_goes_to_all_path(self, mock_db):
        """Empty string '' is falsy, so 'if key:' is False -> all() path."""
        mock_db.all.return_value = [
            _make_row("k1", "v1"),
        ]

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config(""))

        # Because "" is falsy, the 'if key:' branch is skipped -> goes to all()
        assert result == {"k1": "v1"}

    # -- session lifecycle ---------------------------------------------------

    def test_db_close_called(self, mock_db):
        """Session is always closed via finally block."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            asyncio.run(get_system_config("any"))

        mock_db.close.assert_called_once()

    def test_db_close_called_even_on_query_exception(self, mock_db):
        """If query() raises, session.close() is still called (finally)."""
        mock_db.query.side_effect = RuntimeError("DB connection lost")

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            with pytest.raises(RuntimeError, match="DB connection lost"):
                asyncio.run(get_system_config("any"))

        mock_db.close.assert_called_once()


# ============================================================================
# set_system_config
# ============================================================================

class TestSetSystemConfig:
    """Tests for async def set_system_config(key, value)."""

    # -- insert new row ------------------------------------------------------

    def test_create_new_config_dict(self, mock_db):
        """New key with dict value -> row added with JSON-serialized string."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("theme", {"dark": True}))

        assert result is True
        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert added.key == "theme"
        assert json.loads(added.value) == {"dark": True}
        mock_db.commit.assert_called_once()

    def test_create_new_config_list(self, mock_db):
        """New key with list value -> JSON-serialized array."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("ips", ["127.0.0.1", "10.0.0.1"]))

        assert result is True
        added = mock_db.add.call_args[0][0]
        assert json.loads(added.value) == ["127.0.0.1", "10.0.0.1"]

    def test_create_new_config_int(self, mock_db):
        """New key with int value -> JSON-serialized number."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("max_retries", 3))

        assert result is True
        added = mock_db.add.call_args[0][0]
        assert json.loads(added.value) == 3

    def test_create_new_config_bool(self, mock_db):
        """New key with bool value -> JSON-serialized true/false."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("enabled", False))

        assert result is True
        added = mock_db.add.call_args[0][0]
        assert json.loads(added.value) is False

    def test_create_new_config_none(self, mock_db):
        """New key with None value -> JSON 'null'."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("flag", None))

        assert result is True
        added = mock_db.add.call_args[0][0]
        assert added.value == "null"

    def test_create_new_config_empty_key(self, mock_db):
        """Empty string key is accepted (no validation at this layer)."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("", "val"))

        assert result is True
        added = mock_db.add.call_args[0][0]
        assert added.key == ""

    # -- update existing row -------------------------------------------------

    def test_update_existing_config(self, mock_db):
        """Existing key -> row updated in-place, not re-added."""
        existing = _make_row("theme", '{"old":true}')
        mock_db.first.return_value = existing

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("theme", {"new": True}))

        assert result is True
        assert existing.value == '{"new": true}'
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()

    def test_update_existing_with_plain_string(self, mock_db):
        """Update existing row with a plain string (passed through as-is)."""
        existing = _make_row("name", "old_name")
        mock_db.first.return_value = existing

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("name", "new_name"))

        assert result is True
        assert existing.value == "new_name"

    def test_set_string_value_no_json_double_encoding(self, mock_db):
        """When value is already a string, no json.dumps() is applied."""
        existing = _make_row("str_key", "old")
        mock_db.first.return_value = existing

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("str_key", "just a string"))

        assert result is True
        assert existing.value == "just a string"

    def test_update_existing_with_none_value(self, mock_db):
        """Update existing row with None -> stored as 'null' string."""
        existing = _make_row("flag", "old_val")
        mock_db.first.return_value = existing

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("flag", None))

        assert result is True
        assert existing.value == "null"

    # -- failure paths -------------------------------------------------------

    def test_commit_failure_rollback_and_false(self, mock_db):
        """commit() raises -> rollback() called, returns False."""
        mock_db.first.return_value = None
        mock_db.commit.side_effect = Exception("DB error")

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("fail_key", "value"))

        assert result is False
        mock_db.rollback.assert_called_once()

    def test_add_failure_rollback_and_false(self, mock_db):
        """add() raises -> rollback() called, returns False."""
        mock_db.first.return_value = None
        mock_db.add.side_effect = Exception("add failed")

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("fail_key", "value"))

        assert result is False
        mock_db.rollback.assert_called_once()

    def test_query_failure_rollback_and_false(self, mock_db):
        """SessionLocal() succeeds but filter() raises -> rollback, False."""
        mock_db.filter.side_effect = Exception("query failed")

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("fail_key", "value"))

        assert result is False
        mock_db.rollback.assert_called_once()

    # -- session lifecycle ---------------------------------------------------

    def test_db_close_called(self, mock_db):
        """Session is closed via finally block on success."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            asyncio.run(set_system_config("key", "value"))

        mock_db.close.assert_called_once()

    def test_db_close_called_on_failure(self, mock_db):
        """Session is closed via finally block even after rollback."""
        mock_db.commit.side_effect = Exception("DB error")
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            asyncio.run(set_system_config("key", "value"))

        mock_db.close.assert_called_once()


# ============================================================================
# is_system_initialized
# ============================================================================

class TestIsSystemInitialized:
    """Tests for async def is_system_initialized()."""

    def test_initialized_true(self, mock_db):
        """count() > 0 -> True."""
        mock_db.count.return_value = 5

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import is_system_initialized
            result = asyncio.run(is_system_initialized())

        assert result is True

    def test_initialized_false(self, mock_db):
        """count() == 0 -> False."""
        mock_db.count.return_value = 0

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import is_system_initialized
            result = asyncio.run(is_system_initialized())

        assert result is False

    def test_initialized_count_one(self, mock_db):
        """count() == 1 -> True (boundary: exactly one row)."""
        mock_db.count.return_value = 1

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import is_system_initialized
            result = asyncio.run(is_system_initialized())

        assert result is True

    def test_db_close_called(self, mock_db):
        """Session is closed via finally."""
        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import is_system_initialized
            asyncio.run(is_system_initialized())

        mock_db.close.assert_called_once()

    def test_db_close_called_on_exception(self, mock_db):
        """Session is closed even if query() raises."""
        mock_db.query.side_effect = RuntimeError("DB connection lost")

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import is_system_initialized
            with pytest.raises(RuntimeError, match="DB connection lost"):
                asyncio.run(is_system_initialized())

        mock_db.close.assert_called_once()


# ============================================================================
# Round-trip / integration-style tests
# ============================================================================

class TestSetThenGet:
    """Set a value, then fetch it back through a separate mock session."""

    def test_set_dict_then_get(self, mock_db):
        """Set a JSON object -> verify captured add arg -> get returns it parsed."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(
                set_system_config("rt", {"nested": {"deep": [1, 2, 3]}})
            )

        assert result is True
        captured = mock_db.add.call_args[0][0]
        assert captured.key == "rt"
        assert json.loads(captured.value) == {"nested": {"deep": [1, 2, 3]}}

        # Now use a fresh mock that returns the captured row
        mock_db2 = MagicMock()
        mock_db2.query.return_value = mock_db2
        mock_db2.filter.return_value = mock_db2
        mock_db2.first.return_value = captured  # simulate the row we just inserted

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db2):
            from app.api.v1.system_config import get_system_config
            fetched = asyncio.run(get_system_config("rt"))

        assert fetched == {"rt": {"nested": {"deep": [1, 2, 3]}}}

    def test_set_plain_string_then_get(self, mock_db):
        """Set a plain string -> get returns it raw (no double encoding)."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            asyncio.run(set_system_config("greeting", "hello world"))

        captured = mock_db.add.call_args[0][0]

        mock_db2 = MagicMock()
        mock_db2.query.return_value = mock_db2
        mock_db2.filter.return_value = mock_db2
        mock_db2.first.return_value = captured

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db2):
            from app.api.v1.system_config import get_system_config
            fetched = asyncio.run(get_system_config("greeting"))

        # "hello world" is not valid JSON -> returned raw
        assert fetched == {"greeting": "hello world"}


class TestSetThenInitialized:
    """After inserting a config, is_system_initialized reports True."""

    def test_after_insert_is_initialized(self, mock_db):
        """Insert a row, then verify is_system_initialized() returns True."""
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            asyncio.run(set_system_config("boot_key", "done"))

        mock_db2 = MagicMock()
        mock_db2.query.return_value = mock_db2
        mock_db2.count.return_value = 1

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db2):
            from app.api.v1.system_config import is_system_initialized
            initialized = asyncio.run(is_system_initialized())

        assert initialized is True

    def test_no_inserts_not_initialized(self, mock_db):
        """No rows -> is_system_initialized() returns False."""
        mock_db.count.return_value = 0

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import is_system_initialized
            result = asyncio.run(is_system_initialized())

        assert result is False
