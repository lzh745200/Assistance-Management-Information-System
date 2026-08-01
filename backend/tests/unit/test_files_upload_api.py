"""Tests for app.api.v1.files 通用文件上传端点"""

import pytest


class TestFilesUpload:
    def test_upload_success(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            "/api/v1/files/upload",
            files={"file": ("测试文档.pdf", b"%PDF-1.4 test content", "application/pdf")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["code"] == 200
        assert body["data"]["url"].startswith("/uploads/")
        assert body["data"]["url"].endswith(".pdf")
        assert body["data"]["file_name"] == "测试文档.pdf"
        assert body["data"]["file_size"] == len(b"%PDF-1.4 test content")

    def test_upload_with_category(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            "/api/v1/files/upload?category=policies",
            files={"file": ("note.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 200
        assert "/uploads/generic/policies/" in resp.json()["data"]["url"]

    def test_upload_rejects_unsupported_type(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            "/api/v1/files/upload",
            files={"file": ("evil.exe", b"MZ", "application/octet-stream")},
        )
        assert resp.status_code == 400
        assert "不支持的文件类型" in resp.json()["detail"]

    def test_upload_rejects_empty_filename(self, client_with_mocked_auth):
        resp = client_with_mocked_auth.post(
            "/api/v1/files/upload",
            files={"file": ("", b"data", "application/octet-stream")},
        )
        assert resp.status_code == 422

    def test_upload_requires_auth(self, client):
        resp = client.post("/api/v1/files/upload", files={"file": ("a.txt", b"x", "text/plain")})
        assert resp.status_code == 401
