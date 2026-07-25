# -*- coding: utf-8 -*-
"""User 模型属性覆盖率测试：permissions_list/organization_name/allowed_*"""

from app.models.user import User


def test_permissions_list_nonempty():
    u = User(username="u1", permissions=" village:read , project:write ,")
    assert u.permissions_list == ["village:read", "project:write"]


def test_permissions_list_empty():
    assert User(username="u2", permissions="").permissions_list == []


def test_organization_name_present():
    class _Org:
        name = "某单位"

    u = User(username="u3")
    u.organization = _Org()
    assert u.organization_name == "某单位"


def test_organization_name_absent():
    assert User(username="u4").organization_name == ""


def test_allowed_permissions_list_valid_json():
    u = User(username="u5", allowed_permissions='["a","b"]')
    assert u.allowed_permissions_list == ["a", "b"]


def test_allowed_permissions_list_invalid_json():
    assert User(username="u6", allowed_permissions="not-json").allowed_permissions_list == []


def test_allowed_permissions_list_type_error():
    u = User(username="u7")
    u.allowed_permissions = 123  # 非字符串 → TypeError → []
    assert u.allowed_permissions_list == []


def test_allowed_permissions_list_empty():
    assert User(username="u8", allowed_permissions="").allowed_permissions_list == []


def test_allowed_menus_list_none_inherits():
    assert User(username="u9", allowed_menus=None).allowed_menus_list is None


def test_allowed_menus_list_valid_json():
    u = User(username="u10", allowed_menus='["dashboard","villages"]')
    assert u.allowed_menus_list == ["dashboard", "villages"]


def test_allowed_menus_list_invalid_json_returns_none():
    assert User(username="u11", allowed_menus="{bad").allowed_menus_list is None


def test_allowed_menus_list_type_error_returns_none():
    u = User(username="u12")
    u.allowed_menus = 456
    assert u.allowed_menus_list is None


def test_token_version_safe_and_revoke():
    u = User(username="u13", token_version=None)
    assert u.token_version_safe == 0
    u.revoke_all_tokens()
    assert u.token_version == 1
    assert u.password_changed_at is not None
    u.revoke_all_tokens()
    assert u.token_version == 2
