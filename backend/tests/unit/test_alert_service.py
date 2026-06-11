"""告警服务单元测试 — 100% line/branch coverage"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, ANY


class TestSendEmailAlert:
    """覆盖 send_email_alert 所有分支"""

    @pytest.mark.asyncio
    async def test_success(self):
        """完整 SMTP 配置，邮件发送成功"""
        from app.services.alert_service import AlertService

        mock_server = MagicMock()
        mock_server.__enter__.return_value = mock_server
        with patch("app.services.alert_service.settings") as mock_st:
            mock_st.SMTP_HOST = "smtp.test.com"
            mock_st.SMTP_PORT = 587
            mock_st.SMTP_USER = "user@test.com"
            mock_st.SMTP_PASSWORD = "secret"
            mock_st.SMTP_FROM = "noreply@test.com"

            with patch("smtplib.SMTP", return_value=mock_server) as smtp_cls:
                result = await AlertService.send_email_alert(
                    ["a@b.com", "c@d.com"], "主题", "内容"
                )
                assert result is True
                smtp_cls.assert_called_once_with("smtp.test.com", 587)
                mock_server.starttls.assert_called_once()
                mock_server.login.assert_called_once_with("user@test.com", "secret")
                mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_smtp_from_none(self):
        """SMTP_FROM 为 None 时不影响发送"""
        from app.services.alert_service import AlertService

        mock_server = MagicMock()
        mock_server.__enter__.return_value = mock_server
        with patch("app.services.alert_service.settings") as mock_st:
            mock_st.SMTP_HOST = "smtp.test.com"
            mock_st.SMTP_PORT = 587
            mock_st.SMTP_USER = "user@test.com"
            mock_st.SMTP_PASSWORD = "secret"
            mock_st.SMTP_FROM = None

            with patch("smtplib.SMTP", return_value=mock_server):
                result = await AlertService.send_email_alert(
                    ["a@b.com"], "主题", "内容"
                )
                assert result is True
                mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_incomplete_config(self):
        """SMTP_HOST / USER / PASSWORD 任一缺失 → 警告并返回 False"""
        from app.services.alert_service import AlertService

        with patch("app.services.alert_service.settings") as mock_st:
            mock_st.SMTP_HOST = None
            mock_st.SMTP_USER = None
            mock_st.SMTP_PASSWORD = None
            mock_st.SMTP_PORT = 587
            mock_st.SMTP_FROM = None

            with patch("app.services.alert_service.logger") as mock_log:
                result = await AlertService.send_email_alert(
                    ["a@b.com"], "主题", "内容"
                )
                assert result is False
                mock_log.warning.assert_called_once_with(
                    "SMTP配置不完整,跳过邮件发送"
                )

    @pytest.mark.asyncio
    async def test_smtp_exception(self):
        """SMTP 调用抛出异常 → error 日志并返回 False"""
        from app.services.alert_service import AlertService

        with patch("app.services.alert_service.settings") as mock_st:
            mock_st.SMTP_HOST = "smtp.test.com"
            mock_st.SMTP_USER = "user"
            mock_st.SMTP_PASSWORD = "pass"
            mock_st.SMTP_PORT = 587
            mock_st.SMTP_FROM = "noreply@test.com"

            with patch("smtplib.SMTP", side_effect=Exception("conn refused")):
                with patch("app.services.alert_service.logger") as mock_log:
                    result = await AlertService.send_email_alert(
                        ["a@b.com"], "主题", "内容"
                    )
                    assert result is False
                    mock_log.error.assert_called_once()


class TestSendWebhookAlert:
    """覆盖 send_webhook_alert 所有分支"""

    @pytest.mark.asyncio
    async def test_generic_default(self):
        """webhook_type 为 'generic'（默认）"""
        from app.services.alert_service import AlertService

        mock_resp = MagicMock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_resp

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await AlertService.send_webhook_alert(
                "https://hook.example.com/hook", "告警消息"
            )
            assert result is True
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://hook.example.com/hook"
            assert call_args[1]["timeout"] == 10.0
            assert call_args[1]["json"]["message"] == "告警消息"
            assert "timestamp" in call_args[1]["json"]

    @pytest.mark.asyncio
    async def test_dingtalk(self):
        """webhook_type == 'dingtalk'"""
        from app.services.alert_service import AlertService

        mock_resp = MagicMock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_resp

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await AlertService.send_webhook_alert(
                "https://dingtalk/hook", "告警消息", webhook_type="dingtalk"
            )
            assert result is True
            payload = mock_client.post.call_args[1]["json"]
            assert payload["msgtype"] == "text"
            assert "【系统告警】" in payload["text"]["content"]

    @pytest.mark.asyncio
    async def test_wecom(self):
        """webhook_type == 'wecom'"""
        from app.services.alert_service import AlertService

        mock_resp = MagicMock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_resp

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await AlertService.send_webhook_alert(
                "https://wecom/hook", "告警消息", webhook_type="wecom"
            )
            assert result is True
            payload = mock_client.post.call_args[1]["json"]
            assert payload["msgtype"] == "text"
            assert "【系统告警】" in payload["text"]["content"]

    @pytest.mark.asyncio
    async def test_http_error_status(self):
        """HTTP 返回非 2xx → raise_for_status 触发异常"""
        from app.services.alert_service import AlertService

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("HTTP 500")

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_resp

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("app.services.alert_service.logger") as mock_log:
                result = await AlertService.send_webhook_alert(
                    "https://hook/hook", "消息"
                )
                assert result is False
                mock_log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_exception(self):
        """httpx 请求本身抛出异常"""
        from app.services.alert_service import AlertService

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.side_effect = Exception("timeout")

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("app.services.alert_service.logger") as mock_log:
                result = await AlertService.send_webhook_alert(
                    "https://hook/hook", "消息"
                )
                assert result is False
                mock_log.error.assert_called_once()
