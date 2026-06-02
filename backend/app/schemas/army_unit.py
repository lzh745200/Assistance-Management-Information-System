"""Pydantic Schema"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ArmyUnitBase(BaseModel):
    """"""

    unit_name: str = Field(..., min_length=1, max_length=100, description="")
    unit_code: str = Field(..., min_length=1, max_length=50, description="")
    unit_level: Optional[str] = Field(None, max_length=50, description="")
    location: Optional[str] = Field(None, max_length=200, description="")
    description: Optional[str] = Field(None, description="")
    contact_person: Optional[str] = Field(None, max_length=100, description="")
    contact_phone: Optional[str] = Field(None, max_length=20, description="")


class ArmyUnitCreate(ArmyUnitBase):
    """"""


class ArmyUnitUpdate(BaseModel):
    """"""

    unit_name: Optional[str] = Field(None, min_length=1, max_length=100)
    unit_code: Optional[str] = Field(None, min_length=1, max_length=50)
    unit_level: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)


class ArmyUnitResponse(ArmyUnitBase):
    """"""

    id: int = Field(..., description="ID")
    created_at: datetime = Field(..., description="")
    updated_at: datetime = Field(..., description="")

    model_config = ConfigDict(from_attributes=True)


class ArmyUnit(ArmyUnitResponse):
    """"""
