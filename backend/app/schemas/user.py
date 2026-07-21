"""用户 Pydantic Schemas"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """用户基础模型"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="姓名")
    phone_number: Optional[str] = Field(None, max_length=20, description="电话")
    is_active: Optional[bool] = Field(default=True, description="是否激活")
    is_superuser: Optional[bool] = Field(default=False, description="是否超级管理员")
    role_id: Optional[int] = Field(None, description="角色ID")


class UserCreate(UserBase):
    """创建用户"""

    password: str = Field(..., min_length=12, description="密码，至少12位")


class UserUpdate(BaseModel):
    """更新用户"""

    email: Optional[str] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    role_id: Optional[int] = None
    password: Optional[str] = Field(None, min_length=12)


class UserInDB(UserBase):
    """数据库中的用户"""

    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime


class UserResponse(UserBase):
    """用户响应"""

    id: int
    created_at: datetime
    updated_at: datetime
