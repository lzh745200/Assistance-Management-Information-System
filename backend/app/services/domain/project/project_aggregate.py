"""
项目聚合根

项目是帮扶工作的核心单元，封装了项目的生命周期和业务规则。
"""

from datetime import timezone, date, datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum

from app.services.domain import AggregateRoot, DomainEvent
from app.services.event_bus import event_bus


class ProjectStatus(str, Enum):
    """项目状态"""

    DRAFT = "draft"  # 草稿
    PROPOSED = "proposed"  # 已申报
    UNDER_REVIEW = "under_review"  # 审核中
    APPROVED = "approved"  # 已批准
    IN_PROGRESS = "in_progress"  # 进行中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class ProjectType(str, Enum):
    """项目类型"""

    INFRASTRUCTURE = "infrastructure"  # 基础设施
    INDUSTRY = "industry"  # 产业扶持
    EDUCATION = "education"  # 教育培训
    HEALTHCARE = "healthcare"  # 医疗卫生
    CULTURE = "culture"  # 文化惠民
    ENVIRONMENT = "environment"  # 生态环保
    OTHER = "other"  # 其他


class MilestoneValue:
    """里程碑值对象"""

    def __init__(
        self,
        milestone_id: str,
        name: str,
        planned_date: date,
        status: str = "pending",
        actual_date: Optional[date] = None,
        description: Optional[str] = None,
    ):
        self.milestone_id = milestone_id
        self.name = name
        self.planned_date = planned_date
        self.status = status
        self.actual_date = actual_date
        self.description = description

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_overdue(self) -> bool:
        if self.is_completed or not self.planned_date:
            return False
        return date.today() > self.planned_date

    def complete(self, actual_date: Optional[date] = None) -> None:
        """完成里程碑"""
        self.status = "completed"
        self.actual_date = actual_date or date.today()


class ProjectAggregate(AggregateRoot):
    """
    项目聚合根

    职责：
    - 维护项目的基本信息和状态
    - 管理项目里程碑
    - 关联帮扶村和经费
    - 确保业务规则的一致性
    """

    def __init__(
        self,
        project_id: str,
        name: str,
        project_type: ProjectType,
        village_id: str,
        planned_start: date,
        planned_end: date,
        budget_amount: Decimal,
        description: Optional[str] = None,
        status: ProjectStatus = ProjectStatus.DRAFT,
    ):
        super().__init__(project_id)
        self._name = name
        self._type = project_type
        self._village_id = village_id
        self._planned_start = planned_start
        self._planned_end = planned_end
        self._budget_amount = budget_amount
        self._description = description
        self._status = status
        self._actual_start: Optional[date] = None
        self._actual_end: Optional[date] = None
        self._milestones: List[MilestoneValue] = []
        self._fund_ids: List[str] = []
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)

    # 属性访问
    @property
    def name(self) -> str:
        return self._name

    @property
    def project_type(self) -> ProjectType:
        return self._type

    @property
    def village_id(self) -> str:
        return self._village_id

    @property
    def status(self) -> ProjectStatus:
        return self._status

    @property
    def planned_start(self) -> date:
        return self._planned_start

    @property
    def planned_end(self) -> date:
        return self._planned_end

    @property
    def budget_amount(self) -> Decimal:
        return self._budget_amount

    @property
    def milestones(self) -> List[MilestoneValue]:
        return self._milestones.copy()

    @property
    def fund_ids(self) -> List[str]:
        return self._fund_ids.copy()

    # 业务方法
    def submit(self) -> None:
        """提交项目申报"""
        if self._status != ProjectStatus.DRAFT:
            raise ValueError(f"无法从 {self._status} 状态提交申报")

        self._status = ProjectStatus.PROPOSED
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="PROJECT_SUBMITTED",
            aggregate_id=self.id,
            aggregate_type="Project",
            occurred_at=datetime.now(timezone.utc),
            payload={"name": self._name, "type": self._type.value},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def approve(self, approver_id: str) -> None:
        """批准项目"""
        if self._status not in [ProjectStatus.PROPOSED, ProjectStatus.UNDER_REVIEW]:
            raise ValueError(f"无法批准 {self._status} 状态的项目")

        self._status = ProjectStatus.APPROVED
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="PROJECT_APPROVED",
            aggregate_id=self.id,
            aggregate_type="Project",
            occurred_at=datetime.now(timezone.utc),
            payload={"approver_id": approver_id, "village_id": self._village_id},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def start(self) -> None:
        """启动项目"""
        if self._status != ProjectStatus.APPROVED:
            raise ValueError(f"无法启动 {self._status} 状态的项目")

        self._status = ProjectStatus.IN_PROGRESS
        self._actual_start = date.today()
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="PROJECT_STARTED",
            aggregate_id=self.id,
            aggregate_type="Project",
            occurred_at=datetime.now(timezone.utc),
            payload={"start_date": self._actual_start.isoformat()},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def pause(self, reason: str) -> None:
        """暂停项目"""
        if self._status != ProjectStatus.IN_PROGRESS:
            raise ValueError("只有进行中的项目可以暂停")

        self._status = ProjectStatus.PAUSED
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="PROJECT_PAUSED",
            aggregate_id=self.id,
            aggregate_type="Project",
            occurred_at=datetime.now(timezone.utc),
            payload={"reason": reason},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def resume(self) -> None:
        """恢复项目"""
        if self._status != ProjectStatus.PAUSED:
            raise ValueError("只有暂停的项目可以恢复")

        self._status = ProjectStatus.IN_PROGRESS
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="PROJECT_RESUMED",
            aggregate_id=self.id,
            aggregate_type="Project",
            occurred_at=datetime.now(timezone.utc),
            payload={},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def complete(self) -> None:
        """完成项目"""
        if self._status not in [ProjectStatus.IN_PROGRESS, ProjectStatus.PAUSED]:
            raise ValueError(f"无法完成 {self._status} 状态的项目")

        self._status = ProjectStatus.COMPLETED
        self._actual_end = date.today()
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="PROJECT_COMPLETED",
            aggregate_id=self.id,
            aggregate_type="Project",
            occurred_at=datetime.now(timezone.utc),
            payload={
                "actual_start": self._actual_start.isoformat() if self._actual_start else None,
                "actual_end": self._actual_end.isoformat(),
            },
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def add_milestone(self, milestone: MilestoneValue) -> None:
        """添加里程碑"""
        if self._status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]:
            raise ValueError("已完成或已取消的项目不能添加里程碑")

        self._milestones.append(milestone)
        self._updated_at = datetime.now(timezone.utc)

    def complete_milestone(self, milestone_id: str) -> None:
        """完成里程碑"""
        milestone = next((m for m in self._milestones if m.milestone_id == milestone_id), None)
        if not milestone:
            raise ValueError(f"里程碑 {milestone_id} 不存在")

        milestone.complete()
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="MILESTONE_COMPLETED",
            aggregate_id=self.id,
            aggregate_type="Project",
            occurred_at=datetime.now(timezone.utc),
            payload={"milestone_id": milestone_id, "milestone_name": milestone.name},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def link_fund(self, fund_id: str) -> None:
        """关联经费"""
        if fund_id not in self._fund_ids:
            self._fund_ids.append(fund_id)
            self._updated_at = datetime.now(timezone.utc)

    # 查询方法
    @property
    def is_overdue(self) -> bool:
        """项目是否超期"""
        if self._status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]:
            return False
        if not self._planned_end:
            return False
        return date.today() > self._planned_end

    @property
    def completion_rate(self) -> float:
        """完成率（基于里程碑）"""
        if not self._milestones:
            return 0.0
        completed = sum(1 for m in self._milestones if m.is_completed)
        return completed / len(self._milestones)

    def get_overdue_milestones(self) -> List[MilestoneValue]:
        """获取逾期的里程碑"""
        return [m for m in self._milestones if m.is_overdue]
