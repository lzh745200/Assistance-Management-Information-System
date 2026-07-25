"""app/core/file_upload.py 覆盖率补缺测试

补缺行：71-81（python-magic 可用时的内容嗅探与异常回退、扩展名兜底映射）、
98-102（detect_mime_type_from_bytes 的 magic 分支）、
188-189（get_upload_dir 导入 app.core.config 失败时的回退）。
"""

import sys
from unittest.mock import MagicMock, patch

import app.core.file_upload as fu
from app.core.file_upload import (
    detect_mime_type,
    detect_mime_type_from_bytes,
    get_upload_dir,
)


def _no_guess_type():
    """让 stdlib mimetypes 无法识别扩展名，进入后续检测分支。"""
    return patch("app.core.file_upload.mimetypes.guess_type", return_value=(None, None))


# ── detect_mime_type：magic 分支（lines 71-77）与扩展名兜底（lines 80-81） ──


class TestDetectMimeTypeMagicBranch:
    def test_magic_available_returns_sniffed_type(self):
        """magic 可用且嗅探成功 → 返回内容嗅探结果（覆盖 71-74）。"""
        mock_magic = MagicMock()
        mock_magic.Magic.return_value.from_file.return_value = "image/webp"

        with _no_guess_type(), patch.object(fu, "magic", mock_magic):
            result = detect_mime_type("/fake/picture.unknownext99")

        assert result == "image/webp"
        mock_magic.Magic.assert_called_once_with(mime=True)
        mock_magic.Magic.return_value.from_file.assert_called_once_with("/fake/picture.unknownext99")

    def test_magic_failure_falls_back_to_extension_mapping(self):
        """magic 嗅探抛异常 → 回退到内部扩展名映射（覆盖 75-77、80-81）。"""
        mock_magic = MagicMock()
        mock_magic.Magic.return_value.from_file.side_effect = RuntimeError("libmagic boom")

        with _no_guess_type(), patch.object(fu, "magic", mock_magic):
            result = detect_mime_type("/fake/data.weird")

        # ".weird" 不在映射表中 → octet-stream
        assert result == "application/octet-stream"

    def test_no_magic_unknown_extension_uses_mapping(self):
        """magic 不可用且扩展名无法识别 → 内部映射兜底（覆盖 80-81）。"""
        assert fu.magic is None  # 当前环境 python-magic 不可用

        with _no_guess_type():
            assert detect_mime_type("/fake/notes.zzztop") == "application/octet-stream"
            assert detect_mime_type("/fake/report.CSV") == "text/csv"  # 后缀转小写后命中映射


# ── detect_mime_type_from_bytes：magic 分支（lines 98-102） ───────────────


class TestDetectMimeTypeFromBytesMagicBranch:
    def test_magic_available_returns_sniffed_type(self):
        """magic 可用且嗅探成功 → 返回缓冲内容嗅探结果（覆盖 97-100）。"""
        mock_magic = MagicMock()
        mock_magic.Magic.return_value.from_buffer.return_value = "text/plain"

        with patch.object(fu, "magic", mock_magic):
            result = detect_mime_type_from_bytes(b"hello")

        assert result == "text/plain"
        mock_magic.Magic.return_value.from_buffer.assert_called_once_with(b"hello")

    def test_magic_failure_returns_octet_stream(self):
        """magic 嗅探抛异常 → 安全回退 application/octet-stream（覆盖 101-102）。"""
        mock_magic = MagicMock()
        mock_magic.Magic.return_value.from_buffer.side_effect = ValueError("bad buffer")

        with patch.object(fu, "magic", mock_magic):
            result = detect_mime_type_from_bytes(b"\x00\x01")

        assert result == "application/octet-stream"


# ── get_upload_dir：config 导入失败回退（lines 188-189） ──────────────────


class TestGetUploadDirImportFailure:
    def test_config_import_failure_falls_back_to_default(self):
        """from app.core.config import settings 抛异常 → settings=None 走默认目录
        （覆盖 188-189）。sys.modules 置 None 会触发 ImportError，patch.dict 退出后自动还原。"""
        with patch.dict(sys.modules, {"app.core.config": None}):
            with patch("app.core.file_upload.Path") as mock_path:
                mock_path.return_value.absolute.return_value = "/fake/uploads"
                result = get_upload_dir(settings=None)

        # 回退到默认 ./uploads 并创建目录
        mock_path.assert_called_once_with("./uploads")
        mock_path.return_value.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        assert result == "/fake/uploads"
