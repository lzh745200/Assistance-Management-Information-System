"""
审批超时提醒服务

使用后台线程定期检查超时审批，生成提醒消息。
单机版替代Celery的方案——使用diskcache或内置threading。

在 main.py lifespan 中调用:
    reminder = start_approval_reminder(check_interval_minutes=30)
    # shutdown时:
    stop_approval_reminder(reminder)
"""

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CHECK_INTERVAL_MINUTES = 30
DEFAULT_DEADLINE_HOURS = 48
DEFAULT_WARNING_HOURS = 36  # 提前12小时警告


class ApprovalReminderService:
    """审批超时提醒服务 —— 后台线程定期扫描超时审批"""

    def __init__(self, check_interval_minutes: int = DEFAULT_CHECK_INTERVAL_MINUTES):
        self._check_interval = check_interval_minutes * 60  # 转换为秒
        self._deadline_hours = DEFAULT_DEADLINE_HOURS
        self._warning_hours = DEFAULT_WARNING_HOURS
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

    def start(self):
        """启动后台提醒线程"""
        if self._running:
            logger.warning("审批提醒服务已在运行中")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._scan_loop,
            daemon=True,
            name="approval-reminder",
        )
        self._thread.start()
        self._running = True
        logger.info(f"审批提醒服务已启动，检查间隔: {self._check_interval // 60}分钟")

    def stop(self):
        """停止后台提醒线程"""
        if not self._running:
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        self._running = False
        logger.info("审批提醒服务已停止")

    def _scan_loop(self):
        """后台扫描循环"""
        # 首次启动等待30秒，确保数据库已初始化（stop 时立即唤醒）
        if self._stop_event.wait(30):
            return

        while not self._stop_event.is_set():
            try:
                self._check_overdue_approvals()
            except Exception as e:
                logger.error(f"审批超时检查失败: {e}", exc_info=True)

            # 等待下一次检查（响应停止信号）
            self._stop_event.wait(self._check_interval)

    def _check_overdue_approvals(self):
        """检查超时和即将超时的审批"""
        from app.core.database import SessionLocal
        from app.models.approval import ApprovalTask, ApprovalStatus

        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            deadline = now - timedelta(hours=self._deadline_hours)
            warning_time = now - timedelta(hours=self._warning_hours)

            # 查询超过48小时未处理的审批（status 在 ApprovalTask 上）
            overdue = (
                db.query(ApprovalTask)
                .filter(
                    ApprovalTask.status == ApprovalStatus.PENDING.value,
                    ApprovalTask.created_at <= deadline,
                )
                .all()
            )

            # 查询超过36小时未处理的审批（预警）
            approaching = (
                db.query(ApprovalTask)
                .filter(
                    ApprovalTask.status == ApprovalStatus.PENDING.value,
                    ApprovalTask.created_at <= warning_time,
                    ApprovalTask.created_at > deadline,
                )
                .all()
            )

            # 为超时审批创建提醒消息
            for task in overdue:
                self._create_reminder_message(db, task, "overdue")

            # 为即将超时审批创建预警消息
            for task in approaching:
                self._create_reminder_message(db, task, "approaching")

            if overdue or approaching:
                logger.info(
                    f"审批提醒扫描完成: {len(overdue)}条超时, {len(approaching)}条预警"
                )
                db.commit()

        finally:
            db.close()

    def _create_reminder_message(self, db, approval_task, level: str):
        """创建提醒消息（幂等——同一审批任务+同一提醒级别不重复创建）"""
        from app.models.message import Message

        # 检查是否已发送过同类提醒（通过 link 字段标识关联实体）
        ref_link = f"/approval/tasks/{approval_task.id}"
        existing = (
            db.query(Message)
            .filter(
                Message.link == ref_link,
                Message.message_type == f"approval_{level}",
            )
            .first()
        )
        if existing:
            return

        if level == "overdue":
            title = f"审批超时提醒 - #{approval_task.id}"
            content = f"审批任务 #{approval_task.id}（{approval_task.title or '无标题'}）已超过48小时未处理，请尽快审批。"
        else:
            title = f"审批预警提醒 - #{approval_task.id}"
            content = f"审批任务 #{approval_task.id}（{approval_task.title or '无标题'}）已超过36小时未处理，请及时审批以免超时。"

        message = Message(
            user_id=approval_task.current_approver_id,
            title=title,
            content=content,
            message_type=f"approval_{level}",
            link=ref_link,
            is_read=False,
        )
        db.add(message)
        logger.info(f"审批提醒已创建: {title}")


# ══════════════════════════════════════════════════════════════
#  全局实例管理
# ══════════════════════════════════════════════════════════════

_reminder_service: Optional[ApprovalReminderService] = None


def start_approval_reminder(check_interval_minutes: int = DEFAULT_CHECK_INTERVAL_MINUTES) -> ApprovalReminderService:
    """启动审批提醒服务（在main.py lifespan中调用）"""
    global _reminder_service
    if _reminder_service is not None:
        logger.warning("审批提醒服务全局实例已存在，返回现有实例")
        return _reminder_service
    _reminder_service = ApprovalReminderService(check_interval_minutes)
    _reminder_service.start()
    return _reminder_service


def stop_approval_reminder(service: Optional[ApprovalReminderService] = None):
    """停止审批提醒服务（在main.py lifespan shutdown中调用）"""
    global _reminder_service
    target = service or _reminder_service
    if target:
        target.stop()
        if target is _reminder_service:
            _reminder_service = None
