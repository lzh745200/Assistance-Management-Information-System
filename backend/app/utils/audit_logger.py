"""
审计日志工具

用于记录关键业务操作的审计日志，包括：
- 用户操作（登录、登出、权限变更）
- 数据修改（创建、更新、删除）
- 敏感操作（导出、备份、配置变更）
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """审计操作类型"""

    # 认证相关
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"

    # 数据操作
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH_DELETE = "batch_delete"

    # 敏感操作
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"
    CONFIG_CHANGE = "config_change"

    # 权限操作
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_CHANGE = "role_change"


class AuditLevel(str, Enum):
    """审计级别"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AuditLogger:
    """审计日志记录器"""

    @staticmethod
    def log(
        action: AuditAction,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        记录审计日志

        Args:
            action: 操作类型
            user_id: 用户ID
            username: 用户名
            resource_type: 资源类型（如 "project", "fund", "village"）
            resource_id: 资源ID
            details: 详细信息（字典格式）
            level: 审计级别
            ip_address: IP地址
            user_agent: 用户代理
        """
        audit_data = {
            "timestamp": datetime.now().isoformat(),
            "action": action.value,
            "user_id": user_id,
            "username": username,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "level": level.value,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        # 根据级别选择日志方法
        log_message = f"[AUDIT] {json.dumps(audit_data, ensure_ascii=False)}"

        if level == AuditLevel.CRITICAL:
            logger.critical(log_message)
        elif level == AuditLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    @staticmethod
    def log_login(
        user_id: int,
        username: str,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> None:
        """记录登录操作"""
        action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        details = {"success": success}
        if failure_reason:
            details["failure_reason"] = failure_reason

        AuditLogger.log(
            action=action,
            user_id=user_id,
            username=username,
            details=details,
            level=level,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_data_change(
        action: AuditAction,
        user_id: int,
        username: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """记录数据变更操作"""
        details = {}
        if old_data:
            details["old_data"] = old_data
        if new_data:
            details["new_data"] = new_data

        AuditLogger.log(
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            level=AuditLevel.INFO,
            ip_address=ip_address,
        )

    @staticmethod
    def log_sensitive_operation(
        action: AuditAction,
        user_id: int,
        username: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """记录敏感操作"""
        AuditLogger.log(
            action=action,
            user_id=user_id,
            username=username,
            details=details,
            level=AuditLevel.CRITICAL,
            ip_address=ip_address,
        )

    @staticmethod
    def log_permission_change(
        action: AuditAction,
        operator_id: int,
        operator_name: str,
        target_user_id: int,
        target_username: str,
        permission_details: Dict[str, Any],
        ip_address: Optional[str] = None,
    ) -> None:
        """记录权限变更操作"""
        details = {
            "target_user_id": target_user_id,
            "target_username": target_username,
            **permission_details,
        }

        AuditLogger.log(
            action=action,
            user_id=operator_id,
            username=operator_name,
            resource_type="user_permission",
            resource_id=target_user_id,
            details=details,
            level=AuditLevel.CRITICAL,
            ip_address=ip_address,
        )


# 便捷函数
def log_audit(
    action: AuditAction,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    **kwargs,
) -> None:
    """便捷的审计日志记录函数"""
    AuditLogger.log(action=action, user_id=user_id, username=username, **kwargs)
