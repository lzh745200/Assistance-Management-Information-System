"""Tests for app/utils/file_response.py — 100% coverage."""

import os
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch, call

import pytest
from fastapi.responses import FileResponse

from app.utils.file_response import bytesio_response, filepath_response, file_response


# ============================================================================
# bytesio_response
# ============================================================================

class TestBytesioResponse:
    def test_normal_flow(self):
        buf = BytesIO(b"hello world")
        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.xlsx"

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp) as mock_ntf:
            with patch("builtins.open", MagicMock()):
                result = bytesio_response(buf, filename="report.xlsx")

        assert isinstance(result, FileResponse)
        mock_ntf.assert_called_once_with(suffix=".xlsx", delete=False)
        mock_tmp.write.assert_called_once_with(b"hello world")
        mock_tmp.close.assert_called_once()
        assert result.filename == "report.xlsx"

    def test_no_extension(self):
        buf = BytesIO(b"data")
        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.tmp"

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp) as mock_ntf:
            result = bytesio_response(buf, filename="download")

        assert isinstance(result, FileResponse)
        mock_ntf.assert_called_once_with(suffix=".tmp", delete=False)

    def test_default_filename(self):
        buf = BytesIO(b"data")
        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile"

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp):
            result = bytesio_response(buf)

        assert isinstance(result, FileResponse)
        assert result.filename == "download"

    def test_exception_cleans_up_temp_file(self):
        buf = BytesIO(b"data")
        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.xlsx"
        mock_tmp.write.side_effect = OSError("write failed")

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp):
            with patch("os.unlink") as mock_unlink:
                with pytest.raises(OSError, match="write failed"):
                    bytesio_response(buf, filename="report.xlsx")
                mock_unlink.assert_called_once_with("C:\\tmp\\tmpfile.xlsx")

    def test_exception_cleanup_oserror_passes(self):
        buf = BytesIO(b"data")
        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.xlsx"
        mock_tmp.write.side_effect = OSError("write failed")

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp):
            with patch("os.unlink", side_effect=OSError("unlink failed")) as mock_unlink:
                with pytest.raises(OSError, match="write failed"):
                    bytesio_response(buf, filename="report.xlsx")
                mock_unlink.assert_called_once_with("C:\\tmp\\tmpfile.xlsx")


# ============================================================================
# filepath_response
# ============================================================================

class TestFilepathResponse:
    def test_with_filename(self):
        result = filepath_response("C:\\data\\report.xlsx", filename="custom.xlsx")
        assert isinstance(result, FileResponse)
        assert result.filename == "custom.xlsx"
        assert result.path == "C:\\data\\report.xlsx"

    def test_without_filename_uses_basename(self):
        with patch("os.path.basename", return_value="report.xlsx"):
            result = filepath_response("C:\\data\\report.xlsx")
        assert result.filename == "report.xlsx"

    def test_default_media_type(self):
        result = filepath_response("C:\\data\\report.xlsx", filename="r.xlsx")
        assert result.media_type == "application/octet-stream"

    def test_custom_media_type(self):
        result = filepath_response("C:\\data\\report.xlsx", filename="r.xlsx", media_type="application/json")
        assert result.media_type == "application/json"


# ============================================================================
# file_response
# ============================================================================

class TestFileResponse:
    def test_normal_flow(self):
        fp = MagicMock()
        fp.read.return_value = b"file content"

        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.pdf"

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp) as mock_ntf:
            result = file_response(fp, filename="doc.pdf")

        assert isinstance(result, FileResponse)
        fp.seek.assert_called_once_with(0)
        fp.read.assert_called_once()
        mock_ntf.assert_called_once_with(suffix=".pdf", delete=False)
        mock_tmp.write.assert_called_once_with(b"file content")
        mock_tmp.close.assert_called_once()
        fp.close.assert_called_once()
        assert result.filename == "doc.pdf"

    def test_default_filename(self):
        fp = BytesIO(b"data")
        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.tmp"

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp):
            result = file_response(fp)

        assert result.filename == "download"

    def test_no_extension(self):
        fp = MagicMock()
        fp.read.return_value = b"data"
        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.tmp"

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp) as mock_ntf:
            result = file_response(fp, filename="download")

        assert isinstance(result, FileResponse)
        mock_ntf.assert_called_once_with(suffix=".tmp", delete=False)

    def test_exception_during_write_cleans_up_and_closes_fp(self):
        fp = MagicMock()
        fp.read.return_value = b"data"

        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.pdf"
        mock_tmp.write.side_effect = OSError("write failed")

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp):
            with patch("os.unlink") as mock_unlink:
                with pytest.raises(OSError, match="write failed"):
                    file_response(fp, filename="doc.pdf")
                mock_unlink.assert_called_once_with("C:\\tmp\\tmpfile.pdf")
                fp.close.assert_called_once()

    def test_exception_cleanup_unlink_oserror_passes(self):
        fp = MagicMock()
        fp.read.return_value = b"data"

        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.pdf"
        mock_tmp.write.side_effect = OSError("write failed")

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp):
            with patch("os.unlink", side_effect=OSError("unlink failed")):
                with pytest.raises(OSError, match="write failed"):
                    file_response(fp, filename="doc.pdf")
                fp.close.assert_called_once()

    def test_fp_close_exception_passes(self):
        """If fp.close() raises, the exception is caught and swallowed."""
        fp = MagicMock()
        fp.read.return_value = b"data"
        fp.close.side_effect = OSError("close failed")

        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.pdf"

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp):
            result = file_response(fp, filename="doc.pdf")

        assert isinstance(result, FileResponse)
        fp.close.assert_called_once()

    def test_exception_during_read_cleans_up(self):
        """If fp.read() raises, cleanup still happens."""
        fp = MagicMock()
        fp.read.side_effect = OSError("read failed")

        mock_tmp = MagicMock()
        mock_tmp.name = "C:\\tmp\\tmpfile.pdf"

        with patch("tempfile.NamedTemporaryFile", return_value=mock_tmp):
            with patch("os.unlink") as mock_unlink:
                with pytest.raises(OSError, match="read failed"):
                    file_response(fp, filename="doc.pdf")
                mock_unlink.assert_called_once_with("C:\\tmp\\tmpfile.pdf")
                fp.close.assert_called_once()
