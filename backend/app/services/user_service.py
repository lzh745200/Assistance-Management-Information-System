"""
用户服务

提供用户 CRUD、认证、查询等功能。
"""

import logging
from typing import List

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

VALID_ROLES = [
    "super_admin",
    "admin",
    "approval_leader",
    "manager",
    "operator",
    "viewer",
]


class UserService:
    """用户服务"""

    def __init__(self, db: Session = None):
        self.db = db

    def get_user_by_username(self, username: str):
        """通过用户名获取用户"""
        if self.db is None:
            return None
        from app.models.user import User

        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, user_id: int):
        """通过 ID 获取用户"""
        if self.db is None:
            return None
        from app.models.user import User

        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str):
        """通过邮箱获取用户"""
        if self.db is None:
            return None
        from app.models.user import User

        return self.db.query(User).filter(User.email == email).first()

    def get_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role: str = None,
        is_active: bool = None,
        search: str = None,
    ) -> List:
        """获取用户列表"""
        if self.db is None:
            return []
        from app.models.user import User

        query = self.db.query(User)
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if search:
            query = query.filter(
                (User.username.contains(search))
                | (User.full_name.contains(search))
                | (User.email.contains(search))
            )
        return query.offset(skip).limit(limit).all()

    def create_user(self, data: dict):
        """创建用户"""
        if self.db is None:
            return None
        from app.models.user import User
        from app.core.security import get_password_hash

        user = User(
            username=data["username"],
            email=data.get("email"),
            hashed_password=get_password_hash(data["password"]),
            full_name=data.get("full_name"),
            role=data.get("role", "operator"),
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: int, data: dict):
        """更新用户"""
        user = self.get_user_by_id(user_id)
        if user is None:
            return None
        for key, value in data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        if self.db:
            self.db.commit()
            self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        user = self.get_user_by_id(user_id)
        if user is None:
            return False
        if self.db:
            self.db.delete(user)
            self.db.commit()
        return True

    @staticmethod
    async def get_user(user_id: int):
        """异步获取用户（兼容旧接口）"""
        return None
