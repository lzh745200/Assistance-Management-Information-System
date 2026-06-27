"""Work log服务单元测试"""
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_db(): return MagicMock()

@pytest.fixture
def svc(mock_db):
    from app.services.work_log_service import WorkLogService
    return WorkLogService(db=mock_db)

def test_init(mock_db):
    from app.services.work_log_service import WorkLogService
    assert WorkLogService(db=mock_db).db is mock_db

def test_get_work_logs(svc, mock_db):
    q = MagicMock()
    mock_db.query.return_value = q
    q.count.return_value = 0
    q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    items, total = svc.get_work_logs()
    assert items == [] and total == 0

def test_get_work_log_found(svc, mock_db):
    mock_log = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_log
    assert svc.get_work_log(1) is mock_log

def test_get_work_log_not_found(svc, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    assert svc.get_work_log(999) is None

def test_create_work_log_method_exists(svc):
    """create_work_log exists and is callable"""
    assert callable(svc.create_work_log)

def test_update_work_log_not_found(svc, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    assert svc.update_work_log(999, {}) is None

def test_update_work_log_success(svc, mock_db):
    mock_log = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_log
    mock_db.commit = MagicMock()
    result = svc.update_work_log(1, {"title": "new"})
    assert result is mock_log

def test_delete_work_log_not_found(svc, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    assert svc.delete_work_log(999) is None

def test_delete_work_log_success(svc, mock_db):
    mock_log = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_log
    mock_db.delete = MagicMock(); mock_db.commit = MagicMock()
    assert svc.delete_work_log(1) is mock_log
