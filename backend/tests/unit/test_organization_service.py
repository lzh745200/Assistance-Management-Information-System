"""
组织管理服务单元测试
覆盖: app/services/organization_service.py
"""
from unittest.mock import MagicMock


class TestOrganizationExceptions:
    def test_organization_not_found_error(self):
        from app.services.organization_service import OrganizationNotFoundError
        err = OrganizationNotFoundError(42)
        assert err.org_id == 42
        assert "42" in str(err)

    def test_organization_has_subordinates_error(self):
        from app.services.organization_service import OrganizationHasSubordinatesError
        err = OrganizationHasSubordinatesError(1, 5)
        assert err.org_id == 1
        assert err.subordinate_count == 5
        assert "5" in str(err)

    def test_organization_code_duplicate_error(self):
        from app.services.organization_service import OrganizationCodeDuplicateError
        err = OrganizationCodeDuplicateError("ORG-001")
        assert err.code == "ORG-001"
        assert "ORG-001" in str(err)

    def test_exceptions_inherit_business_error(self):
        from app.services.organization_service import (
            OrganizationNotFoundError,
            OrganizationHasSubordinatesError,
            OrganizationCodeDuplicateError,
        )
        from app.core.exceptions import BusinessError

        assert issubclass(OrganizationNotFoundError, BusinessError)
        assert issubclass(OrganizationHasSubordinatesError, BusinessError)
        assert issubclass(OrganizationCodeDuplicateError, BusinessError)


class TestOrganizationServiceInit:
    def test_init_with_db(self):
        from app.services.organization_service import OrganizationService
        mock_db = MagicMock()
        svc = OrganizationService(db=mock_db)
        assert svc.db is mock_db

    def test_init_db_is_set(self):
        from app.services.organization_service import OrganizationService
        mock_db = MagicMock()
        svc = OrganizationService(db=mock_db)
        assert svc.db is mock_db


class TestOrganizationTreeNode:
    def test_create_node(self):
        from app.schemas.organization import OrganizationTreeNode
        node = OrganizationTreeNode(
            id=1,
            name="Test Org",
            code="ORG-001",
            children=[],
        )
        assert node.id == 1
        assert node.name == "Test Org"
        assert node.code == "ORG-001"
        assert node.children == []
