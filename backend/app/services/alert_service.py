"""
告警服务
提供多渠道告警功能(邮件、Webhook)
"""

import logging
import smtplib
from datetime import timezone, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertService:
    """告警服务"""

    @staticmethod
    async def send_email_alert(recipients: List[str], subject: str, message: str) -> bool:
        """
        发送邮件告警

        Args:
            recipients: 收件人列表
            subject: 邮件主题
            message: 邮件内容

        Returns:
            是否发送成功
        """
        try:
            # 获取SMTP配置
            smtp_host = getattr(settings, "SMTP_HOST", None)
            smtp_port = getattr(settings, "SMTP_PORT", 587)
            smtp_user = getattr(settings, "SMTP_USER", None)
            smtp_password = getattr(settings, "SMTP_PASSWORD", None)
            smtp_from = getattr(settings, "SMTP_FROM", smtp_user)

            if not all([smtp_host, smtp_user, smtp_password]):
                logger.warning("SMTP配置不完整,跳过邮件发送")
                return False

            # 创建邮件
            msg = MIMEMultipart()
            msg["From"] = smtp_from
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject

            msg.attach(MIMEText(message, "plain", "utf-8"))

            # 发送邮件
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info(f"邮件告警已发送: {subject}")
            return True

        except Exception as e:
            logger.error(f"发送邮件告警失败: {e}")
            return False

    @staticmethod
    async def send_webhook_alert(webhook_url: str, message: str, webhook_type: str = "generic") -> bool:
        """
        发送Webhook告警

        Args:
            webhook_url: Webhook URL
            message: 告警消息
            webhook_type: Webhook类型(generic/dingtalk/wecom)

        Returns:
            是否发送成功
        """
        try:
            # 根据类型构造不同的消息格式
            if webhook_type == "dingtalk":
                payload = {
                    "msgtype": "text",
                    "text": {"content": f"【系统告警】\n{message}"},
                }
            elif webhook_type == "wecom":
                payload = {
                    "msgtype": "text",
                    "text": {"content": f"【系统告警】\n{message}"},
                }
            else:
                payload = {
                    "message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            # 发送HTTP请求
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=10.0)
                response.raise_for_status()

            logger.info(f"Webhook告警已发送: {webhook_url}")
            return True

        except Exception as e:
            logger.error(f"发送Webhook告警失败: {e}")
            return False
