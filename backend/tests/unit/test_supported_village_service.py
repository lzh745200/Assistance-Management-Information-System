"""帮扶村服务单元测试"""
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_db():
    return AsyncMock()

def test_service_instantiable(mock_db):
    from app.services.supported_village_service import SupportedVillageService
    svc = SupportedVillageService(db=mock_db)
    assert svc.db is mock_db

def test_methods_callable(mock_db):
    from app.services.supported_village_service import SupportedVillageService
    svc = SupportedVillageService(db=mock_db)
    assert callable(svc.get_villages)
    assert callable(svc.get_village)
    assert callable(svc.create_village)
    assert callable(svc.update_village)
    assert callable(svc.delete_village)
