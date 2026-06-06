"""
版本管理服务单元测试
覆盖: app/services/version_service.py
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
import json


@pytest.fixture
def version_service():
    """Create VersionService with mocked file I/O."""
    with patch("pathlib.Path.exists", return_value=False), \
         patch("pathlib.Path.mkdir"), \
         patch("builtins.open", mock_open(read_data="{}")), \
         patch("app.services.version_service.settings"):
        from app.services.version_service import VersionService
        svc = VersionService()
        # Override file paths to use mock
        svc._load_current_version = MagicMock(return_value={
            "version": "1.2.0",
            "build": "20260606",
            "release_date": "2026-06-06",
            "description": "Test version",
        })
        svc._load_history = MagicMock(return_value=[])
        svc._save_version = MagicMock()
        svc._save_history = MagicMock()
        svc.current_version = {
            "version": "1.2.0",
            "build": "20260606",
            "release_date": "2026-06-06",
            "description": "Test version",
        }
        return svc


class TestCompareVersions:
    @pytest.fixture
    def svc(self, version_service):
        return version_service

    def test_equal_versions(self, svc):
        assert svc.compare_versions("1.0.0", "1.0.0") == 0

    def test_greater_major(self, svc):
        assert svc.compare_versions("2.0.0", "1.0.0") == 1

    def test_lesser_major(self, svc):
        assert svc.compare_versions("1.0.0", "2.0.0") == -1

    def test_greater_minor(self, svc):
        assert svc.compare_versions("1.2.0", "1.1.0") == 1

    def test_lesser_minor(self, svc):
        assert svc.compare_versions("1.1.0", "1.2.0") == -1

    def test_greater_patch(self, svc):
        assert svc.compare_versions("1.0.5", "1.0.3") == 1

    def test_unequal_length(self, svc):
        assert svc.compare_versions("2.0", "1.0.0") == 1
        assert svc.compare_versions("1.0", "1.0.0") == 0

    def test_large_version_numbers(self, svc):
        assert svc.compare_versions("10.20.30", "10.20.30") == 0

    def test_invalid_returns_zero(self, svc):
        # Invalid version strings should return 0 (graceful degradation)
        assert svc.compare_versions("abc", "1.0") == 0


class TestGetCurrentVersion:
    def test_returns_copy(self, version_service):
        result = version_service.get_current_version()
        assert result["version"] == "1.2.0"
        assert result is not version_service.current_version  # should be a copy

    def test_has_required_keys(self, version_service):
        result = version_service.get_current_version()
        assert "version" in result
        assert "build" in result


class TestGetVersionHistory:
    def test_returns_reversed(self, version_service):
        version_service._load_history.return_value = [
            {"action": "upgrade", "new_version": "1.0.0"},
            {"action": "upgrade", "new_version": "1.1.0"},
            {"action": "upgrade", "new_version": "1.2.0"},
        ]
        result = version_service.get_version_history(limit=2)
        assert len(result) == 2
        assert result[0]["new_version"] == "1.2.0"  # newest first

    def test_empty_history(self, version_service):
        version_service._load_history.return_value = []
        result = version_service.get_version_history()
        assert result == []


class TestCheckVersionChange:
    def test_no_change(self, version_service):
        with patch.object(version_service, "current_version",
                          {"version": "1.2.0"}):
            with patch("app.services.version_service.settings") as mock_settings:
                mock_settings.PROJECT_VERSION = "1.2.0"
                result = version_service.check_version_change()
                assert result["changed"] is False

    def test_version_changed(self, version_service):
        with patch.object(version_service, "current_version",
                          {"version": "1.1.0"}):
            with patch("app.services.version_service.settings") as mock_settings:
                mock_settings.PROJECT_VERSION = "1.2.0"
                result = version_service.check_version_change()
                assert result["changed"] is True
                assert result["old_version"] == "1.1.0"
                assert result["new_version"] == "1.2.0"

    def test_check_version_changed_detected(self, version_service):
        """When versions differ, return change info."""
        version_service.current_version = {"version": "1.0.0"}
        with patch("app.services.version_service.settings") as mock_settings:
            mock_settings.PROJECT_VERSION = "1.2.0"
            result = version_service.check_version_change()
            assert result["changed"] is True
            assert result["old_version"] == "1.0.0"
            assert result["new_version"] == "1.2.0"


class TestUpgrade:
    def test_upgrade_success(self, version_service):
        version_service._run_migrations = MagicMock(
            return_value={"status": "success"}
        )
        version_service._update_config = MagicMock(
            return_value={"status": "success"}
        )

        with patch("app.services.version_service.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "2026-06-06"
            mock_dt.now.return_value.isoformat.return_value = "2026-06-06T00:00:00"

            result = version_service.upgrade(
                "1.3.0",
                description="Major upgrade",
                backup_before_upgrade=False,
            )

        assert result["status"] == "success"
        assert result["old_version"] == "1.2.0"
        assert result["new_version"] == "1.3.0"

    def test_upgrade_with_backup(self, version_service):
        version_service._run_migrations = MagicMock(
            return_value={"status": "success"}
        )
        version_service._update_config = MagicMock(
            return_value={"status": "success"}
        )

        with patch("app.services.backup_service.BackupService") as mock_backup_svc:
            mock_backup_svc.return_value.create_backup.return_value = MagicMock(
                file_path="/backups/test.db"
            )

            with patch("app.services.version_service.datetime") as mock_dt:
                mock_dt.now.return_value.strftime.return_value = "2026-06-06"
                mock_dt.now.return_value.isoformat.return_value = "2026-06-06T00:00:00"

                result = version_service.upgrade("1.3.0", backup_before_upgrade=True)

        assert result["status"] == "success"

    def test_upgrade_exception_returns_error(self, version_service):
        version_service._run_migrations = MagicMock(
            side_effect=Exception("DB error")
        )

        result = version_service.upgrade("1.3.0", backup_before_upgrade=False)
        assert result["status"] == "error"
        assert "DB error" in result["message"]


class TestRollback:
    def test_rollback_no_history(self, version_service):
        result = version_service.rollback()
        assert result["status"] == "error"
        assert "没有可回滚的版本" in result["message"]

    def test_rollback_target_not_found(self, version_service):
        version_service._load_history.return_value = [
            {"action": "upgrade", "old_version": "1.1.0", "new_version": "1.2.0"}
        ]
        result = version_service.rollback("9.9.9")
        assert result["status"] == "error"
        assert "未找到版本" in result["message"]

    def test_rollback_no_backup_file(self, version_service):
        version_service._load_history.return_value = [
            {"action": "upgrade", "old_version": "1.1.0", "new_version": "1.2.0",
             "backup_path": None}
        ]
        result = version_service.rollback("1.2.0")
        assert result["status"] == "error"


class TestMigrateMissingColumns:
    def test_migration_success(self, version_service):
        with patch("app.core.migration_helper.migrate_missing_columns") as mock_migrate:
            mock_migrate.return_value = None
            result = version_service._run_migrations("1.0", "1.2")
            assert result["status"] == "success"

    def test_migration_error(self, version_service):
        with patch("app.core.migration_helper.migrate_missing_columns",
                   side_effect=Exception("Migration failed")):
            result = version_service._run_migrations("1.0", "1.2")
            assert result["status"] == "error"


class TestUpdateConfig:
    def test_config_update_success(self, version_service):
        result = version_service._update_config("1.0", "1.1")
        assert result["status"] == "success"


class TestGlobalInstance:
    def test_version_service_instance_exists(self):
        from app.services.version_service import version_service
        assert version_service is not None
        assert hasattr(version_service, "get_current_version")
        assert hasattr(version_service, "compare_versions")
