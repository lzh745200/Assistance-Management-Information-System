from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

# 活动日志模式
"""活动日志 Pydantic Schema"""


class ActivityLogBase(BaseModel):
    """"""

    user_id: int = Field(..., description="ID")
    action: str = Field(..., description="")
    resource_type: Optional[str] = Field(None, description="")
    resource_id: Optional[int] = Field(None, description="ID")
    details: Optional[Dict[str, Any]] = Field(None, description="")
    ip_address: Optional[str] = Field(None, description="IP ")


class ActivityLogCreate(ActivityLogBase):
    """"""


class ActivityLogUpdate(BaseModel):
    """"""

    action: Optional[str] = None


class ActivityLog(ActivityLogBase):
    """"""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityLogResponse(BaseModel):
    """"""

    user_name: Optional[str] = None
