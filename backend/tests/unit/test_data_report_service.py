"""数据上报服务单元测试"""
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_db(): return MagicMock()

def test_service_instantiable(mock_db):
    from app.services.data_report_service import DataReportService
    svc = DataReportService(db=mock_db)
    assert svc.db is mock_db

def test_data_report_service_exists(mock_db):
    from app.services.data_report_service import DataReportService
    svc = DataReportService(db=mock_db)
    assert svc.db is mock_db
