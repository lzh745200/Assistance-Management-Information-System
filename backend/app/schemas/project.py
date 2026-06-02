from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

"""Pydantic"""


class ProjectBase(BaseModel):
    """"""

    name: str = Field(..., min_length=1, max_length=100, description="")
    description: Optional[str] = Field(None, max_length=500, description="")
    start_date: datetime = Field(..., description="")
    end_date: Optional[datetime] = Field(None, description="")
    status: str = Field(..., min_length=1, max_length=20, description="")
    budget: float = Field(..., ge=0, description="")
    responsible_person_id: Optional[int] = Field(None, description="ID")
    category: str = Field(..., min_length=1, max_length=50, description="")
    location: str = Field(..., min_length=1, max_length=200, description="")
    priority: str = Field(..., min_length=1, max_length=20, description="")
    remarks: Optional[str] = Field(None, max_length=500, description="")


class ProjectCreate(ProjectBase):
    """"""


class ProjectUpdate(BaseModel):
    """"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="")
    start_date: Optional[datetime] = Field(None, description="")
    status: Optional[str] = Field(None, min_length=1, max_length=20, description="")
    budget: Optional[float] = Field(None, ge=0, description="")
    category: Optional[str] = Field(None, min_length=1, max_length=50, description="")
    location: Optional[str] = Field(None, min_length=1, max_length=200, description="")
    priority: Optional[str] = Field(None, min_length=1, max_length=20, description="")


class ProjectResponse(ProjectBase):
    """"""

    id: int
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """"""

    total: int = Field(..., description="")
    items: list[ProjectResponse] = Field(..., description="")


class ProjectProgressBase(BaseModel):
    """"""

    project_id: int = Field(..., description="ID")
    progress_date: datetime = Field(..., description="")
    progress_percentage: float = Field(..., ge=0, le=100, description="")
    description: str = Field(..., max_length=500, description="")
    reporter_id: Optional[int] = Field(None, description="ID")


class ProjectProgressCreate(ProjectProgressBase):
    """"""


class ProjectProgressResponse(ProjectProgressBase):
    """"""

    id: int
    created_at: datetime
