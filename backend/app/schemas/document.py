"""Pydantic Schema"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    """"""

    title: str = Field(..., min_length=1, max_length=200, description="")
    description: Optional[str] = Field(None, max_length=500, description="")
    file_path: str = Field(..., min_length=1, max_length=255, description="")
    file_type: str = Field(..., min_length=1, max_length=50, description="")
    file_size: int = Field(..., ge=0, description="()")
    category: str = Field(..., min_length=1, max_length=50, description="")
    related_id: Optional[int] = Field(None, description="ID")
    related_type: Optional[str] = Field(None, max_length=50, description="")
    is_public: bool = Field(False, description="")


class DocumentCreate(DocumentBase):
    """"""


class DocumentUpdate(BaseModel):
    """"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    related_id: Optional[int] = None
    related_type: Optional[str] = Field(None, max_length=50)
    is_public: Optional[bool] = None


class DocumentResponse(DocumentBase):
    """"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Document(DocumentResponse):
    """"""
