"""app.models.message 覆盖率攻坚测试

直接实例化 Message，覆盖 is_system / is_approval / is_task 三个类型属性。
"""

from app.models.message import Message, MessageType


def _msg(message_type):
    return Message(user_id=1, message_type=message_type, title="标题", content="内容")


class TestTypeProperties:
    def test_system_message(self):
        msg = _msg(MessageType.SYSTEM.value)
        assert msg.is_system is True
        assert msg.is_approval is False
        assert msg.is_task is False

    def test_approval_message(self):
        msg = _msg(MessageType.APPROVAL.value)
        assert msg.is_system is False
        assert msg.is_approval is True
        assert msg.is_task is False

    def test_task_message(self):
        msg = _msg(MessageType.TASK.value)
        assert msg.is_system is False
        assert msg.is_approval is False
        assert msg.is_task is True

    def test_repr_truncates_title(self):
        msg = _msg("system")
        assert repr(msg) == "<Message(id=None, type='system', title='标题...')>"
