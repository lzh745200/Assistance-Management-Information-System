"""
帮扶村领域

核心业务：
- 帮扶村信息管理
- 帮扶对象跟踪
- 帮扶需求管理
- 帮扶成效评估
"""

from .village_aggregate import VillageAggregate, VillageStatus
from .support_target import SupportTarget
from .village_repository import VillageRepository
from .village_domain_service import VillageDomainService
from .value_objects import Address

# NOTE: SupportTargetStatus is not yet implemented in support_target.py
# It will be added when the support target lifecycle is completed.

__all__ = [
    "VillageAggregate",
    "VillageStatus",
    "SupportTarget",
    "VillageRepository",
    "VillageDomainService",
    "Address",
]
