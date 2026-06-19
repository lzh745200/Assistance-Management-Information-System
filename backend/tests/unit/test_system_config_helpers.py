"""Tests for app.api.v1.system_config helper functions (not route handlers)."""

import pytest
import json
import asyncio
from unittest.mock import MagicMock, patch, call


@pytest.fixture
def mock_db():
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    session.count.return_value = 0
    return session


class TestGetSystemConfig:
    def test_get_single_key_found_json(self, mock_db):
        config_row = MagicMock()
        config_row.value = '{"name": "test"}'
        mock_db.first.return_value = config_row

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("my_key"))
            assert result == {"my_key": {"name": "test"}}

    def test_get_single_key_found_plain_string(self, mock_db):
        config_row = MagicMock()
        config_row.value = "plain_value"
        mock_db.first.return_value = config_row

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("key1"))
            assert result == {"key1": "plain_value"}

    def test_get_single_key_found_none_value(self, mock_db):
        config_row = MagicMock()
        config_row.value = None
        mock_db.first.return_value = config_row

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("empty_key"))
            assert result == {"empty_key": None}

    def test_get_single_key_not_found(self, mock_db):
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("missing"))
            assert result == {}

    def test_get_all_keys(self, mock_db):
        row1 = MagicMock()
        row1.key = "key1"
        row1.value = '{"a": 1}'
        row2 = MagicMock()
        row2.key = "key2"
        row2.value = "plain"
        row3 = MagicMock()
        row3.key = "key3"
        row3.value = None
        mock_db.all.return_value = [row1, row2, row3]

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config())
            assert result == {"key1": {"a": 1}, "key2": "plain", "key3": None}

    def test_get_all_empty(self, mock_db):
        mock_db.all.return_value = []

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config())
            assert result == {}

    def test_json_decode_error_returns_raw_string(self, mock_db):
        config_row = MagicMock()
        config_row.value = "{invalid json"
        mock_db.first.return_value = config_row

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            result = asyncio.run(get_system_config("bad_json"))
            assert result == {"bad_json": "{invalid json"}

    def test_db_close_called(self, mock_db):
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import get_system_config
            asyncio.run(get_system_config("any"))
            mock_db.close.assert_called_once()


class TestSetSystemConfig:
    def test_create_new_config(self, mock_db):
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("new_key", {"data": 1}))
            assert result is True
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_update_existing_config(self, mock_db):
        existing_row = MagicMock()
        mock_db.first.return_value = existing_row

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("existing", "updated_value"))
            assert result is True
            assert existing_row.value == "updated_value"
            mock_db.commit.assert_called_once()

    def test_set_string_value_no_json_double_encoding(self, mock_db):
        existing_row = MagicMock()
        mock_db.first.return_value = existing_row

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("str_key", "just a string"))
            assert result is True
            assert existing_row.value == "just a string"

    def test_set_dict_value_serializes_to_json(self, mock_db):
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("json_key", {"nested": [1, 2]}))
            assert result is True
            args, kwargs = mock_db.add.call_args
            added_obj = args[0]
            assert isinstance(added_obj.value, str)
            assert json.loads(added_obj.value) == {"nested": [1, 2]}

    def test_failure_returns_false(self, mock_db):
        mock_db.commit.side_effect = Exception("DB error")

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            result = asyncio.run(set_system_config("fail_key", "value"))
            assert result is False
            mock_db.rollback.assert_called_once()

    def test_db_close_called(self, mock_db):
        mock_db.first.return_value = None

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import set_system_config
            asyncio.run(set_system_config("key", "value"))
            mock_db.close.assert_called_once()


class TestIsSystemInitialized:
    def test_initialized_when_rows_exist(self, mock_db):
        mock_db.count.return_value = 5

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import is_system_initialized
            result = asyncio.run(is_system_initialized())
            assert result is True

    def test_not_initialized_when_no_rows(self, mock_db):
        mock_db.count.return_value = 0

        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import is_system_initialized
            result = asyncio.run(is_system_initialized())
            assert result is False

    def test_db_close_called(self, mock_db):
        with patch("app.api.v1.system_config.SessionLocal", return_value=mock_db):
            from app.api.v1.system_config import is_system_initialized
            asyncio.run(is_system_initialized())
            mock_db.close.assert_called_once()
