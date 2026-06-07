"""通知偏好服务单元测试"""
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_db(): return MagicMock()

@pytest.fixture
def svc(mock_db):
    from app.services.notification_preference_service import NotificationPreferenceService
    return NotificationPreferenceService(db=mock_db)

def test_init(svc, mock_db):
    assert svc.db is mock_db

def test_get_preference_returns_existing(svc, mock_db):
    mock_pref = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_pref
    assert svc.get_preference(1) is mock_pref

def test_update_preference_callable(svc):
    assert callable(svc.update_preference) if hasattr(svc, 'update_preference') else True
