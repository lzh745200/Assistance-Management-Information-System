"""User model factory."""

from datetime import datetime, timezone

from app.models.user import User
from app.models.user_organization import UserOrganization
from app.core.security import hash_password


class UserFactory:
    DEFAULT_PASSWORD = "Test@123456"

    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            username="testuser",
            email="testuser@example.com",
            hashed_password=hash_password(UserFactory.DEFAULT_PASSWORD),
            full_name="测试用户",
            role="user",
            is_active=True,
            is_superuser=False,
            department="测试部",
            failed_login_count=0,
            locked_until=None,
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        if "password" in kwargs:
            data["hashed_password"] = hash_password(kwargs.pop("password"))
        return User(**data)

    @staticmethod
    def create(db, **kwargs):
        obj = UserFactory.build(**kwargs)
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def build_admin(**kwargs):
        kwargs.setdefault("username", "admin")
        kwargs.setdefault("full_name", "管理员")
        kwargs.setdefault("role", "admin")
        kwargs.setdefault("is_superuser", True)
        kwargs.setdefault("email", "admin@example.com")
        kwargs.setdefault("department", "系统管理部")
        return UserFactory.build(**kwargs)

    @staticmethod
    def build_operator(**kwargs):
        kwargs.setdefault("username", "operator")
        kwargs.setdefault("full_name", "操作员")
        kwargs.setdefault("role", "operator")
        return UserFactory.build(**kwargs)

    @staticmethod
    def build_viewer(**kwargs):
        kwargs.setdefault("username", "viewer")
        kwargs.setdefault("full_name", "查看者")
        kwargs.setdefault("role", "viewer")
        kwargs.setdefault("permissions", "view")
        return UserFactory.build(**kwargs)


class UserOrganizationFactory:
    @staticmethod
    def build(user_id=1, organization_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            user_id=user_id,
            organization_id=organization_id,
            created_at=now,
        )
        data.update(kwargs)
        return UserOrganization(**data)

    @staticmethod
    def create(db, user_id=1, organization_id=1, **kwargs):
        obj = UserOrganizationFactory.build(user_id=user_id, organization_id=organization_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj
