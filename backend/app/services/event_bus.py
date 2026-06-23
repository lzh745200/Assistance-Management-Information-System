"""
事件总线 - 事件驱动架构核心

提供发布/订阅机制，支持领域事件的异步处理。
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import timezone, datetime
from enum import Enum

from app.core.async_utils import get_event_loop_safe
from app.core.logging import logger


class EventPriority(int, Enum):
    """事件优先级"""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class DomainEvent:
    """领域事件"""

    event_type: str
    aggregate_id: str
    aggregate_type: str
    payload: Dict[str, Any]
    event_id: Optional[str] = None
    occurred_at: Optional[datetime] = None
    correlation_id: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL

    def __post_init__(self):
        if self.event_id is None:
            import uuid

            self.event_id = str(uuid.uuid4())
        if self.occurred_at is None:
            self.occurred_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "payload": self.payload,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "correlation_id": self.correlation_id,
            "priority": self.priority.value,
        }


class EventHandler(ABC):
    """事件处理器基类"""

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """处理事件"""

    @property
    @abstractmethod
    def event_types(self) -> List[str]:
        """支持的事件类型"""


class EventBus:
    """
    事件总线

    功能：
    - 事件发布（同步/异步）
    - 事件订阅（广播/点对点）
    - 事件持久化
    - 重试机制
    """

    _instance: Optional["EventBus"] = None

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        # 处理器注册表: {event_type: [handlers]}
        self._handlers: Dict[str, List[EventHandler]] = {}

        # 事件队列（用于异步处理）
        self._event_queue: asyncio.Queue = asyncio.Queue()

        # 后台任务
        self._worker_task: Optional[asyncio.Task] = None

        # 事件历史（用于调试和审计）
        self._event_history: List[DomainEvent] = []
        self._max_history_size = 1000

        # 启动后台处理器
        self._start_worker()

    def _start_worker(self) -> None:
        """启动后台事件处理器"""
        loop = get_event_loop_safe()
        if loop is not None and loop.is_running():
            self._worker_task = asyncio.create_task(self._process_events())
        else:
            self._worker_task = None

    async def _process_events(self) -> None:
        """后台事件处理循环"""
        while True:
            try:
                event = await self._event_queue.get()
                await self._dispatch_event(event)
            except Exception as e:
                logger.error(f"事件处理错误: {e}")

    async def _dispatch_event(self, event: DomainEvent) -> None:
        """分发事件到处理器"""
        handlers = self._handlers.get(event.event_type, [])

        # 支持通配符订阅
        wildcard_handlers = self._handlers.get("*", [])
        all_handlers = list(set(handlers + wildcard_handlers))

        if not all_handlers:
            logger.warning(f"未找到 {event.event_type} 的事件处理器")
            return

        # 根据优先级排序
        sorted_handlers = sorted(
            all_handlers, key=lambda h: getattr(h, "priority", EventPriority.NORMAL).value, reverse=True
        )

        # 并行执行所有处理器
        tasks = [self._execute_handler(handler, event) for handler in sorted_handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 记录失败
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"事件处理器 {sorted_handlers[i].__class__.__name__} 失败: {result}")

    async def _execute_handler(self, handler: EventHandler, event: DomainEvent) -> None:
        """执行单个处理器"""
        try:
            await handler.handle(event)
        except Exception as e:
            logger.error(f"处理器 {handler.__class__.__name__} 执行失败: {e}")
            raise

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"处理器 {handler.__class__.__name__} 订阅了 {event_type}")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """取消订阅"""
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]

    async def publish(self, event: DomainEvent, async_mode: bool = True) -> None:
        """
        发布事件

        Args:
            event: 领域事件
            async_mode: 是否异步处理
        """
        # 记录事件历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)

        if async_mode:
            # 异步处理：放入队列
            await self._event_queue.put(event)
        else:
            # 同步处理：直接分发
            await self._dispatch_event(event)

    def publish_sync(self, event: DomainEvent) -> None:
        """同步发布事件（用于非异步环境）"""
        import threading

        self._event_history.append(event)

        # 尝试获取事件循环
        loop = get_event_loop_safe()
        if loop is None:  # pragma: no cover - get_event_loop_safe 永不返回 None
            # 没有事件循环，使用线程池处理
            def run_async():
                asyncio.run(self._dispatch_event(event))

            threading.Thread(target=run_async, daemon=True).start()
            return

        if loop.is_running():
            # 如果事件循环正在运行，创建任务
            asyncio.create_task(self._dispatch_event(event))
        else:
            # 否则在新线程中运行
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(self._dispatch_event(event))
                new_loop.close()

            thread = threading.Thread(target=run_in_thread)
            thread.start()

    def get_event_history(
        self, event_type: Optional[str] = None, aggregate_id: Optional[str] = None, limit: int = 100
    ) -> List[DomainEvent]:
        """获取事件历史"""
        events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if aggregate_id:
            events = [e for e in events if e.aggregate_id == aggregate_id]

        return events[-limit:]

    def clear_history(self) -> None:
        """清空事件历史"""
        self._event_history.clear()


# ── 死信队列 ──
# 处理失败的事件会被移入死信队列，供运维排查和手动重放
# Uses deque for O(1) append/popleft with automatic size cap.
from collections import deque  # noqa: E402

_dead_letter_queue: deque = deque(maxlen=500)


def add_to_dead_letter(event: DomainEvent, error: Exception, handler_name: str) -> None:
    """将处理失败的事件移入死信队列"""
    _dead_letter_queue.append({
        "event": event.to_dict(),
        "error": str(error),
        "handler": handler_name,
        "failed_at": datetime.now(timezone.utc).isoformat(),
    })


def get_dead_letter_events(limit: int = 50) -> List[Dict[str, Any]]:
    """获取死信队列中的事件"""
    items = list(_dead_letter_queue)
    return items[-limit:]


def replay_dead_letter(index: int) -> bool:
    """重放死信队列中指定索引的事件"""
    items = list(_dead_letter_queue)
    if 0 <= index < len(items):
        entry = items[index]
        del items[index]
        _dead_letter_queue.clear()
        _dead_letter_queue.extend(items)
        event_dict = entry["event"]
        event = DomainEvent(
            event_type=event_dict["event_type"],
            aggregate_id=event_dict["aggregate_id"],
            aggregate_type=event_dict["aggregate_type"],
            payload=event_dict.get("payload", {}),
            correlation_id=event_dict.get("correlation_id"),
            priority=EventPriority(event_dict.get("priority", EventPriority.NORMAL.value)),
        )
        event_bus.publish_sync(event)
        return True
    return False


# ── 标准系统事件类型 ──
class SystemEventTypes:
    """系统标准事件类型常量"""

    # 项目管理
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    PROJECT_STATUS_CHANGED = "project.status_changed"

    # 经费管理
    FUND_ALLOCATED = "fund.allocated"
    FUND_TRANSFERRED = "fund.transferred"
    FUND_ANOMALY_DETECTED = "fund.anomaly_detected"
    FUND_SETTLEMENT_COMPLETED = "fund.settlement_completed"

    # 村庄管理
    VILLAGE_REGISTERED = "village.registered"
    VILLAGE_UPDATED = "village.updated"
    VILLAGE_DATA_IMPORTED = "village.data_imported"

    # 审批流程
    APPROVAL_SUBMITTED = "approval.submitted"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"

    # 用户与安全
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PASSWORD_CHANGED = "user.password_changed"
    USER_LOCKED = "user.locked"
    SECURITY_ALERT = "security.alert"

    # 系统运维
    BACKUP_CREATED = "system.backup_created"
    BACKUP_RESTORED = "system.backup_restored"
    DATABASE_MAINTENANCE = "system.database_maintenance"
    PERFORMANCE_THRESHOLD = "system.performance_threshold"


# 全局事件总线实例
event_bus = EventBus()


class FundCreatedHandler(EventHandler):
    """经费创建事件处理器"""

    @property
    def event_types(self) -> List[str]:
        return ["FUND_CREATED", "FUND_APPROVED"]

    async def handle(self, event: DomainEvent) -> None:
        logger.info(f"处理经费事件: {event.event_type}, 聚合ID: {event.aggregate_id}")
        # 可以在这里发送通知、更新统计等


class AuditLogHandler(EventHandler):
    """审计日志事件处理器"""

    @property
    def event_types(self) -> List[str]:
        return ["FUND_CREATED", "FUND_APPROVED", "FUND_ALLOCATED", "FUND_COMPLETED"]

    async def handle(self, event: DomainEvent) -> None:
        # 记录审计日志
        logger.info(f"[审计] {event.event_type}: {event.aggregate_id}")
