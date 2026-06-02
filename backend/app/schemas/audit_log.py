from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.audit import AuditAction as AuditActionEnum


class AuditLogCreate(BaseModel):
    """Schema"""

    user_id: Optional[int] = None
    username: str
    action: AuditActionEnum
    resource_type: str
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    description: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_url: Optional[str] = None
    request_method: Optional[str] = None
    status: str = "success"
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None


class AuditLogResponse(BaseModel):
    """Schema"""

    id: int
    user_id: Optional[int]
    resource_id: Optional[str]
    resource_name: Optional[str]
    description: Optional[str]
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_url: Optional[str]
    request_method: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime
    duration_ms: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class AuditLogQuery(BaseModel):
    """Schema"""

    username: Optional[str] = None
    action: Optional[AuditActionEnum] = None
    resource_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
