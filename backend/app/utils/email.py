"""邮件发送工具模块"""

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_via_smtp(msg: EmailMessage) -> bool:
    """通过 SMTP 发送邮件（内部辅助函数）

    Args:
        msg: 已构建的邮件消息

    Returns:
        是否发送成功
    """
    if not settings.SMTP_HOST:
        return False

    try:
        port = settings.SMTP_PORT or 587

        with smtplib.SMTP(settings.SMTP_HOST, port, timeout=10) as smtp:
            smtp.ehlo()
            try:
                smtp.starttls()
            except smtplib.SMTPException as e:
                logger.warning(f"STARTTLS 失败，使用非加密连接: {str(e)}")

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            smtp.send_message(msg)

        return True

    except Exception as e:
        logger.error(f"SMTP 发送失败: {str(e)}")
        return False


def send_temp_password(to_email: str, temp_password: str) -> bool:
    """发送临时密码邮件

    Args:
        to_email: 收件人邮箱
        temp_password: 临时密码

    Returns:
        是否发送成功
    """
    if not settings.SMTP_HOST:
        logger.info(f"SMTP未配置，模拟发送邮件到({to_email})，临时密码已生成")
        return False

    subject = f"[{settings.APP_NAME}] 临时密码"
    body = f"您的临时密码是: {temp_password}\n请登录后立即修改密码。"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email
    msg.set_content(body)

    success = _send_via_smtp(msg)
    if success:
        logger.info(f"临时密码邮件已发送到: {to_email}")
    return success


def send_notification(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """发送通知邮件

    Args:
        to_email: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文
        html_body: HTML格式正文（可选）

    Returns:
        是否发送成功
    """
    if not settings.SMTP_HOST:
        logger.info(f"SMTP未配置，模拟发送通知邮件到: {to_email}")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email
    msg.set_content(body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    success = _send_via_smtp(msg)
    if success:
        logger.info(f"通知邮件已发送到: {to_email}")
    return success
