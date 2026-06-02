"""Pydantic :."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class VillageBase(BaseModel):
    """."""

    name: str = Field(..., min_length=1, max_length=200, description="")
    code: str = Field(..., min_length=1, max_length=50, description="")
    province: Optional[str] = Field(None, max_length=50, description="")
    city: Optional[str] = Field(None, max_length=50, description="")
    county: Optional[str] = Field(None, max_length=50, description="")
    town: Optional[str] = Field(None, max_length=50, description="")
    address: Optional[str] = Field(None, max_length=255, description="")

    longitude: Optional[float] = Field(None, description="")
    latitude: Optional[float] = Field(None, description="")
    altitude: Optional[float] = Field(None, description="()")
    area: Optional[float] = Field(None, ge=0, description="()")

    population: Optional[int] = Field(None, ge=0, description="")
    households: Optional[int] = Field(None, ge=0, description="")
    poor_households: Optional[int] = Field(None, ge=0, description="")
    poor_population: Optional[int] = Field(None, ge=0, description="")

    party_secretary: Optional[str] = Field(None, max_length=50, description="")
    party_secretary_phone: Optional[str] = Field(None, max_length=20, description="")
    village_director: Optional[str] = Field(None, max_length=50, description="")
    village_director_phone: Optional[str] = Field(None, max_length=20, description="")

    organization_structure: Optional[Dict[str, Any]] = Field(None, description=" JSON")
    description: Optional[str] = Field(None, description="")
    main_industries: Optional[str] = Field(None, description="")
    infrastructure: Optional[str] = Field(None, description="")
    education_health: Optional[str] = Field(None, description="")
    support_start_date: Optional[datetime] = Field(None, description="")
    support_unit: Optional[str] = Field(None, max_length=200, description="")
    support_contact: Optional[str] = Field(None, max_length=50, description="")
    support_contact_phone: Optional[str] = Field(None, max_length=20, description="")
    support_status: Optional[str] = Field("ongoing", max_length=20, description="")
    images: Optional[List[str]] = Field(None, description="")
    achievements: Optional[str] = Field(None, description="")
    notes: Optional[str] = Field(None, description="")

    model_config = ConfigDict(from_attributes=True)


class VillageCreate(VillageBase):
    """."""


class VillageUpdate(BaseModel):
    """."""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="")
    province: Optional[str] = Field(None, max_length=50, description="")
    city: Optional[str] = Field(None, max_length=50, description="")
    county: Optional[str] = Field(None, max_length=50, description="")
    town: Optional[str] = Field(None, max_length=50, description="")
    address: Optional[str] = Field(None, max_length=255, description="")
    longitude: Optional[float] = Field(None, description="")
    latitude: Optional[float] = Field(None, description="")
    altitude: Optional[float] = Field(None, description="()")
    area: Optional[float] = Field(None, ge=0, description="()")
    population: Optional[int] = Field(None, ge=0, description="")
    households: Optional[int] = Field(None, ge=0, description="")
    poor_households: Optional[int] = Field(None, ge=0, description="")
    poor_population: Optional[int] = Field(None, ge=0, description="")
    party_secretary: Optional[str] = Field(None, max_length=50, description="")
    party_secretary_phone: Optional[str] = Field(None, max_length=20, description="")
    village_director: Optional[str] = Field(None, max_length=50, description="")
    village_director_phone: Optional[str] = Field(None, max_length=20, description="")
    organization_structure: Optional[Dict[str, Any]] = Field(None, description=" JSON")
    description: Optional[str] = Field(None, description="")
    main_industries: Optional[str] = Field(None, description="")
    infrastructure: Optional[str] = Field(None, description="")
    education_health: Optional[str] = Field(None, description="")
    support_start_date: Optional[datetime] = Field(None, description="")
    support_unit: Optional[str] = Field(None, max_length=200, description="")
    support_contact: Optional[str] = Field(None, max_length=50, description="")
    support_contact_phone: Optional[str] = Field(None, max_length=20, description="")
    support_status: Optional[str] = Field(None, max_length=20, description="")
    images: Optional[List[str]] = Field(None, description="")
    achievements: Optional[str] = Field(None, description="")
    notes: Optional[str] = Field(None, description="")

    model_config = ConfigDict(from_attributes=True)


class VillageResponse(VillageBase):
    """."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VillageListResponse(BaseModel):
    """."""

    total: int = Field(..., description="")
    items: List[VillageResponse] = Field(..., description="")

    model_config = ConfigDict(from_attributes=True)
