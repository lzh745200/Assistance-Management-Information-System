"""Pydantic Schema"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ResourceBase(BaseModel):
    """"""

    name: str = Field(..., min_length=1, max_length=100, description="")
    type: str = Field(..., min_length=1, max_length=50, description="")
    quantity: float = Field(..., ge=0, description="")
    unit: str = Field(..., min_length=1, max_length=20, description="")
    location: Optional[str] = Field(None, max_length=200, description="")
    owner_id: Optional[int] = Field(None, description="ID")
    available: bool = Field(True, description="")
    remarks: Optional[str] = Field(None, max_length=500, description="")


class ResourceCreate(ResourceBase):
    """"""


class ResourceUpdate(BaseModel):
    """"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    quantity: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    location: Optional[str] = Field(None, max_length=200)
    owner_id: Optional[int] = None
    available: Optional[bool] = None
    remarks: Optional[str] = Field(None, max_length=500)


class ResourceResponse(ResourceBase):
    """"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Resource(ResourceResponse):
    """"""
