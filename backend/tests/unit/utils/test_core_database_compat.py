"""
数据库兼容层测试

测试 app/core/database_compat.py 模块
"""
import pytest
from unittest.mock import MagicMock, patch
from app.core.database_compat import (
    is_sqlite,
    is_postgresql,
    is_mysql,
    get_db_type,
    paginate_query,
    like_escape,
    sqlite_regexp,
)


class TestDatabaseDetection:
    def test_is_sqlite(self):
        assert is_sqlite("sqlite:///./data.db") is True
        assert is_sqlite("sqlite://") is True
        assert is_sqlite("postgresql://localhost/db") is False
        assert is_sqlite("") is False

    def test_is_postgresql(self):
        assert is_postgresql("postgresql://localhost/db") is True
        assert is_postgresql("postgres://localhost/db") is True
        assert is_postgresql("sqlite:///./data.db") is False
        assert is_postgresql("mysql://localhost/db") is False

    def test_is_mysql(self):
        assert is_mysql("mysql://localhost/db") is True
        assert is_mysql("mariadb://localhost/db") is True
        assert is_mysql("sqlite:///./data.db") is False
        assert is_mysql("postgresql://localhost/db") is False

    def test_get_db_type(self):
        assert get_db_type("sqlite:///./data.db") == "sqlite"
        assert get_db_type("postgresql://localhost/db") == "postgresql"
        assert get_db_type("mysql://localhost/db") == "mysql"
        assert get_db_type("mariadb://localhost/db") == "mysql"
        assert get_db_type("oracle://localhost/db") == "unknown"


class TestPaginateQuery:
    def test_paginate_basic(self):
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.offset.return_value.limit.return_value.all.return_value = [
            {"id": i} for i in range(1, 21)
        ]
        result = paginate_query(mock_query, page=1, page_size=20)
        assert result["total"] == 100
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["pages"] == 5

    def test_paginate_with_url(self):
        mock_query = MagicMock()
        mock_query.count.return_value = 50
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        result = paginate_query(mock_query, page=1, page_size=20, base_url="/api/items")
        assert result["next"] is not None
        assert result["previous"] is None

    def test_paginate_middle_page(self):
        mock_query = MagicMock()
        mock_query.count.return_value = 50
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        result = paginate_query(mock_query, page=2, page_size=20, base_url="/api/items")
        assert result["next"] is not None
        assert result["previous"] is not None

    def test_paginate_last_page(self):
        mock_query = MagicMock()
        mock_query.count.return_value = 50
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        result = paginate_query(mock_query, page=3, page_size=20, base_url="/api/items")
        assert result["next"] is None
        assert result["previous"] is not None

    def test_paginate_empty(self):
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        result = paginate_query(mock_query, page=1, page_size=20)
        assert result["total"] == 0
        assert result["pages"] == 1
        assert result["items"] == []


class TestLikeEscape:
    def test_escape_percent(self):
        assert like_escape("100%") == r"100\%"

    def test_escape_underscore(self):
        assert like_escape("test_value") == r"test\_value"

    def test_escape_backslash(self):
        assert like_escape("a\\b") == r"a\\b"

    def test_escape_combined(self):
        assert like_escape("100%_test") == r"100\%\_test"

    def test_escape_no_special(self):
        assert like_escape("hello world") == "hello world"

    def test_escape_empty(self):
        assert like_escape("") == ""


class TestSqliteRegexp:
    def test_regexp_match(self):
        assert sqlite_regexp(r"^\d{3}", "123abc") is True

    def test_regexp_no_match(self):
        assert sqlite_regexp(r"^\d{3}", "abc123") is False

    def test_regexp_invalid(self):
        assert sqlite_regexp(r"[invalid", "test") is False

    def test_regexp_empty_string(self):
        assert sqlite_regexp(r".*", "") is True
