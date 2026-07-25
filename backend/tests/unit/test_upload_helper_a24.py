"""app.utils.upload_helper 覆盖补充测试（a24）

缺口：64-106（save_upload_file 主体）、135-151（get_attachment_response 主体）、
167-174（delete_attachment_file）。
"""
import io
import os

import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, UploadFile

import app.utils.upload_helper as uh
from app.utils.upload_helper import (
    delete_attachment_file,
    get_attachment_response,
    save_upload_file,
)


@pytest.fixture
def mock_settings(tmp_path):
    settings = MagicMock()
    settings.MAX_FILE_SIZE = 1024
    settings.UPLOAD_DIR = str(tmp_path)
    settings.allowed_file_types_list = ["pdf", "txt"]
    with patch.object(uh, "settings", settings):
        yield settings


def _upload(content: bytes, filename):
    return UploadFile(file=io.BytesIO(content), filename=filename)


class TestSaveUploadFile:
    @pytest.mark.asyncio
    async def test_save_success(self, mock_settings, tmp_path):
        file = _upload(b"hello world", "report.txt")
        info = await save_upload_file(file, sub_dir="funds/123")

        assert info["file_name"] == "report.txt"
        assert info["file_size"] == len(b"hello world")
        assert info["file_type"] == "application/octet-stream"
        saved = tmp_path / "funds" / "123"
        assert saved.is_dir()
        files = list(saved.iterdir())
        assert len(files) == 1
        assert files[0].name.endswith("_report.txt")
        assert files[0].read_bytes() == b"hello world"
        assert os.path.realpath(info["file_path"]) == os.path.realpath(str(files[0]))

    @pytest.mark.asyncio
    async def test_save_uses_default_max_size(self, mock_settings):
        # max_size=None 时使用 settings.MAX_FILE_SIZE（1024）
        file = _upload(b"x" * 1025, "big.txt")
        with pytest.raises(HTTPException) as exc_info:
            await save_upload_file(file, sub_dir="a")
        assert exc_info.value.status_code == 400
        assert "文件大小超过限制" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_save_explicit_max_size(self, mock_settings):
        file = _upload(b"123456", "big.txt")
        with pytest.raises(HTTPException) as exc_info:
            await save_upload_file(file, sub_dir="a", max_size=5)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_save_disallowed_extension(self, mock_settings):
        file = _upload(b"data", "evil.exe")
        with pytest.raises(HTTPException) as exc_info:
            await save_upload_file(file, sub_dir="a", allowed_extensions={"pdf"})
        assert exc_info.value.status_code == 400
        assert "不支持的文件类型" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_save_filename_without_extension_skips_type_check(self, mock_settings, tmp_path):
        file = _upload(b"data", "noext")
        info = await save_upload_file(file, sub_dir="plain", allowed_extensions={"pdf"})
        assert info["file_name"] == "noext"

    @pytest.mark.asyncio
    async def test_save_filename_none(self, mock_settings, tmp_path):
        file = _upload(b"data", None)
        info = await save_upload_file(file, sub_dir="noname")
        assert info["file_name"] == "unknown"
        assert "_unknown" in info["file_path"]

    @pytest.mark.asyncio
    async def test_save_write_failure(self, mock_settings):
        file = _upload(b"data", "a.txt")
        with patch("builtins.open", side_effect=OSError("disk full")):
            with pytest.raises(HTTPException) as exc_info:
                await save_upload_file(file, sub_dir="broken")
        assert exc_info.value.status_code == 500


class TestGetAttachmentResponse:
    def test_not_found(self, tmp_path):
        with pytest.raises(HTTPException) as exc_info:
            get_attachment_response(str(tmp_path / "missing.txt"), "missing.txt")
        assert exc_info.value.status_code == 404

    def test_explicit_media_type(self, tmp_path):
        f = tmp_path / "a.bin"
        f.write_bytes(b"x")
        resp = get_attachment_response(str(f), "a.bin", media_type="text/plain")
        assert resp.media_type == "text/plain"

    def test_guessed_media_type(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_bytes(b"x")
        resp = get_attachment_response(str(f), "a.txt")
        assert resp.media_type == "text/plain"

    def test_unknown_media_type_fallback(self, tmp_path):
        f = tmp_path / "a.unlikelyext123"
        f.write_bytes(b"x")
        resp = get_attachment_response(str(f), "a.unlikelyext123")
        assert resp.media_type == "application/octet-stream"

    def test_inline_disposition(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_bytes(b"x")
        resp = get_attachment_response(str(f), "a.txt", inline=True)
        assert resp.headers["content-disposition"].startswith("inline;")


class TestDeleteAttachmentFile:
    def test_empty_path(self):
        assert delete_attachment_file("") is False

    def test_not_exists(self, tmp_path):
        assert delete_attachment_file(str(tmp_path / "nope.txt")) is False

    def test_delete_success(self, tmp_path):
        f = tmp_path / "del.txt"
        f.write_bytes(b"x")
        assert delete_attachment_file(str(f)) is True
        assert not f.exists()

    def test_delete_oserror(self, tmp_path):
        f = tmp_path / "del.txt"
        f.write_bytes(b"x")
        with patch.object(uh.os, "remove", side_effect=OSError("denied")):
            assert delete_attachment_file(str(f)) is False
        assert f.exists()
