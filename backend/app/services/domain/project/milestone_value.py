"""
里程碑值对象
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


class MilestoneStatus(str):
    """里程碑状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"


@dataclass
class MilestoneValue:
    """里程碑值对象"""

    milestone_id: str
    name: str
    planned_date: date
    status: str = MilestoneStatus.PENDING
    actual_date: Optional[date] = None
    description: Optional[str] = None
    completion_percentage: float = 0.0

    @property
    def is_completed(self) -> bool:
        return self.status == MilestoneStatus.COMPLETED

    @property
    def is_overdue(self) -> bool:
        if self.is_completed or not self.planned_date:
            return False
        return date.today() > self.planned_date

    def complete(self, actual_date: Optional[date] = None) -> None:
        """完成里程碑"""
        self.status = MilestoneStatus.COMPLETED
        self.actual_date = actual_date or date.today()
        self.completion_percentage = 100.0

    def update_progress(self, percentage: float) -> None:
        """更新进度"""
        self.completion_percentage = max(0.0, min(100.0, percentage))
        if self.completion_percentage >= 100.0:
            self.status = MilestoneStatus.COMPLETED
        elif self.completion_percentage > 0:
            self.status = MilestoneStatus.IN_PROGRESS
