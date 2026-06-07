"""导入导出历史服务单元测试"""
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db

@pytest.fixture
def svc(mock_db):
    from app.services.import_export_history_service import ImportExportHistoryService
    return ImportExportHistoryService(db=mock_db)

def test_init(svc, mock_db):
    assert svc.db is mock_db

def test_list_history_callable(svc):
    assert callable(svc.list_history)
