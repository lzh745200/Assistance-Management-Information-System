"""TDD: 自动备份调度."""
import pytest
import os
import tempfile


class TestBackupScheduler:
    def test_scheduler_creation(self):
        from app.services.auto_backup import BackupScheduler
        s = BackupScheduler(interval_minutes=60, backup_dir="/tmp")
        assert s.interval == 60
        assert s.backup_dir == "/tmp"

    def test_should_backup_first_run(self):
        from app.services.auto_backup import BackupScheduler
        import time
        s = BackupScheduler(interval_minutes=60, backup_dir="/tmp")
        # Never backed up — should backup
        assert s.should_backup() is True

    def test_should_not_backup_immediately_after_last(self):
        from app.services.auto_backup import BackupScheduler
        import time
        s = BackupScheduler(interval_minutes=60, backup_dir="/tmp")
        s._last_backup = time.time()
        assert s.should_backup() is False

    def test_retention_cleanup(self, tmp_path):
        from app.services.auto_backup import cleanup_old_backups
        import time
        old = tmp_path / "backup_2020.db"
        recent = tmp_path / "backup_2026.db"
        old.write_text("old")
        recent.write_text("recent")
        # Set mtime to 100 days ago
        old_time = time.time() - 86400 * 100
        os.utime(old, (old_time, old_time))
        removed = cleanup_old_backups(str(tmp_path), max_age_days=30, keep_min=1)
        assert removed >= 1 or not old.exists()


class TestBackupIntegrity:
    def test_checksum_computation(self):
        from app.services.auto_backup import compute_file_checksum
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        f.write(b"test backup data")
        f.close()
        try:
            checksum = compute_file_checksum(f.name)
            assert len(checksum) == 64  # SHA-256
            assert compute_file_checksum(f.name) == checksum  # Deterministic
        finally:
            os.unlink(f.name)

    def test_checksum_detect_change(self):
        from app.services.auto_backup import compute_file_checksum
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        f.write(b"original data")
        f.close()
        try:
            c1 = compute_file_checksum(f.name)
            with open(f.name, "ab") as fh:
                fh.write(b"tampered")
            c2 = compute_file_checksum(f.name)
            assert c1 != c2
        finally:
            os.unlink(f.name)
