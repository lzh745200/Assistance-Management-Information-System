"""分块上传服务单元测试"""
import pytest

def test_service_exists():
    from app.services.chunked_upload_service import ChunkedUploadService
    assert ChunkedUploadService is not None

def test_status_enum():
    from app.services.chunked_upload_service import UploadStatus
    assert UploadStatus.PENDING is not None
    assert UploadStatus.COMPLETED is not None
