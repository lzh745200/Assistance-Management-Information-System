"""
帮扶村聚合根

帮扶村是乡村振兴的基本单元，管理帮扶村的所有信息。
"""

from datetime import timezone, date, datetime
from typing import List, Optional
from enum import Enum
from decimal import Decimal

from app.services.domain import AggregateRoot, DomainEvent
from app.services.event_bus import event_bus


class VillageStatus(str, Enum):
    """帮扶村状态"""

    PENDING = "pending"  # 待帮扶
    ACTIVE = "active"  # 帮扶中
    COMPLETED = "completed"  # 已退出
    SUSPENDED = "suspended"  # 暂停帮扶


class SupportTarget:
    """帮扶对象值对象"""

    def __init__(
        self,
        target_id: str,
        name: str,
        target_type: str,  # household, individual, group
        poverty_level: Optional[str] = None,
        needs: Optional[str] = None,
        status: str = "active",
    ):
        self.target_id = target_id
        self.name = name
        self.target_type = target_type
        self.poverty_level = poverty_level
        self.needs = needs
        self.status = status
        self.created_at = datetime.now(timezone.utc)


class VillageAggregate(AggregateRoot):
    """
    帮扶村聚合根

    职责：
    - 维护帮扶村基本信息
    - 管理帮扶对象
    - 跟踪帮扶需求
    - 记录成效数据
    """

    def __init__(
        self,
        village_id: str,
        name: str,
        province: str,
        city: str,
        county: str,
        township: Optional[str] = None,
        status: VillageStatus = VillageStatus.PENDING,
    ):
        super().__init__(village_id)
        self._name = name
        self._province = province
        self._city = city
        self._county = county
        self._township = township
        self._status = status
        self._support_targets: List[SupportTarget] = []
        self._project_ids: List[str] = []
        self._population: Optional[int] = None
        self._poverty_population: Optional[int] = None
        self._per_capita_income: Optional[Decimal] = None
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)

    # 属性访问
    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> VillageStatus:
        return self._status

    @property
    def location(self) -> dict:
        """完整位置信息"""
        return {"province": self._province, "city": self._city, "county": self._county, "township": self._township}

    @property
    def support_targets(self) -> List[SupportTarget]:
        return self._support_targets.copy()

    @property
    def project_ids(self) -> List[str]:
        return self._project_ids.copy()

    @property
    def population(self) -> Optional[int]:
        return self._population

    @property
    def poverty_population(self) -> Optional[int]:
        return self._poverty_population

    @property
    def per_capita_income(self) -> Optional[Decimal]:
        return self._per_capita_income

    # 业务方法
    def activate(self) -> None:
        """启动帮扶"""
        if self._status != VillageStatus.PENDING:
            raise ValueError(f"无法从 {self._status} 状态启动帮扶")

        self._status = VillageStatus.ACTIVE
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="VILLAGE_ACTIVATED",
            aggregate_id=self.id,
            aggregate_type="Village",
            occurred_at=datetime.now(timezone.utc),
            payload={"name": self._name, "location": self.location},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def complete_support(self) -> None:
        """完成帮扶（退出）"""
        if self._status != VillageStatus.ACTIVE:
            raise ValueError("只有帮扶中的村庄可以退出")

        self._status = VillageStatus.COMPLETED
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="VILLAGE_COMPLETED",
            aggregate_id=self.id,
            aggregate_type="Village",
            occurred_at=datetime.now(timezone.utc),
            payload={"exit_date": date.today().isoformat()},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def suspend(self, reason: str) -> None:
        """暂停帮扶"""
        if self._status != VillageStatus.ACTIVE:
            raise ValueError("只有帮扶中的村庄可以暂停")

        self._status = VillageStatus.SUSPENDED
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="VILLAGE_SUSPENDED",
            aggregate_id=self.id,
            aggregate_type="Village",
            occurred_at=datetime.now(timezone.utc),
            payload={"reason": reason},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def resume(self) -> None:
        """恢复帮扶"""
        if self._status != VillageStatus.SUSPENDED:
            raise ValueError("只有暂停的村庄可以恢复")

        self._status = VillageStatus.ACTIVE
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="VILLAGE_RESUMED",
            aggregate_id=self.id,
            aggregate_type="Village",
            occurred_at=datetime.now(timezone.utc),
            payload={},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def add_support_target(self, target: SupportTarget) -> None:
        """添加帮扶对象"""
        self._support_targets.append(target)
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="SUPPORT_TARGET_ADDED",
            aggregate_id=self.id,
            aggregate_type="Village",
            occurred_at=datetime.now(timezone.utc),
            payload={"target_id": target.target_id, "target_name": target.name, "target_type": target.target_type},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def remove_support_target(self, target_id: str) -> None:
        """移除帮扶对象"""
        target = next((t for t in self._support_targets if t.target_id == target_id), None)
        if target:
            self._support_targets = [t for t in self._support_targets if t.target_id != target_id]
            self._updated_at = datetime.now(timezone.utc)

    def update_demographics(self, population: int, poverty_population: int, per_capita_income: Decimal) -> None:
        """更新人口统计信息"""
        self._population = population
        self._poverty_population = poverty_population
        self._per_capita_income = per_capita_income
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="DEMOGRAPHICS_UPDATED",
            aggregate_id=self.id,
            aggregate_type="Village",
            occurred_at=datetime.now(timezone.utc),
            payload={
                "population": population,
                "poverty_population": poverty_population,
                "per_capita_income": str(per_capita_income),
            },
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def link_project(self, project_id: str) -> None:
        """关联项目"""
        if project_id not in self._project_ids:
            self._project_ids.append(project_id)
            self._updated_at = datetime.now(timezone.utc)

    # 查询方法
    @property
    def poverty_rate(self) -> Optional[float]:
        """贫困发生率"""
        if self._population and self._population > 0:
            return (self._poverty_population or 0) / self._population
        return None

    def get_active_targets(self) -> List[SupportTarget]:
        """获取活跃的帮扶对象"""
        return [t for t in self._support_targets if t.status == "active"]

    def has_active_project(self) -> bool:
        """是否有进行中项目（简单检查）"""
        return len(self._project_ids) > 0
