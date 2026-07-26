"""补齐 app.services.message_service 覆盖率缺口（70-90 行：send_message 类型校验与落库）."""
import pytest
from unittest.mock import MagicMock

from app.services.message_service import MessageService


class TestSendMessage:
    def test_invalid_type_raises_value_error(self):
        svc = MessageService(MagicMock())
        with pytest.raises(ValueError, match="无效的消息类型"):
            svc.send_message(1, "bogus", "标题", "内容")

    def test_valid_type_persists_message(self):
        db = MagicMock()
        msg = MessageService(db).send_message(1, "system", "标题", "内容", "/link")
        db.add.assert_called_once_with(msg)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(msg)
        assert msg.user_id == 1
        assert msg.message_type == "system"
        assert msg.is_read is False
        assert msg.link == "/link"
