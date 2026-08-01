"""app.services.user_service 覆盖率攻坚测试

补齐缺口：
- get_user_by_email 的 db 为 None 分支（49）
- create_user 全路径（84-98，含默认角色/缺省字段）
- update_user 找到用户后的更新路径（105-111，含 None 值跳过、未知属性跳过）

db 使用 MagicMock 链式查询；密码哈希使用真实 get_password_hash。
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.user_service import UserService


class TestGetUserByEmail:
    def test_db_none_returns_none(self):
        assert UserService(None).get_user_by_email("a@b.com") is None


class TestCreateUser:
    def test_create_user_persists_and_returns(self):
        db = MagicMock()
        svc = UserService(db)

        user = svc.create_user(
            {
                "username": "zhangsan",
                "email": "zs@example.com",
                "password": "secret123",
                "full_name": "张三",
                "role": "admin",
            }
        )

        assert user.username == "zhangsan"
        assert user.email == "zs@example.com"
        assert user.full_name == "张三"
        assert user.role == "admin"
        assert user.is_active is True
        # 真实哈希：不等于明文且非空
        assert user.hashed_password
        assert user.hashed_password != "secret123"
        db.add.assert_called_once_with(user)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(user)

    def test_create_user_defaults(self):
        db = MagicMock()
        svc = UserService(db)

        user = svc.create_user({"username": "u2", "password": "p"})

        assert user.role == "user"  # 默认角色（精简后为普通用户）
        assert user.email is None
        assert user.full_name is None
        db.add.assert_called_once_with(user)
        db.commit.assert_called_once()


class TestUpdateUser:
    def test_update_existing_user(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        user = SimpleNamespace(username="u1", full_name="旧名", email="old@x.com")
        q.first.return_value = user
        svc = UserService(db)

        updated = svc.update_user(1, {"full_name": "新名", "email": None, "ghost": "x"})

        assert updated is user
        assert updated.full_name == "新名"  # 有效字段被更新
        assert updated.email == "old@x.com"  # None 值被跳过
        assert not hasattr(updated, "ghost")  # 不存在的属性被跳过
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(user)
