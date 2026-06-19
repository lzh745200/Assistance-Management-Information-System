"""Tests for app.services.village.data_permission - zero coverage → 100%"""

import pytest
from unittest.mock import MagicMock, patch
from app.services.village.data_permission import filter_villages_by_permission


class TestFilterVillagesByPermission:
    def test_delegates_to_filter_by_data_scope(self):
        query = MagicMock(name="query")
        user = MagicMock(name="user")
        model = MagicMock(name="model")
        db = MagicMock(name="db")

        with patch(
            "app.services.village.data_permission.filter_by_data_scope",
            return_value="filtered_query",
        ) as mock_filter:
            result = filter_villages_by_permission(query, user, model, db=db)
            mock_filter.assert_called_once_with(query, model, user, db=db)
            assert result == "filtered_query"

    def test_default_db_none(self):
        query = MagicMock(name="query")
        user = MagicMock(name="user")
        model = MagicMock(name="model")

        with patch(
            "app.services.village.data_permission.filter_by_data_scope",
            return_value="result_default",
        ) as mock_filter:
            result = filter_villages_by_permission(query, user, model)
            mock_filter.assert_called_once_with(query, model, user, db=None)
            assert result == "result_default"

    def test_returns_same_type(self):
        query = MagicMock(name="query")
        user = MagicMock(name="user")
        model = MagicMock(name="model")
        expected = MagicMock(name="expected_query")

        with patch(
            "app.services.village.data_permission.filter_by_data_scope",
            return_value=expected,
        ):
            result = filter_villages_by_permission(query, user, model)
            assert result is expected
