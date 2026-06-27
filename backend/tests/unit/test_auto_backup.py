"""TDD: 自动备份调度 — 100% 行覆盖（测试需启用自动备份）."""
import os
os.environ["BACKUP_ENABLED"] = "true"  # Enable for backup tests (uses tmp_path)
import time
from unittest.mock import patch


class TestBackupScheduler:
    """BackupScheduler 全覆盖测试."""

    # ── __init__ ──

    def test_init_default(self):
        from app.services.auto_backup import BackupScheduler
        s = BackupScheduler()
        assert s.interval == 1440
        assert s.backup_dir == "./backups"
        assert s.source_db_path == "./data/rural_revitalization.db"
        assert s._last_backup == 0.0

    def test_init_custom(self):
        from app.services.auto_backup import BackupScheduler
        s = BackupScheduler(interval_minutes=60, backup_dir="/tmp/custom",
                            source_db_path="/tmp/custom.db")
        assert s.interval == 60
        assert s.backup_dir == "/tmp/custom"
        assert s.source_db_path == "/tmp/custom.db"

    def test_init_creates_backup_dir(self, tmp_path):
        from app.services.auto_backup import BackupScheduler
        d = tmp_path / "new_backup_dir"
        assert not os.path.exists(d)
        BackupScheduler(backup_dir=str(d))
        assert os.path.exists(d)

    # ── should_backup ──

    def test_should_backup_first_run(self):
        from app.services.auto_backup import BackupScheduler
        s = BackupScheduler(interval_minutes=60)
        assert s.should_backup() is True

    @patch("app.services.auto_backup.time.time")
    def test_should_backup_elapsed_less_than_interval(self, mock_time):
        from app.services.auto_backup import BackupScheduler
        s = BackupScheduler(interval_minutes=60)
        s._last_backup = 1000.0
        mock_time.return_value = 1000.0
        assert s.should_backup() is False

    @patch("app.services.auto_backup.time.time")
    def test_should_backup_elapsed_equals_interval(self, mock_time):
        from app.services.auto_backup import BackupScheduler
        s = BackupScheduler(interval_minutes=60)
        s._last_backup = 1000.0
        mock_time.return_value = 1000.0 + 60 * 60
        assert s.should_backup() is True

    @patch("app.services.auto_backup.time.time")
    def test_should_backup_elapsed_exceeds_interval(self, mock_time):
        from app.services.auto_backup import BackupScheduler
        s = BackupScheduler(interval_minutes=60)
        s._last_backup = 1000.0
        mock_time.return_value = 1000.0 + 7200.0
        assert s.should_backup() is True

    # ── run_backup ──

    def test_run_backup_source_not_found(self):
        from app.services.auto_backup import BackupScheduler
        s = BackupScheduler(source_db_path="/nonexistent/path/db.db")
        result = s.run_backup()
        assert result is None
        assert s._last_backup == 0.0

    def test_run_backup_success(self, tmp_path):
        from app.services.auto_backup import BackupScheduler
        src = tmp_path / "source.db"
        src.write_bytes(b"test database content")
        backup_dir = tmp_path / "backups"
        s = BackupScheduler(backup_dir=str(backup_dir), source_db_path=str(src))
        result = s.run_backup()
        assert result is not None
        assert os.path.exists(result)
        assert result.endswith(".zip")
        assert s._last_backup > 0.0
        assert "backup_" in os.path.basename(result)

    @patch("zipfile.ZipFile")
    @patch("app.services.auto_backup.os.path.exists", return_value=True)
    def test_run_backup_copy_fails(self, mock_exists, mock_zipfile, tmp_path):
        from app.services.auto_backup import BackupScheduler
        mock_zipfile.side_effect = PermissionError("access denied")
        s = BackupScheduler(backup_dir=str(tmp_path))
        result = s.run_backup()
        assert result is None
        assert s._last_backup == 0.0

    # ── verify_last_backup ──

    def test_verify_last_backup_no_backups(self, tmp_path):
        from app.services.auto_backup import BackupScheduler
        s = BackupScheduler(backup_dir=str(tmp_path))
        assert s.verify_last_backup() is False

    def test_verify_last_backup_matching_hash(self, tmp_path):
        from app.services.auto_backup import BackupScheduler
        src = tmp_path / "source.db"
        src.write_bytes(b"same content")
        bk = tmp_path / "backup_20250101_120000.db"
        bk.write_bytes(b"same content")
        s = BackupScheduler(backup_dir=str(tmp_path), source_db_path=str(src))
        assert s.verify_last_backup() is True

    def test_verify_last_backup_mismatched_hash(self, tmp_path):
        from app.services.auto_backup import BackupScheduler
        src = tmp_path / "source.db"
        src.write_bytes(b"original content")
        bk = tmp_path / "backup_20250101_120000.db"
        bk.write_bytes(b"different content")
        s = BackupScheduler(backup_dir=str(tmp_path), source_db_path=str(src))
        assert s.verify_last_backup() is False

    def test_verify_last_backup_non_backup_files_ignored(self, tmp_path):
        from app.services.auto_backup import BackupScheduler
        src = tmp_path / "source.db"
        src.write_bytes(b"data")
        not_a_backup = tmp_path / "readme.txt"
        not_a_backup.write_text("ignore me")
        s = BackupScheduler(backup_dir=str(tmp_path), source_db_path=str(src))
        assert s.verify_last_backup() is False


class TestChecksum:
    """compute_file_checksum 全覆盖测试."""

    def test_checksum_normal_file(self, tmp_path):
        from app.services.auto_backup import compute_file_checksum
        f = tmp_path / "test.db"
        f.write_bytes(b"test backup data")
        checksum = compute_file_checksum(str(f))
        assert len(checksum) == 64
        assert compute_file_checksum(str(f)) == checksum

    def test_checksum_detect_change(self, tmp_path):
        from app.services.auto_backup import compute_file_checksum
        f = tmp_path / "test.db"
        f.write_bytes(b"original data")
        c1 = compute_file_checksum(str(f))
        f.write_bytes(b"tampered data")
        c2 = compute_file_checksum(str(f))
        assert c1 != c2

    def test_checksum_file_not_found(self):
        from app.services.auto_backup import compute_file_checksum
        assert compute_file_checksum("/nonexistent/file.db") == ""


class TestCleanup:
    """cleanup_old_backups 全覆盖测试."""

    def test_no_backup_files(self, tmp_path):
        from app.services.auto_backup import cleanup_old_backups
        assert cleanup_old_backups(str(tmp_path)) == 0

    def test_none_expired(self, tmp_path):
        from app.services.auto_backup import cleanup_old_backups
        for i in range(5):
            (tmp_path / f"backup_{i}.db").write_text("data")
        assert cleanup_old_backups(str(tmp_path), max_age_days=30) == 0

    def test_removes_expired_respecting_keep_min(self, tmp_path):
        from app.services.auto_backup import cleanup_old_backups
        for i in range(10):
            f = tmp_path / f"backup_{i}.db"
            f.write_text("data")
            old_time = time.time() - 60 * 86400
            os.utime(str(f), (old_time, old_time))
        result = cleanup_old_backups(str(tmp_path), max_age_days=30, keep_min=5)
        assert result == 5
        remaining = sorted(tmp_path.glob("backup_*"))
        assert len(remaining) == 5

    def test_old_files_under_keep_min_preserved(self, tmp_path):
        from app.services.auto_backup import cleanup_old_backups
        for i in range(3):
            f = tmp_path / f"backup_{i}.db"
            f.write_text("data")
            old_time = time.time() - 60 * 86400
            os.utime(str(f), (old_time, old_time))
        result = cleanup_old_backups(str(tmp_path), max_age_days=30, keep_min=5)
        assert result == 0
        assert len(list(tmp_path.glob("backup_*"))) == 3

    def test_some_expired_some_fresh(self, tmp_path):
        from app.services.auto_backup import cleanup_old_backups
        for i in range(3):
            f = tmp_path / f"backup_old_{i}.db"
            f.write_text("old")
            old_time = time.time() - 60 * 86400
            os.utime(str(f), (old_time, old_time))
        for i in range(3):
            f = tmp_path / f"backup_new_{i}.db"
            f.write_text("new")
        result = cleanup_old_backups(str(tmp_path), max_age_days=30, keep_min=1)
        assert result == 3
