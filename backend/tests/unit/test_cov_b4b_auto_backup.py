"""补齐 app.services.auto_backup 覆盖率缺口（37/41/49-50/77/107 行：BACKUP_ENABLED=False 分支）."""
from unittest.mock import patch

import app.services.auto_backup as ab


class TestBackupDisabledBranches:
    def test_init_logs_disabled(self):
        with patch.object(ab, "BACKUP_ENABLED", False):
            scheduler = ab.BackupScheduler()
        assert scheduler.interval == ab.DEFAULT_INTERVAL_MINUTES

    def test_should_backup_disabled_returns_false(self):
        with patch.object(ab, "BACKUP_ENABLED", False):
            assert ab.BackupScheduler().should_backup() is False

    def test_run_backup_disabled_returns_none(self):
        with patch.object(ab, "BACKUP_ENABLED", False):
            assert ab.BackupScheduler().run_backup() is None

    def test_verify_last_backup_disabled_returns_true(self):
        with patch.object(ab, "BACKUP_ENABLED", False):
            assert ab.BackupScheduler().verify_last_backup() is True

    def test_cleanup_old_backups_disabled_returns_zero(self):
        with patch.object(ab, "BACKUP_ENABLED", False):
            assert ab.cleanup_old_backups("./backups") == 0
