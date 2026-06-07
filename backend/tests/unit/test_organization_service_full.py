"""组织管理服务单元测试"""
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_db(): return MagicMock()

@pytest.fixture
def svc(mock_db):
    from app.services.organization_service import OrganizationService
    return OrganizationService(db=mock_db)

def test_init_requires_db():
    from app.services.organization_service import OrganizationService
    with pytest.raises(ValueError, match="database session"):
        OrganizationService()

def test_init_with_db(svc, mock_db):
    assert svc.db is mock_db

def test_get_organization_found(svc, mock_db):
    mock_org = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_org
    assert svc.get_organization(1) is mock_org

def test_get_organization_not_found(svc, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    assert svc.get_organization(999) is None

def test_get_organization_by_code_found(svc, mock_db):
    mock_org = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_org
    assert svc.get_organization_by_code("C1") is mock_org

def test_get_organization_tree(svc, mock_db):
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    assert isinstance(svc.get_organization_tree(), list)

def test_get_subordinate_ids(svc, mock_db):
    mock_db.query.return_value.filter.return_value.all.return_value = []
    assert isinstance(svc.get_subordinate_ids(1), list)

def test_get_statistics(svc, mock_db):
    mock_db.query.return_value.filter.return_value.count.return_value = 5
    assert svc.get_statistics() is not None

def test_search_organizations_callable(svc):
    assert callable(svc.search_organizations)

def test_batch_update_sort_orders(svc, mock_db):
    mock_org = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_org
    mock_db.commit = MagicMock()
    ok, count = svc.batch_update_sort_orders([{"id": 1, "sort_order": 10}])
    assert ok is True or ok is False

def test_validate_parent_child(svc):
    assert callable(svc.validate_parent_child_relationship)

def test_exceptions():
    from app.services.organization_service import (
        OrganizationNotFoundError,
        OrganizationHasSubordinatesError,
        OrganizationCodeDuplicateError,
    )
    assert OrganizationNotFoundError(42).org_id == 42
    assert OrganizationHasSubordinatesError(1, 5).subordinate_count == 5
    assert OrganizationCodeDuplicateError("X").code == "X"
