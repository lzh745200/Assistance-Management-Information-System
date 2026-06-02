"""Pydantic Schema"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    """"""

    name: str = Field(..., description="", max_length=50)
    code: str = Field(..., description="", max_length=50)
    description: Optional[str] = Field(None, description="")
    is_active: bool = Field(True, description="")
    is_default: bool = Field(False, description="")


class RoleCreate(RoleBase):
    """Schema"""


class RoleUpdate(BaseModel):
    """Schema"""

    name: Optional[str] = Field(None, description="", max_length=50)
    code: Optional[str] = Field(None, description="", max_length=50)
    description: Optional[str] = Field(None, description="")
    is_active: Optional[bool] = Field(None, description="")
    is_default: Optional[bool] = Field(None, description="")


class RoleInDB(RoleBase):
    """"""

    id: int = Field(..., description=" ID")
    created_at: datetime = Field(..., description="")
    updated_at: datetime = Field(..., description="")

    model_config = ConfigDict(from_attributes=True)


class Role(RoleInDB):
    """角色Schema"""


class RoleResponse(RoleInDB):
    """角色响应Schema"""
