"""
通知偏好服务

任务 7.7: 实现通知偏好服务
- 用户通知偏好CRUD
- 根据偏好过滤通知发送

需求: 6.2
"""

from datetime import timezone, datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.notification_preference import NotificationPreference


class NotificationPreferenceService:
    """
    通知偏好服务类

    需求:
    - 6.2: 用户可配置接收哪些类型的通知
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== 获取偏好 ====================

    def get_preference(self, user_id: int) -> NotificationPreference:
        """
        获取用户通知偏好

        如果不存在则创建默认偏好

        参数:
            user_id: 用户ID

        返回:
            NotificationPreference: 通知偏好对象
        """
        preference = self.db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()

        if not preference:
            # 创建默认偏好
            preference = self._create_default_preference(user_id)

        return preference

    def _create_default_preference(self, user_id: int) -> NotificationPreference:
        """创建默认通知偏好"""
        preference = NotificationPreference(
            user_id=user_id,
            # 站内消息默认全部启用
            site_message_enabled=True,
            system_notification=True,
            approval_notification=True,
            task_notification=True,
            report_notification=True,
            # 邮件通知默认启用
            email_enabled=True,
            email_system=True,
            email_approval=True,
            email_task=True,
            email_report=False,  # 报表邮件默认关闭
            # 免打扰时段默认关闭
            quiet_hours_enabled=False,
            quiet_hours_start=None,
            quiet_hours_end=None,
        )

        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)

        return preference

    # ==================== 更新偏好 ====================

    def update_preference(self, user_id: int, **kwargs) -> NotificationPreference:
        """
        更新用户通知偏好

        参数:
            user_id: 用户ID
            **kwargs: 要更新的字段

        返回:
            NotificationPreference: 更新后的偏好对象
        """
        preference = self.get_preference(user_id)

        # 允许更新的字段
        allowed_fields = [
            "site_message_enabled",
            "system_notification",
            "approval_notification",
            "task_notification",
            "report_notification",
            "email_enabled",
            "email_system",
            "email_approval",
            "email_task",
            "email_report",
            "quiet_hours_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
        ]

        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(preference, field):
                setattr(preference, field, value)

        preference.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(preference)

        return preference

    def update_site_message_settings(
        self,
        user_id: int,
        enabled: bool = True,
        system: bool = True,
        approval: bool = True,
        task: bool = True,
        report: bool = True,
    ) -> NotificationPreference:
        """更新站内消息设置"""
        return self.update_preference(
            user_id,
            site_message_enabled=enabled,
            system_notification=system,
            approval_notification=approval,
            task_notification=task,
            report_notification=report,
        )

    def update_email_settings(
        self,
        user_id: int,
        enabled: bool = True,
        system: bool = True,
        approval: bool = True,
        task: bool = True,
        report: bool = False,
    ) -> NotificationPreference:
        """更新邮件通知设置"""
        return self.update_preference(
            user_id,
            email_enabled=enabled,
            email_system=system,
            email_approval=approval,
            email_task=task,
            email_report=report,
        )

    def update_quiet_hours(
        self,
        user_id: int,
        enabled: bool,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> NotificationPreference:
        """更新免打扰时段设置"""
        return self.update_preference(
            user_id,
            quiet_hours_enabled=enabled,
            quiet_hours_start=start_time,
            quiet_hours_end=end_time,
        )

    # ==================== 检查偏好 ====================

    def should_send_site_message(self, user_id: int, notification_type: str) -> bool:
        """
        检查是否应该发送站内消息

        参数:
            user_id: 用户ID
            notification_type: 通知类型 (system / approval / task / report)

        返回:
            bool: 是否应该发送
        """
        preference = self.get_preference(user_id)

        if not preference.site_message_enabled:
            return False

        # 检查免打扰时段
        if self._is_in_quiet_hours(preference):
            return False

        # 检查具体类型
        type_mapping = {
            "system": preference.system_notification,
            "approval": preference.approval_notification,
            "task": preference.task_notification,
            "report": preference.report_notification,
        }

        return type_mapping.get(notification_type, True)

    def should_send_email(self, user_id: int, notification_type: str) -> bool:
        """
        检查是否应该发送邮件

        参数:
            user_id: 用户ID
            notification_type: 通知类型 (system / approval / task / report)

        返回:
            bool: 是否应该发送
        """
        preference = self.get_preference(user_id)

        if not preference.email_enabled:
            return False

        # 检查具体类型
        type_mapping = {
            "system": preference.email_system,
            "approval": preference.email_approval,
            "task": preference.email_task,
            "report": preference.email_report,
        }

        return type_mapping.get(notification_type, True)

    def _is_in_quiet_hours(self, preference: NotificationPreference) -> bool:
        """检查当前是否在免打扰时段"""
        if not preference.quiet_hours_enabled:
            return False

        if not preference.quiet_hours_start or not preference.quiet_hours_end:
            return False

        now = datetime.now().time()

        try:
            start = datetime.strptime(preference.quiet_hours_start, "%H:%M").time()
            end = datetime.strptime(preference.quiet_hours_end, "%H:%M").time()

            # 处理跨午夜的情况
            if start <= end:
                return start <= now <= end
            else:
                return now >= start or now <= end
        except ValueError:
            return False

    # ==================== 批量操作 ====================

    def get_users_for_notification(self, user_ids: list, notification_type: str, channel: str = "site") -> list:
        """
        获取应该接收通知的用户列表

        参数:
            user_ids: 用户ID列表
            notification_type: 通知类型
            channel: 通知渠道 (site / email)

        返回:
            list: 应该接收通知的用户ID列表
        """
        result = []

        for user_id in user_ids:
            if channel == "site":
                if self.should_send_site_message(user_id, notification_type):
                    result.append(user_id)
            elif channel == "email":
                if self.should_send_email(user_id, notification_type):
                    result.append(user_id)

        return result

    # ==================== 转换为字典 ====================

    def preference_to_dict(self, preference: NotificationPreference) -> Dict[str, Any]:
        """将偏好对象转换为字典"""
        return {
            "user_id": preference.user_id,
            "site_message": {
                "enabled": preference.site_message_enabled,
                "system": preference.system_notification,
                "approval": preference.approval_notification,
                "task": preference.task_notification,
                "report": preference.report_notification,
            },
            "email": {
                "enabled": preference.email_enabled,
                "system": preference.email_system,
                "approval": preference.email_approval,
                "task": preference.email_task,
                "report": preference.email_report,
            },
            "quiet_hours": {
                "enabled": preference.quiet_hours_enabled,
                "start": preference.quiet_hours_start,
                "end": preference.quiet_hours_end,
            },
            "updated_at": (preference.updated_at.isoformat() if preference.updated_at else None),
        }
