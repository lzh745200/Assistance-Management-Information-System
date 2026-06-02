from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PermissionBase(BaseModel):
    """Schema"""

    name: str = Field(..., max_length=100, description="")
    resource: str = Field(..., max_length=50, description="")
    action: str = Field(..., max_length=50, description="")
    description: Optional[str] = Field(None, description="")


class PermissionCreate(PermissionBase):
    """Schema"""


class PermissionUpdate(BaseModel):
    """Schema"""

    description: Optional[str] = None


class PermissionResponse(PermissionBase):
    """Schema"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RolePermissionAssign(BaseModel):
    """Schema"""

    role_id: int
    permission_ids: list[int]
