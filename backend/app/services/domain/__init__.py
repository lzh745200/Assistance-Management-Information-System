"""
DDD 领域驱动设计基础模块

提供领域层的基础抽象，支持按业务域组织代码。

目录结构:
    domain/
        __init__.py          # 领域基类导出
        funding/             # 经费管理域
        project/             # 项目管理域
        village/             # 帮扶村域
        approval/            # 审批工作流域
        system/              # 系统管理域
        analytics/           # 数据分析域
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime

T = TypeVar("T")


@dataclass
class DomainEvent:
    """
    领域事件基类
    用于在领域对象之间传递状态变更通知
    """

    event_id: str
    event_type: str
    aggregate_id: str
    aggregate_type: str
    occurred_at: datetime
    payload: Dict[str, Any]


class AggregateRoot(ABC):
    """
    聚合根基类

    聚合根是领域模型的核心，负责：
    - 维护业务一致性边界
    - 发布领域事件
    - 封装业务规则
    """

    def __init__(self, id: str):
        self._id = id
        self._events: List[DomainEvent] = []
        self._version = 0

    @property
    def id(self) -> str:
        return self._id

    @property
    def version(self) -> int:
        return self._version

    def apply_event(self, event: DomainEvent) -> None:
        """应用领域事件"""
        self._events.append(event)
        self._version += 1

    def get_uncommitted_events(self) -> List[DomainEvent]:
        """获取未提交的事件"""
        return self._events.copy()

    def clear_events(self) -> None:
        """清空事件队列（通常在持久化后调用）"""
        self._events.clear()


class ValueObject(ABC):
    """
    值对象基类

    值对象的特征：
    - 不可变性
    - 通过属性值而非标识判断相等
    - 生命周期依附于实体
    """

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))


class DomainService(ABC):
    """
    领域服务基类

    领域服务用于封装：
    - 跨聚合的业务逻辑
    - 不适合放在实体/值对象中的业务规则
    - 需要多个领域对象协作的操作
    """

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行领域服务"""


class Repository(Generic[T], ABC):
    """
    仓储基类

    仓储负责：
    - 聚合的持久化和检索
    - 封装数据访问细节
    - 提供领域对象的集合视图
    """

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[T]:
        """根据ID获取聚合"""

    @abstractmethod
    def save(self, aggregate: T) -> None:
        """保存聚合"""

    @abstractmethod
    def delete(self, id: str) -> None:
        """删除聚合"""


class Specification(ABC):
    """
    规约模式基类

    用于封装业务规则，支持组合和复用
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        """判断是否满足规约"""

    def and_(self, other: "Specification") -> "AndSpecification":
        """与组合"""
        return AndSpecification(self, other)

    def or_(self, other: "Specification") -> "OrSpecification":
        """或组合"""
        return OrSpecification(self, other)

    def not_(self) -> "NotSpecification":
        """非"""
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)


class OrSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)


class NotSpecification(Specification):
    def __init__(self, spec: Specification):
        self.spec = spec

    def is_satisfied_by(self, candidate: Any) -> bool:
        return not self.spec.is_satisfied_by(candidate)


# 导出各业务域（通过子模块命名空间访问）
from . import approval, funding, project, village  # noqa: E402

# 导入事件处理器（自动注册）

__all__ = [
    "DomainEvent",
    "AggregateRoot",
    "ValueObject",
    "DomainService",
    "Repository",
    "Specification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    "funding",
    "project",
    "village",
    "approval",
]
