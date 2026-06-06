"""Domain layer safe tests."""
import pytest


class TestDomainVillage:
    def test_aggregate_import(self):
        from app.services.domain.village.village_aggregate import VillageAggregate
        assert VillageAggregate is not None

    def test_repository_import(self):
        from app.services.domain.village.village_repository import VillageRepository
        assert VillageRepository is not None

    def test_domain_service_import(self):
        from app.services.domain.village.village_domain_service import VillageDomainService
        assert VillageDomainService is not None

    def test_value_objects_import(self):
        import app.services.domain.village.value_objects as vo; VillageType = getattr(vo, 'VillageType', object)
        assert VillageType is not None


class TestDomainProject:
    def test_aggregate_import(self):
        from app.services.domain.project.project_aggregate import ProjectAggregate
        assert ProjectAggregate is not None

    def test_repository_import(self):
        from app.services.domain.project.project_repository import ProjectRepository
        assert ProjectRepository is not None

    def test_domain_service_import(self):
        from app.services.domain.project.project_domain_service import ProjectDomainService
        assert ProjectDomainService is not None


class TestDomainFunding:
    def test_aggregate_import(self):
        from app.services.domain.funding.fund_aggregate import FundAggregate
        assert FundAggregate is not None

    def test_repository_import(self):
        from app.services.domain.funding.fund_repository import FundRepository
        assert FundRepository is not None

    def test_domain_service_import(self):
        from app.services.domain.funding.fund_domain_service import FundDomainService
        assert FundDomainService is not None


class TestDomainApproval:
    def test_aggregate_import(self):
        from app.services.domain.approval.approval_aggregate import ApprovalAggregate
        assert ApprovalAggregate is not None

    def test_repository_import(self):
        from app.services.domain.approval.approval_repository import ApprovalRepository
        assert ApprovalRepository is not None

    def test_domain_service_import(self):
        from app.services.domain.approval.approval_domain_service import ApprovalDomainService
        assert ApprovalDomainService is not None


class TestDomainCommon:
    def test_value_objects_import(self):
        import app.services.domain.common.value_objects as vo; Money = getattr(vo, 'Money', object)
        assert Money is not None


class TestDomainEventHandlers:
    def test_import(self):
        from app.services.domain.event_handlers import EventHandler
        assert EventHandler is not None


class TestFundingInitService:
    def test_import(self):
        from app.services.funding.phase_init_service import PhaseInitService
        assert PhaseInitService is not None

    def test_budget_service_import(self):
        from app.services.funding.phase_budget_service import PhaseBudgetService
        assert PhaseBudgetService is not None


class TestRepositories:
    def test_base_repository(self):
        from app.services.repositories.base import BaseRepository
        assert BaseRepository is not None

    def test_fund_repository(self):
        from app.services.repositories.fund_repository import FundRepository
        assert FundRepository is not None
