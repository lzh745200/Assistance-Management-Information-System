"""Tests for app.core.user_info — 100% coverage."""

import pytest
from app.core.user_info import UserInfo


class TestUserInfo:
    def test_attribute_access(self):
        u = UserInfo(id=1, username="admin", role="admin")
        assert u.id == 1
        assert u.username == "admin"
        assert u.role == "admin"

    def test_get_method(self):
        u = UserInfo(name="test")
        assert u.get("name") == "test"
        assert u.get("missing") is None
        assert u.get("missing", "default") == "default"

    def test_getitem(self):
        u = UserInfo(id=1, email="a@b.com")
        assert u["id"] == 1
        assert u["email"] == "a@b.com"

    def test_getitem_key_error(self):
        u = UserInfo(id=1)
        with pytest.raises(KeyError):
            _ = u["nonexistent"]

    def test_setitem(self):
        u = UserInfo(id=1)
        u["name"] = "new_name"
        assert u.name == "new_name"
        assert u["name"] == "new_name"

    def test_contains(self):
        u = UserInfo(id=1)
        assert "id" in u
        assert "nonexistent" not in u

    def test_repr(self):
        u = UserInfo(id=1, username="admin")
        r = repr(u)
        assert "UserInfo" in r
        assert "id=1" in r
        assert "username='admin'" in r

    def test_keys(self):
        u = UserInfo(a=1, b=2)
        assert set(u.keys()) == {"a", "b"}

    def test_values(self):
        u = UserInfo(a=1, b=2)
        assert set(u.values()) == {1, 2}

    def test_items(self):
        u = UserInfo(a=1)
        assert dict(u.items()) == {"a": 1}

    def test_empty_user(self):
        u = UserInfo()
        assert u.get("anything", "default") == "default"
        assert list(u.keys()) == []
