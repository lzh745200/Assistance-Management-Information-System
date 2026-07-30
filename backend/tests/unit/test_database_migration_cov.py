"""Coverage tests for app.utils.database_migration module."""

import pytest
from unittest.mock import MagicMock, patch


class TestMigrateDatabase:
    """Tests for migrate_database function."""

    def test_migrate_database_all_success(self):
        """All migrations execute successfully."""
        from app.utils.database_migration import migrate_database

        mock_db = MagicMock()
        # check queries return 0 (migration needed)
        mock_db.execute.return_value.scalar.return_value = 0

        with patch("app.utils.database_migration.safe_commit") as mock_commit:
            mock_commit.return_value = True
            result = migrate_database(mock_db)

        assert result["success"] == 7
        assert result["skipped"] == 0
        assert result["failed"] == 0
        assert result["total"] == 7

    def test_migrate_database_all_skipped(self):
        """All migrations already applied."""
        from app.utils.database_migration import migrate_database

        mock_db = MagicMock()
        # check queries return 1 (already exists)
        mock_db.execute.return_value.scalar.return_value = 1

        result = migrate_database(mock_db)

        assert result["success"] == 0
        assert result["skipped"] == 7
        assert result["failed"] == 0

    def test_migrate_database_with_errors(self):
        """Some migrations fail."""
        from app.utils.database_migration import migrate_database

        mock_db = MagicMock()
        # First call succeeds, second fails
        mock_db.execute.return_value.scalar.side_effect = [0, RuntimeError("error"), 1, 0, 1, 1, 1]

        result = migrate_database(mock_db)

        assert result["success"] == 1
        assert result["skipped"] == 5
        assert result["failed"] == 1

    def test_migrate_database_execute_error(self):
        """Migration SQL execution fails."""
        from app.utils.database_migration import migrate_database

        mock_db = MagicMock()
        # check returns 0 (needs migration), but execute fails
        mock_db.execute.return_value.scalar.return_value = 0
        mock_db.execute.side_effect = [MagicMock(scalar=MagicMock(return_value=0)), RuntimeError("exec error")]

        result = migrate_database(mock_db)
        assert result["failed"] >= 1


class TestCheckMigrationStatus:
    """Tests for check_migration_status function."""

    def test_check_migration_status_all_true(self):
        """All migrations present."""
        from app.utils.database_migration import check_migration_status

        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 1

        status = check_migration_status(mock_db)
        assert status["user_data_scope"] is True
        assert status["system_configs_table"] is True
        assert status["package_versions_table"] is True
        assert status["package_edit_logs_table"] is True

    def test_check_migration_status_all_false(self):
        """No migrations present."""
        from app.utils.database_migration import check_migration_status

        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 0

        status = check_migration_status(mock_db)
        assert status["user_data_scope"] is False
        assert status["system_configs_table"] is False
        assert status["package_versions_table"] is False
        assert status["package_edit_logs_table"] is False

    def test_check_migration_status_error(self):
        """Check handles errors gracefully."""
        from app.utils.database_migration import check_migration_status

        mock_db = MagicMock()
        mock_db.execute.side_effect = RuntimeError("db error")

        status = check_migration_status(mock_db)
        # Should return default status with all False
        assert status["user_data_scope"] is False
