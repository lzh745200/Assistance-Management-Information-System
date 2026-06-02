"""
项目管理域

核心业务：
- 帮扶项目生命周期管理
- 项目进度跟踪
- 项目关联资金管理
"""

from .project_aggregate import ProjectAggregate, ProjectStatus, ProjectType
from .milestone_value import MilestoneValue, MilestoneStatus
from .project_repository import ProjectRepository
from .project_domain_service import ProjectDomainService
from .value_objects import DateRange

__all__ = [
    "ProjectAggregate",
    "ProjectStatus",
    "ProjectType",
    "MilestoneValue",
    "MilestoneStatus",
    "ProjectRepository",
    "ProjectDomainService",
    "DateRange",
]
