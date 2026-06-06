"""
数据同步服务单元测试
覆盖: app/services/data_sync_service.py — 纯函数和核心逻辑
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


class TestExportConfig:
    def test_create_default(self):
        from app.services.data_sync_service import ExportConfig
        cfg = ExportConfig()
        assert cfg.since is None
        assert cfg.modules is None
        assert cfg.include_files is False
        assert cfg.user_id is None
        assert cfg.user_name is None

    def test_create_with_values(self):
        from app.services.data_sync_service import ExportConfig
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        cfg = ExportConfig(
            since=dt,
            modules=["schools", "projects"],
            include_files=True,
            user_id=1,
            user_name="admin",
        )
        assert cfg.since == dt
        assert cfg.modules == ["schools", "projects"]
        assert cfg.include_files is True
        assert cfg.user_id == 1
        assert cfg.user_name == "admin"


class TestSanitizeColumnName:
    def test_valid_name_unchanged(self):
        from app.services.data_sync_service import DataSyncService
        assert DataSyncService._sanitize_column_name("user_name") == "user_name"

    def test_alphanumeric_and_underscore(self):
        from app.services.data_sync_service import DataSyncService
        assert DataSyncService._sanitize_column_name("col_123") == "col_123"

    def test_invalid_chars_raises(self):
        from app.services.data_sync_service import DataSyncService
        # col-name has '-' which is not [A-Za-z0-9_]
        with pytest.raises(ValueError):
            DataSyncService._sanitize_column_name("col-name;DROP")

    def test_empty_raises(self):
        from app.services.data_sync_service import DataSyncService
        # Empty string fails regex (must start with letter/_)
        with pytest.raises(ValueError):
            DataSyncService._sanitize_column_name("")

    def test_starting_with_number_raises(self):
        from app.services.data_sync_service import DataSyncService
        with pytest.raises(ValueError):
            DataSyncService._sanitize_column_name("123col")


class TestValidateTableName:
    def test_valid_table_name(self):
        from app.services.data_sync_service import DataSyncService
        # Uses a table from the allowed list
        result = DataSyncService._validate_table_name("schools")
        assert result == "schools"

    def test_valid_table_projects(self):
        from app.services.data_sync_service import DataSyncService
        result = DataSyncService._validate_table_name("projects")
        assert result == "projects"

    def test_non_allowed_table_raises(self):
        from app.services.data_sync_service import DataSyncService
        with pytest.raises(ValueError):
            DataSyncService._validate_table_name("DROP TABLE users")

    def test_sql_injection_blocked(self):
        from app.services.data_sync_service import DataSyncService
        with pytest.raises(ValueError):
            DataSyncService._validate_table_name("users; DROP TABLE schools;")

    def test_invalid_chars_raises(self):
        from app.services.data_sync_service import DataSyncService
        with pytest.raises(ValueError):
            DataSyncService._validate_table_name("malicious';--")

    def test_empty_string_raises(self):
        from app.services.data_sync_service import DataSyncService
        with pytest.raises(ValueError):
            DataSyncService._validate_table_name("")


class TestShouldUpdateRecord:
    @pytest.fixture
    def svc(self):
        from app.services.data_sync_service import DataSyncService
        return DataSyncService()

    def test_default_returns_false(self, svc):
        """No updated_at fields → default False."""
        assert svc._should_update_record({}, {}) is False

    def test_only_existing_has_updated_at(self, svc):
        """Only existing has updated_at→ first if fails → default False."""
        assert svc._should_update_record(
            {"updated_at": "2026-01-01"}, {}
        ) is False

    def test_only_imported_has_updated_at(self, svc):
        """Only imported has updated_at → first if fails → default False."""
        assert svc._should_update_record(
            {}, {"updated_at": "2026-06-01"}
        ) is False

    def test_returns_false_on_parse_error(self, svc):
        """When timestamp parsing fails → exception caught → default False."""
        assert svc._should_update_record(
            {"updated_at": "not-a-date"}, {"updated_at": "also-bad"}
        ) is False


class TestAllowedTables:
    def test_allowed_tables_contains_key_modules(self):
        from app.services.data_sync_service import _ALLOWED_TABLES
        assert "schools" in _ALLOWED_TABLES
        assert "projects" in _ALLOWED_TABLES
        assert "funds" in _ALLOWED_TABLES
        assert "users" in _ALLOWED_TABLES
        assert "supported_villages" in _ALLOWED_TABLES

    def test_allowed_tables_is_frozenset(self):
        from app.services.data_sync_service import _ALLOWED_TABLES
        assert isinstance(_ALLOWED_TABLES, frozenset)


class TestDataSyncServiceInit:
    def test_init_creates_service(self):
        from app.services.data_sync_service import DataSyncService
        svc = DataSyncService()
        assert svc is not None


class TestTableNamePattern:
    def test_pattern_valid(self):
        import re
        pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
        assert pattern.match("users") is not None
        assert pattern.match("supported_villages") is not None
        assert pattern.match("col_123") is not None

    def test_pattern_invalid(self):
        import re
        pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
        assert pattern.match("123col") is None
        assert pattern.match("col-name") is None
        assert pattern.match("col name") is None
        assert pattern.match("col;drop") is None
