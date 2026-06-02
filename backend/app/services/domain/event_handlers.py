"""
事件处理器集成

集成所有领域事件处理器到事件总线。
"""

from typing import List
from datetime import timezone, datetime

from app.core.logging import logger
from app.services.event_bus import EventHandler, event_bus, DomainEvent


class FundEventHandler(EventHandler):
    """经费事件处理器"""

    @property
    def event_types(self) -> List[str]:
        return ["FUND_SUBMITTED", "FUND_APPROVED", "BUDGET_ALLOCATED", "FUND_FROZEN", "FUND_COMPLETED"]

    async def handle(self, event: DomainEvent) -> None:
        """处理经费事件"""
        logger.info(f"[领域事件] 经费: {event.event_type}, ID: {event.aggregate_id}")

        # 根据事件类型执行不同逻辑
        handlers = {
            "FUND_SUBMITTED": self._on_submitted,
            "FUND_APPROVED": self._on_approved,
            "BUDGET_ALLOCATED": self._on_allocated,
            "FUND_FROZEN": self._on_frozen,
            "FUND_COMPLETED": self._on_completed,
        }

        handler = handlers.get(event.event_type)
        if handler:
            await handler(event)

    async def _on_submitted(self, event: DomainEvent) -> None:
        """经费提交后：触发审批流程"""
        logger.info(f"经费 {event.aggregate_id} 已提交，等待审批")

    async def _on_approved(self, event: DomainEvent) -> None:
        """经费批准后：通知相关方"""
        approver_id = event.payload.get("approver_id")
        logger.info(f"经费 {event.aggregate_id} 已由 {approver_id} 批准")

    async def _on_allocated(self, event: DomainEvent) -> None:
        """预算分配后：记录分配明细"""
        category = event.payload.get("category")
        amount = event.payload.get("amount")
        logger.info(f"经费 {event.aggregate_id} 分配: {category} = {amount}")

    async def _on_frozen(self, event: DomainEvent) -> None:
        """经费冻结后：记录原因"""
        reason = event.payload.get("reason")
        logger.info(f"经费 {event.aggregate_id} 已冻结，原因: {reason}")

    async def _on_completed(self, event: DomainEvent) -> None:
        """经费完成后：生成总结报告"""
        logger.info(f"经费 {event.aggregate_id} 已完成使用")


class ProjectEventHandler(EventHandler):
    """项目事件处理器"""

    @property
    def event_types(self) -> List[str]:
        return [
            "PROJECT_SUBMITTED",
            "PROJECT_APPROVED",
            "PROJECT_STARTED",
            "PROJECT_PAUSED",
            "PROJECT_RESUMED",
            "PROJECT_COMPLETED",
            "MILESTONE_COMPLETED",
        ]

    async def handle(self, event: DomainEvent) -> None:
        """处理项目事件"""
        logger.info(f"[领域事件] 项目: {event.event_type}, ID: {event.aggregate_id}")

        # 里程碑完成时通知
        if event.event_type == "MILESTONE_COMPLETED":
            milestone_name = event.payload.get("milestone_name")
            logger.info(f"项目 {event.aggregate_id} 里程碑完成: {milestone_name}")

        # 项目完成时生成报告
        if event.event_type == "PROJECT_COMPLETED":
            logger.info(f"项目 {event.aggregate_id} 已完成，生成结项报告")


class VillageEventHandler(EventHandler):
    """帮扶村事件处理器"""

    @property
    def event_types(self) -> List[str]:
        return [
            "VILLAGE_ACTIVATED",
            "VILLAGE_COMPLETED",
            "VILLAGE_SUSPENDED",
            "VILLAGE_RESUMED",
            "SUPPORT_TARGET_ADDED",
            "DEMOGRAPHICS_UPDATED",
        ]

    async def handle(self, event: DomainEvent) -> None:
        """处理帮扶村事件"""
        logger.info(f"[领域事件] 帮扶村: {event.event_type}, ID: {event.aggregate_id}")

        if event.event_type == "VILLAGE_COMPLETED":
            logger.info(f"帮扶村 {event.aggregate_id} 已完成帮扶退出")

        if event.event_type == "DEMOGRAPHICS_UPDATED":
            population = event.payload.get("population")
            poverty_pop = event.payload.get("poverty_population")
            logger.info(f"帮扶村 {event.aggregate_id} 人口更新: 总人口 {population}, 贫困 {poverty_pop}")


class ApprovalEventHandler(EventHandler):
    """审批事件处理器"""

    @property
    def event_types(self) -> List[str]:
        return [
            "APPROVAL_SUBMITTED",
            "APPROVAL_STEP_STARTED",
            "APPROVAL_STEP_COMPLETED",
            "APPROVAL_COMPLETED",
            "APPROVAL_REJECTED",
            "APPROVAL_RETURNED",
            "APPROVAL_CANCELLED",
        ]

    async def handle(self, event: DomainEvent) -> None:
        """处理审批事件"""
        logger.info(f"[领域事件] 审批: {event.event_type}, ID: {event.aggregate_id}")

        if event.event_type == "APPROVAL_COMPLETED":
            target_id = event.payload.get("target_id")
            target_type = event.payload.get("target_type")
            logger.info(f"审批完成，批准 {target_type}: {target_id}")
            # 触发后续业务操作
            await self._trigger_post_approval(target_type, target_id)

        if event.event_type == "APPROVAL_REJECTED":
            reason = event.payload.get("reason")
            logger.info(f"审批被拒绝，原因: {reason}")

    async def _trigger_post_approval(self, target_type: str, target_id: str) -> None:
        """审批通过后触发后续操作"""
        logger.info(f"触发 {target_type} {target_id} 的批准后操作")


class AuditLogHandler(EventHandler):
    """审计日志事件处理器 - 记录所有领域事件"""

    @property
    def event_types(self) -> List[str]:
        """监听所有事件"""
        return ["*"]

    async def handle(self, event: DomainEvent) -> None:
        """记录审计日志"""
        logger.info(
            f"[审计] {event.occurred_at.isoformat()} | "
            f"{event.aggregate_type}:{event.aggregate_id} | "
            f"{event.event_type}"
        )


class NotificationHandler(EventHandler):
    """通知事件处理器 - 发送系统通知"""

    @property
    def event_types(self) -> List[str]:
        return [
            "FUND_APPROVED",
            "PROJECT_APPROVED",
            "APPROVAL_SUBMITTED",
            "APPROVAL_REJECTED",
            "APPROVAL_COMPLETED",
            "VILLAGE_SUSPENDED",
        ]

    async def handle(self, event: DomainEvent) -> None:
        """发送通知"""
        # 这里可以集成消息推送服务
        notifications = {
            "FUND_APPROVED": "您的经费申请已获批准",
            "PROJECT_APPROVED": "您的项目申报已获批准",
            "APPROVAL_SUBMITTED": "有新的审批需要处理",
            "APPROVAL_REJECTED": "您的申请已被拒绝",
            "APPROVAL_COMPLETED": "审批流程已完成",
            "VILLAGE_SUSPENDED": "帮扶村帮扶已暂停",
        }

        message = notifications.get(event.event_type)
        if message:
            logger.info(f"[通知] {message} - {event.aggregate_id}")


class MetricsHandler(EventHandler):
    """指标收集处理器 - 收集业务指标"""

    def __init__(self):
        self._metrics_cache = {}

    @property
    def event_types(self) -> List[str]:
        return [
            "FUND_APPROVED",
            "FUND_COMPLETED",
            "PROJECT_COMPLETED",
            "APPROVAL_COMPLETED",
            "APPROVAL_REJECTED",
            "VILLAGE_COMPLETED",
        ]

    async def handle(self, event: DomainEvent) -> None:
        """收集业务指标"""
        metric_type = event.event_type.lower()

        if metric_type not in self._metrics_cache:
            self._metrics_cache[metric_type] = {"count": 0, "last_at": None}

        self._metrics_cache[metric_type]["count"] += 1
        self._metrics_cache[metric_type]["last_at"] = datetime.now(timezone.utc).isoformat()

        logger.debug(f"[指标] {metric_type}: {self._metrics_cache[metric_type]['count']}")

    def get_metrics(self) -> dict:
        """获取收集的指标"""
        return self._metrics_cache.copy()


# 全局处理器实例
fund_handler = FundEventHandler()
project_handler = ProjectEventHandler()
village_handler = VillageEventHandler()
approval_handler = ApprovalEventHandler()
audit_handler = AuditLogHandler()
notification_handler = NotificationHandler()
metrics_handler = MetricsHandler()


def register_all_handlers():
    """注册所有事件处理器到事件总线"""
    # 经费事件
    for event_type in fund_handler.event_types:
        event_bus.subscribe(event_type, fund_handler)

    # 项目事件
    for event_type in project_handler.event_types:
        event_bus.subscribe(event_type, project_handler)

    # 帮扶村事件
    for event_type in village_handler.event_types:
        event_bus.subscribe(event_type, village_handler)

    # 审批事件
    for event_type in approval_handler.event_types:
        event_bus.subscribe(event_type, approval_handler)

    # 审计日志（监听所有事件）
    if "*" in audit_handler.event_types:
        # 订阅所有已知事件类型
        all_events = (
            fund_handler.event_types
            + project_handler.event_types
            + village_handler.event_types
            + approval_handler.event_types
        )
        for event_type in set(all_events):
            event_bus.subscribe(event_type, audit_handler)

    # 通知
    for event_type in notification_handler.event_types:
        event_bus.subscribe(event_type, notification_handler)

    # 指标收集
    for event_type in metrics_handler.event_types:
        event_bus.subscribe(event_type, metrics_handler)

    logger.info("所有领域事件处理器已注册")


# 自动注册（导入时执行）
register_all_handlers()
