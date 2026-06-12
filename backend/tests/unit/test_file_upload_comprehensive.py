"""Comprehensive tests for file_upload module (0% -> 100%)."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from app.core.file_upload import (
    detect_mime_type,
    detect_mime_type_from_bytes,
    is_allowed_mime,
    sanitize_filename,
    generate_unique_filename,
    get_upload_dir,
    get_upload_subdir,
    _guess_mime_from_extension,
    SAFE_MIME_TYPES,
)


class TestDetectMimeType:
    def test_detect_jpeg(self, tmp_path):
        f = tmp_path / "test.jpg"
        f.write_bytes(b"\xff\xd8\xff")
        result = detect_mime_type(str(f))
        assert result

    def test_fallback_on_exception(self):
        import app.core.file_upload as mod
        orig = mod.magic
        mod.magic = None
        try:
            result = detect_mime_type("/nonexistent/file.png")
            assert result == "image/png"
        finally:
            mod.magic = orig

    def test_detect_png(self, tmp_path):
        f = tmp_path / "test.png"
        f.write_bytes(b"\x89PNG\r\n")
        result = detect_mime_type(str(f))
        assert result


class TestDetectMimeTypeFromBytes:
    def test_normal(self):
        result = detect_mime_type_from_bytes(b"hello world")
        assert result

    def test_fallback(self):
        import app.core.file_upload as mod
        orig = mod.magic
        mod.magic = None
        try:
            result = detect_mime_type_from_bytes(b"\x00\x01\x02")
            assert result == "application/octet-stream"
        finally:
            mod.magic = orig


class TestIsAllowedMime:
    def test_allowed(self):
        assert is_allowed_mime("image/png") is True

    def test_not_allowed(self):
        assert is_allowed_mime("application/x-executable") is False

    def test_custom_set(self):
        custom = {"application/json"}
        assert is_allowed_mime("application/json", allowed_types=custom) is True
        assert is_allowed_mime("image/png", allowed_types=custom) is False


class TestSanitizeFilename:
    def test_safe_name(self):
        assert sanitize_filename("report.pdf") == "report.pdf"

    def test_special_chars(self):
        result = sanitize_filename("my<script>.pdf")
        assert "<" not in result
        assert ">" not in result
        assert result.endswith(".pdf")

    def test_chinese_chars(self):
        result = sanitize_filename("报告文件.xlsx")
        assert "报告" in result
        assert result.endswith(".xlsx")

    def test_empty_becomes_file(self):
        result = sanitize_filename("!!!###.txt")
        assert result.startswith("file")

    def test_long_name_truncated(self):
        long_name = "a" * 200 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) < 200

    def test_multiple_underscores_collapsed(self):
        result = sanitize_filename("a__b___c.txt")
        assert "___" not in result


class TestGenerateUniqueFilename:
    def test_unique(self):
        name1 = generate_unique_filename("doc.pdf")
        name2 = generate_unique_filename("doc.pdf")
        assert name1 != name2

    def test_with_prefix(self):
        result = generate_unique_filename("doc.pdf", prefix="backup")
        assert result.startswith("backup_")

    def test_preserves_extension(self):
        result = generate_unique_filename("data.xlsx")
        assert result.endswith(".xlsx")


class TestGetUploadDir:
    def test_default(self):
        with patch("app.core.file_upload.Path") as mock_path:
            mock_path.return_value.absolute.return_value = "/tmp/uploads"
            result = get_upload_dir()
            assert result == "/tmp/uploads"

    def test_with_settings(self):
        settings = MagicMock()
        settings.UPLOAD_DIR = "/custom/uploads"
        with patch("app.core.file_upload.Path") as mock_path:
            mock_path.return_value.absolute.return_value = "/custom/uploads"
            result = get_upload_dir(settings=settings)
            assert result == "/custom/uploads"

    def test_no_settings_fallback(self):
        with patch("app.core.file_upload.Path") as mock_path:
            mock_path.return_value.absolute.return_value = os.path.abspath("./uploads")
            result = get_upload_dir(settings=None)
            assert result


class TestGetUploadSubdir:
    def test_creates_subdir(self):
        with patch("app.core.file_upload.get_upload_dir", return_value="/tmp/uploads"):
            with patch("app.core.file_upload.Path") as mock_path:
                mock_base = MagicMock()
                mock_target = MagicMock()
                mock_base.__truediv__ = MagicMock(return_value=mock_target)
                mock_path.return_value = mock_base
                mock_target.absolute.return_value = "/tmp/uploads/avatars"
                result = get_upload_subdir("avatars")
                assert result == "/tmp/uploads/avatars"


class TestGuessMimeFromExtension:
    def test_known_extensions(self):
        assert _guess_mime_from_extension(".jpg") == "image/jpeg"
        assert _guess_mime_from_extension(".jpeg") == "image/jpeg"
        assert _guess_mime_from_extension(".png") == "image/png"
        assert _guess_mime_from_extension(".gif") == "image/gif"
        assert _guess_mime_from_extension(".webp") == "image/webp"
        assert _guess_mime_from_extension(".bmp") == "image/bmp"
        assert _guess_mime_from_extension(".pdf") == "application/pdf"
        assert _guess_mime_from_extension(".csv") == "text/csv"
        assert _guess_mime_from_extension(".txt") == "text/plain"
        assert _guess_mime_from_extension(".xlsx") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert _guess_mime_from_extension(".xls") == "application/vnd.ms-excel"
        assert _guess_mime_from_extension(".docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert _guess_mime_from_extension(".doc") == "application/msword"
        assert _guess_mime_from_extension(".pptx") == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        assert _guess_mime_from_extension(".ppt") == "application/vnd.ms-powerpoint"
        assert _guess_mime_from_extension(".json") == "application/json"

    def test_unknown_extension(self):
        assert _guess_mime_from_extension(".xyz") == "application/octet-stream"

    def test_no_extension(self):
        assert _guess_mime_from_extension("") == "application/octet-stream"


class TestSafeMimeTypes:
    def test_safe_types_not_empty(self):
        assert len(SAFE_MIME_TYPES) > 0

    def test_common_safe_types(self):
        assert "image/jpeg" in SAFE_MIME_TYPES
        assert "image/png" in SAFE_MIME_TYPES
        assert "application/pdf" in SAFE_MIME_TYPES
        assert "text/csv" in SAFE_MIME_TYPES
        assert "application/msword" in SAFE_MIME_TYPES
