"""Test data factories — generate model instances with sensible defaults."""

from .user_factory import UserFactory, UserOrganizationFactory
from .organization_factory import OrganizationFactory
from .village_factory import (
    SupportedVillageFactory, VillagePopulationFactory, VillageIncomeFactory,
    SupportFundingFactory, ForceInvestmentFactory, IndustrySupportFactory,
    InfrastructureImprovementFactory, PartyBuildingSupportFactory,
    MedicalSupportFactory, ConsumptionSupportFactory, EmploymentSupportFactory,
    EducationSupportFactory,
)
from .project_factory import ProjectFactory, ProjectTaskFactory, ProjectFileFactory
from .fund_factory import FundFactory, FundAttachmentFactory, BudgetRecordFactory
from .approval_factory import (
    ApprovalWorkflowFactory, ApprovalNodeFactory,
    ApprovalTaskFactory, ApprovalRecordFactory,
)
from .school_factory import (
    SchoolFactory, SchoolSupportFactory, SchoolProjectFactory, ScholarshipStudentFactory,
)
from .common_factory import RegionFactory, RoleFactory, PolicyFactory, PolicyCategoryFactory

__all__ = [
    "UserFactory", "UserOrganizationFactory",
    "OrganizationFactory",
    "SupportedVillageFactory", "VillagePopulationFactory", "VillageIncomeFactory",
    "SupportFundingFactory", "ForceInvestmentFactory", "IndustrySupportFactory",
    "InfrastructureImprovementFactory", "PartyBuildingSupportFactory",
    "MedicalSupportFactory", "ConsumptionSupportFactory", "EmploymentSupportFactory",
    "EducationSupportFactory",
    "ProjectFactory", "ProjectTaskFactory", "ProjectFileFactory",
    "FundFactory", "FundAttachmentFactory", "BudgetRecordFactory",
    "ApprovalWorkflowFactory", "ApprovalNodeFactory",
    "ApprovalTaskFactory", "ApprovalRecordFactory",
    "SchoolFactory", "SchoolSupportFactory", "SchoolProjectFactory", "ScholarshipStudentFactory",
    "RegionFactory", "RoleFactory", "PolicyFactory", "PolicyCategoryFactory",
]
