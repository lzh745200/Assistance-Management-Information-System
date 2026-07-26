"""b3 攻坚：覆盖 app.models.notification_preference 的各通知判断方法与默认配置"""
from app.models.notification_preference import NotificationPreference


def _make_pref(**overrides):
    pref = NotificationPreference(user_id=1)
    pref.email_approval = overrides.get("email_approval", True)
    pref.email_task = overrides.get("email_task", True)
    pref.email_system = overrides.get("email_system", False)
    pref.site_approval = overrides.get("site_approval", True)
    pref.site_task = overrides.get("site_task", True)
    pref.site_system = overrides.get("site_system", True)
    pref.push_approval = overrides.get("push_approval", True)
    pref.push_task = overrides.get("push_task", True)
    pref.push_system = overrides.get("push_system", True)
    return pref


class TestNotificationPreference:
    def test_repr(self):
        pref = _make_pref()
        pref.id = 7
        assert "user_id=1" in repr(pref)

    def test_should_send_email(self):
        pref = _make_pref()
        assert pref.should_send_email("approval") is True
        assert pref.should_send_email("task") is True
        assert pref.should_send_email("system") is False
        assert pref.should_send_email("unknown_type") is False

    def test_should_send_site_message(self):
        pref = _make_pref(site_task=False)
        assert pref.should_send_site_message("approval") is True
        assert pref.should_send_site_message("task") is False
        assert pref.should_send_site_message("system") is True
        # 未知类型默认发送
        assert pref.should_send_site_message("unknown_type") is True

    def test_should_push(self):
        pref = _make_pref(push_system=False)
        assert pref.should_push("approval") is True
        assert pref.should_push("task") is True
        assert pref.should_push("system") is False
        # 未知类型默认推送
        assert pref.should_push("unknown_type") is True

    def test_get_default_preferences(self):
        defaults = NotificationPreference.get_default_preferences()
        assert defaults["email_approval"] is True
        assert defaults["email_system"] is False
        assert defaults["site_system"] is True
        assert defaults["push_task"] is True
        assert len(defaults) == 9
