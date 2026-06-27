"""Tests for LogExportService — 100% code coverage."""

import os
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.log_export_service import LogExportService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service(tmp_path):
    s = LogExportService()
    s.base_dir = tmp_path
    s.logs_dir = tmp_path / "logs"
    s.logs_dir.mkdir(parents=True, exist_ok=True)
    s.export_dir = tmp_path / "exports" / "error_reports"
    s.export_dir.mkdir(parents=True, exist_ok=True)
    return s


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestInit:
    def test_init_creates_dirs(self):
        s = LogExportService()
        assert s.export_dir.exists()


# ---------------------------------------------------------------------------
# _apply_sanitization
# ---------------------------------------------------------------------------


class TestApplySanitization:
    def test_password_redacted(self, service):
        result = service._apply_sanitization('password="secret123"')
        assert "***REDACTED***" in result
        assert "secret123" not in result

    def test_token_redacted(self, service):
        result = service._apply_sanitization('token="my.jwt.token"')
        assert "***TOKEN***" in result

    def test_secret_key_redacted(self, service):
        result = service._apply_sanitization('secret_key="supersecret"')
        assert "***SECRET***" in result

    def test_authorization_redacted(self, service):
        result = service._apply_sanitization("Authorization: Bearer abcdef123")
        assert "***BEARER_TOKEN***" in result

    def test_no_sensitive_data(self, service):
        result = service._apply_sanitization("This is normal log content")
        assert result == "This is normal log content"

    def test_hashed_password(self, service):
        result = service._apply_sanitization('hashed_password="abc123"')
        assert "***REDACTED***" in result


# ---------------------------------------------------------------------------
# _collect_log_files
# ---------------------------------------------------------------------------


class TestCollectLogFiles:
    def test_no_log_dir(self, service):
        service.logs_dir = service.base_dir / "nonexistent"
        result = service._collect_log_files(24)
        assert result == []

    def test_collects_recent_files(self, service):
        recent = service.logs_dir / "recent.log"
        old = service.logs_dir / "old.log"
        recent.write_text("recent")
        old.write_text("old")
        import time
        old_mtime = time.time() - 48 * 3600
        os.utime(str(old), (old_mtime, old_mtime))
        result = service._collect_log_files(24)
        assert recent in result
        assert old not in result

    def test_stat_exception_skipped(self, service):
        import time
        current_ts = time.time()
        mock_logs_dir = MagicMock()
        mock_logs_dir.exists.return_value = True
        bad_file = MagicMock()
        bad_file.stat.side_effect = [
            MagicMock(st_mtime=current_ts),
            Exception("stat fail"),
            MagicMock(st_mtime=current_ts),
        ]
        mock_logs_dir.glob.return_value = [bad_file, bad_file]
        service.logs_dir = mock_logs_dir
        result = service._collect_log_files(24)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _sanitize_log_file
# ---------------------------------------------------------------------------


class TestSanitizeLogFile:
    def test_sanitize_success(self, service, tmp_path):
        log_file = service.logs_dir / "test.log"
        log_file.write_text('password="secret"', encoding="utf-8")
        result = service._sanitize_log_file(log_file, tmp_path)
        assert result is not None
        content = result.read_text(encoding="utf-8")
        assert "***REDACTED***" in content

    def test_sanitize_failure(self, service, tmp_path):
        log_file = service.logs_dir / "fail.log"
        log_file.write_text("content", encoding="utf-8")
        with patch.object(
            service, "_apply_sanitization", side_effect=Exception("fail")
        ):
            result = service._sanitize_log_file(log_file, tmp_path)
            assert result is None


# ---------------------------------------------------------------------------
# _generate_diagnostic_report
# ---------------------------------------------------------------------------


class TestGenerateDiagnosticReport:
    def test_success(self, service, tmp_path):
        result = service._generate_diagnostic_report(tmp_path)
        assert result.exists()
        content = result.read_text(encoding="utf-8")
        assert "系统诊断报告" in content
        assert "[系统信息]" in content

    def test_app_info_failure(self, service, tmp_path):
        class FailingSettings:
            def __getattr__(self, name):
                raise Exception("fail")

        with patch("app.core.config.settings", FailingSettings()):
            result = service._generate_diagnostic_report(tmp_path)
            content = result.read_text(encoding="utf-8")
            assert "无法获取应用信息" in content

    def test_psutil_not_installed(self, service, tmp_path):
        import builtins
        orig = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "psutil":
                raise ImportError("psutil not available")
            return orig(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = service._generate_diagnostic_report(tmp_path)
            content = result.read_text(encoding="utf-8")
            assert "psutil未安装" in content

    def test_db_check_failure(self, service, tmp_path):
        with patch(
            "app.core.database.SessionLocal",
            side_effect=Exception("db fail"),
        ):
            result = service._generate_diagnostic_report(tmp_path)
            content = result.read_text(encoding="utf-8")
            assert "数据库检查失败" in content

    def test_pkg_resources_failure(self, service, tmp_path):
        import builtins
        orig_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pkg_resources":
                raise ImportError("pkg_resources not available")
            return orig_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = service._generate_diagnostic_report(tmp_path)
            content = result.read_text(encoding="utf-8")
            assert "获取依赖包版本失败" in content

    def test_overall_report_exception(self, service, tmp_path):
        with patch("builtins.open", side_effect=Exception("open fail")):
            with pytest.raises(Exception):
                service._generate_diagnostic_report(tmp_path)

    def test_performance_exception(self, service, tmp_path):
        import builtins
        orig = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "psutil":
                m = MagicMock()
                m.cpu_percent.side_effect = Exception("cpu fail")
                return m
            return orig(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = service._generate_diagnostic_report(tmp_path)
            content = result.read_text(encoding="utf-8")
            assert "获取性能指标失败" in content

    def test_db_execute_failure(self, service, tmp_path):
        db_mock = MagicMock()
        db_mock.execute.side_effect = Exception("execute fail")
        with patch(
            "app.core.database.SessionLocal",
            return_value=db_mock,
        ):
            result = service._generate_diagnostic_report(tmp_path)
            content = result.read_text(encoding="utf-8")
            assert "数据库连接: 失败" in content


# ---------------------------------------------------------------------------
# _create_zip_archive
# ---------------------------------------------------------------------------


class TestCreateZipArchive:
    def test_create_zip_success(self, service, tmp_path):
        report_dir = tmp_path / "report_dir"
        report_dir.mkdir()
        diag = report_dir / "diagnostic_report.txt"
        diag.write_text("diagnostic")
        files = [report_dir / "log1.log", report_dir / "log2.log"]
        for f in files:
            f.write_text("log")
        result = service._create_zip_archive("test-report", report_dir, files)
        assert result.exists()
        with zipfile.ZipFile(result, "r") as zf:
            names = zf.namelist()
            assert "diagnostic_report.txt" in names

    def test_create_zip_missing_files(self, service, tmp_path):
        report_dir = tmp_path / "report_dir2"
        report_dir.mkdir()
        diag = report_dir / "diagnostic_report.txt"
        diag.write_text("diag")
        missing = report_dir / "missing.log"
        result = service._create_zip_archive(
            "test-missing", report_dir, [missing]
        )
        assert result.exists()

    def test_create_zip_missing_diagnostic(self, service, tmp_path):
        report_dir = tmp_path / "report_dir3"
        report_dir.mkdir()
        files = []
        result = service._create_zip_archive(
            "test-no-diag", report_dir, files
        )
        assert result.exists()

    def test_create_zip_exception(self, service, tmp_path):
        report_dir = tmp_path / "report_dir4"
        report_dir.mkdir()
        with patch.object(
            zipfile.ZipFile, "__init__", side_effect=Exception("zip fail")
        ):
            with pytest.raises(Exception):
                service._create_zip_archive("fail", report_dir, [])


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------


class TestGenerateReport:
    def test_generate_report_success(self, service):
        with patch.object(service, "_collect_log_files", return_value=[]):
            result = service.generate_report(time_range_hours=24)
            assert result["report_id"].startswith("ERR-")
            assert result["zip_size"] >= 0
            assert result["files_count"] >= 1

    def test_generate_report_with_custom_id(self, service):
        with patch.object(service, "_collect_log_files", return_value=[]):
            result = service.generate_report(
                report_id="CUSTOM-001", time_range_hours=48
            )
            assert result["report_id"] == "CUSTOM-001"

    def test_generate_report_with_logs(self, service):
        log_file = service.logs_dir / "app.log"
        log_file.write_text('password="secret"', encoding="utf-8")
        result = service.generate_report(time_range_hours=24)
        assert result["files_count"] >= 2
        assert result["zip_path"] is not None

    def test_generate_report_exception(self, service):
        with patch.object(
            service, "_collect_log_files", side_effect=Exception("fail")
        ):
            with pytest.raises(Exception):
                service.generate_report()


# ---------------------------------------------------------------------------
# _cleanup_temp_files
# ---------------------------------------------------------------------------


class TestCleanupTempFiles:
    def test_cleanup_success(self, service, tmp_path):
        report_dir = tmp_path / "to_clean"
        report_dir.mkdir()
        (report_dir / "file.txt").write_text("x")
        service._cleanup_temp_files(report_dir)
        assert not report_dir.exists()

    def test_cleanup_exception(self, service, tmp_path):
        report_dir = tmp_path / "to_clean"
        report_dir.mkdir()
        with patch("shutil.rmtree", side_effect=Exception("rm fail")):
            service._cleanup_temp_files(report_dir)


# ---------------------------------------------------------------------------
# list_reports — test via patching the service attribute
# ---------------------------------------------------------------------------


class TestListReports:
    def test_list_reports_ok(self, service):
        for i in range(3):
            z = service.export_dir / f"ERR-2024010{i}-000000.zip"
            z.write_text("zip")
        res = service.list_reports(limit=10)
        assert len(res) == 3

    def test_list_reports_empty(self, service):
        assert service.list_reports() == []

    def test_list_reports_exception(self, service):
        with patch.object(
            service, "export_dir", wraps=service.export_dir
        ) as ed:
            ed.glob.side_effect = Exception("boom")
            assert service.list_reports() == []


# ---------------------------------------------------------------------------
# get_report_path
# ---------------------------------------------------------------------------


class TestGetReportPath:
    def test_get_existing(self, service):
        z = service.export_dir / "TEST-001.zip"
        z.write_text("x")
        assert service.get_report_path("TEST-001") == z

    def test_get_nonexistent(self, service):
        assert service.get_report_path("NONEXIST") is None


# ---------------------------------------------------------------------------
# delete_report
# ---------------------------------------------------------------------------


class TestDeleteReport:
    def test_delete_existing(self, service):
        z = service.export_dir / "DEL-001.zip"
        z.write_text("x")
        assert service.delete_report("DEL-001") is True
        assert not z.exists()

    def test_delete_nonexistent(self, service):
        assert service.delete_report("DEL-NOPE") is False

    def test_delete_file_not_found(self, service):
        z = service.export_dir / "DEL-003.zip"
        z.write_text("x")
        with patch.object(Path, "unlink", side_effect=FileNotFoundError):
            assert service.delete_report("DEL-003") is True

    def test_delete_exception(self, service):
        z = service.export_dir / "DEL-004.zip"
        z.write_text("x")
        with patch.object(Path, "unlink", side_effect=Exception("boom")):
            assert service.delete_report("DEL-004") is False


# ---------------------------------------------------------------------------
# cleanup_old_reports
# ---------------------------------------------------------------------------


class TestCleanupOldReports:
    def _create_old_zip(self, service, name, days_ago=10):
        z = service.export_dir / name
        z.write_text("x")
        import time
        os.utime(str(z), (time.time() - days_ago * 86400, time.time() - days_ago * 86400))
        return z

    def test_cleanup_some(self, service):
        self._create_old_zip(service, "ERR-OLD-001.zip", days_ago=10)
        new = service.export_dir / "ERR-NEW-001.zip"
        new.write_text("new")
        service.cleanup_old_reports(retention_days=7)
        assert not (service.export_dir / "ERR-OLD-001.zip").exists()
        assert new.exists()

    def test_cleanup_none(self, service):
        z = service.export_dir / "ERR-CURRENT.zip"
        z.write_text("x")
        service.cleanup_old_reports(retention_days=30)
        assert z.exists()

    def test_cleanup_file_not_found(self, service):
        z = self._create_old_zip(service, "ERR-CLEAN.zip", days_ago=10)
        with patch.object(Path, "unlink", side_effect=FileNotFoundError):
            service.cleanup_old_reports(retention_days=1)

    def test_cleanup_exception(self, service):
        with patch.object(
            service, "export_dir", wraps=service.export_dir
        ) as ed:
            ed.glob.side_effect = Exception("boom")
            service.cleanup_old_reports()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------


def test_global_instance():
    from app.services.log_export_service import log_export_service
    assert isinstance(log_export_service, LogExportService)
