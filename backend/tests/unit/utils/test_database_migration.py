"""
数据库迁移脚本测试

测试 app/utils/database_migration.py 模块
"""
import pytest
from unittest.mock import MagicMock, patch
from app.utils.database_migration import migrate_database, check_migration_status


class TestMigrateDatabase:
    def test_all_need_migration(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 0
        result = migrate_database(mock_db)
        assert result["success"] == 7
        assert result["skipped"] == 0
        assert result["failed"] == 0
        assert result["total"] == 7

    def test_all_skipped(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 1
        result = migrate_database(mock_db)
        assert result["success"] == 0
        assert result["skipped"] == 7
        assert result["failed"] == 0
        assert result["total"] == 7

    def test_mixed_migration(self):
        mock_db = MagicMock()
        call_count = [0]

        def mock_scalar():
            call_count[0] += 1
            return 0 if call_count[0] <= 3 else 1

        mock_db.execute.return_value.scalar.side_effect = mock_scalar
        result = migrate_database(mock_db)
        assert result["success"] == 3
        assert result["skipped"] == 4
        assert result["failed"] == 0
        assert result["total"] == 7

    def test_error_handling(self):
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB error")
        result = migrate_database(mock_db)
        assert result["success"] == 0
        assert result["failed"] == 7
        assert result["total"] == 7
        mock_db.rollback.assert_called()


class TestCheckMigrationStatus:
    def test_all_complete(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 1
        status = check_migration_status(mock_db)
        assert all(v is True for v in status.values())

    def test_none_complete(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 0
        status = check_migration_status(mock_db)
        assert all(v is False for v in status.values())

    def test_error_handling(self):
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Check failed")
        status = check_migration_status(mock_db)
        assert all(v is False for v in status.values())
