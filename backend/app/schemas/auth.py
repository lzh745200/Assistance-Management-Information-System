"""认证相关 Pydantic Schemas"""

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class Token(BaseModel):
    """令牌"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class TokenPayload(BaseModel):
    """令牌载荷"""

    sub: Optional[str] = None


class UserInfo(BaseModel):
    """用户基本信息"""

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="姓名")
    role: Optional[str] = Field(None, description="角色")
    is_active: bool = Field(default=True, description="是否激活")
    is_superuser: bool = Field(default=False, description="是否超级管理员")
    organization_id: Optional[int] = Field(None, description="所属组织ID")
    organization_name: Optional[str] = Field(None, description="所属组织名称")
    permissions: Optional[list] = Field(default_factory=list, description="权限列表")
    allowed_menus: Optional[list] = Field(None, description="允许访问的菜单列表")
    allowed_menus_list: Optional[list] = Field(None, description="允许访问的菜单key列表")


class LoginData(BaseModel):
    """登录数据（token + user）"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: Optional[UserInfo] = Field(None, description="用户信息")


class LoginResponse(BaseModel):
    """登录响应"""

    code: int = Field(default=200, description="状态码")
    data: Optional[LoginData] = Field(None, description="登录数据")
    message: str = Field(default="", description="消息")
    must_change_password: bool = Field(default=False, description="是否必须修改密码")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=12, description="新密码，至少12位")
