"""Test data factories — generate model instances with sensible defaults."""

from .user_factory import UserFactory, UserOrganizationFactory
from .organization_factory import OrganizationFactory
from .village_factory import SupportedVillageFactory
from .project_factory import ProjectFactory, ProjectTaskFactory, ProjectFileFactory
from .fund_factory import FundFactory, FundAttachmentFactory
from .approval_factory import (
    ApprovalWorkflowFactory, ApprovalNodeFactory,
    ApprovalTaskFactory, ApprovalRecordFactory,
)
from .school_factory import SchoolFactory
from .common_factory import RegionFactory, RoleFactory, PolicyFactory

__all__ = [
    "UserFactory", "UserOrganizationFactory",
    "OrganizationFactory",
    "SupportedVillageFactory",
    "ProjectFactory", "ProjectTaskFactory", "ProjectFileFactory",
    "FundFactory", "FundAttachmentFactory",
    "ApprovalWorkflowFactory", "ApprovalNodeFactory",
    "ApprovalTaskFactory", "ApprovalRecordFactory",
    "SchoolFactory",
    "RegionFactory", "RoleFactory", "PolicyFactory",
]
