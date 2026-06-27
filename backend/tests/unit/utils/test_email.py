"""
邮件发送工具测试

测试 app/utils/email.py 模块
"""
import pytest
from unittest.mock import patch, MagicMock
from app.utils.email import (
    send_temp_password,
    send_notification,
    _send_via_smtp,
)


class TestSendViaSmtp:
    @patch("app.utils.email.settings")
    def test_no_smtp_host(self, mock_settings):
        mock_settings.SMTP_HOST = ""
        msg = MagicMock()
        result = _send_via_smtp(msg)
        assert result is False

    @patch("app.utils.email.settings")
    @patch("app.utils.email.smtplib.SMTP")
    def test_smtp_success(self, mock_smtp, mock_settings):
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_PASSWORD = "pass"
        mock_settings.SMTP_FROM = "noreply@test.com"
        msg = MagicMock()
        result = _send_via_smtp(msg)
        assert result is True

    @patch("app.utils.email.settings")
    @patch("app.utils.email.smtplib.SMTP")
    def test_smtp_exception(self, mock_smtp, mock_settings):
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_smtp.side_effect = Exception("Connection failed")
        msg = MagicMock()
        result = _send_via_smtp(msg)
        assert result is False

    @patch("app.utils.email.settings")
    @patch("app.utils.email.smtplib.SMTP")
    def test_starttls_failure_fallback(self, mock_smtp_cls, mock_settings):
        import smtplib
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_PASSWORD = "pass"
        mock_instance = MagicMock()
        mock_instance.starttls.side_effect = smtplib.SMTPException("TLS failed")
        mock_smtp_cls.return_value.__enter__.return_value = mock_instance
        msg = MagicMock()
        result = _send_via_smtp(msg)
        assert result is True


class TestSendTempPassword:
    @patch("app.utils.email.settings")
    def test_smtp_not_configured(self, mock_settings):
        mock_settings.SMTP_HOST = ""
        mock_settings.APP_NAME = "TestApp"
        result = send_temp_password("user@test.com", "temp123")
        assert result is False

    @patch("app.utils.email._send_via_smtp")
    @patch("app.utils.email.settings")
    def test_send_success(self, mock_settings, mock_send):
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_FROM = "noreply@test.com"
        mock_settings.APP_NAME = "TestApp"
        mock_send.return_value = True
        result = send_temp_password("user@test.com", "temp123")
        assert result is True
        mock_send.assert_called_once()


class TestSendNotification:
    @patch("app.utils.email.settings")
    def test_smtp_not_configured(self, mock_settings):
        mock_settings.SMTP_HOST = ""
        result = send_notification("user@test.com", "Subject", "Body")
        assert result is False

    @patch("app.utils.email._send_via_smtp")
    @patch("app.utils.email.settings")
    def test_send_success(self, mock_settings, mock_send):
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_FROM = "noreply@test.com"
        mock_send.return_value = True
        result = send_notification("user@test.com", "Subject", "Body")
        assert result is True
        mock_send.assert_called_once()

    @patch("app.utils.email._send_via_smtp")
    @patch("app.utils.email.settings")
    def test_send_with_html(self, mock_settings, mock_send):
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_FROM = "noreply@test.com"
        mock_send.return_value = True
        result = send_notification("user@test.com", "Subject", "Body", html_body="<h1>HTML</h1>")
        assert result is True
        mock_send.assert_called_once()
