"""Pydantic Schema"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SystemMetricsResponse(BaseModel):
    """Schema"""

    id: int
    cpu_percent: Optional[float] = None
    cpu_count: Optional[int] = None
    memory_total: Optional[float] = None
    memory_used: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_total: Optional[float] = None
    disk_used: Optional[float] = None
    disk_percent: Optional[float] = None
    network_sent_mb: Optional[float] = None
    network_recv_mb: Optional[float] = None
    db_connections: Optional[int] = None
    db_pool_size: Optional[int] = None
    active_users: Optional[int] = None
    request_count: Optional[int] = None
    error_count: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class APIMetricsResponse(BaseModel):
    """APISchema"""

    id: int
    endpoint: str
    method: str
    response_time_ms: Optional[int] = None
    status_code: Optional[int] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PerformanceAlertResponse(BaseModel):
    """Schema"""

    id: int
    alert_type: str
    severity: str
    title: str
    description: Optional[str] = None
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    status: str
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonitorDashboard(BaseModel):
    """Schema"""

    current_metrics: Optional[SystemMetricsResponse] = None
    recent_alerts: List[PerformanceAlertResponse]
    slow_apis: List[APIMetricsResponse]
    error_rate: float
    avg_response_time: float


class MonitorCreate(BaseModel):
    """监控创建Schema"""

    name: str
    description: Optional[str] = None
    monitor_type: str = "system"  # system, api, database
    interval_seconds: int = 60
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    enabled: bool = True

    model_config = ConfigDict(from_attributes=True)


class MonitorUpdate(BaseModel):
    """监控更新Schema"""

    name: Optional[str] = None
    description: Optional[str] = None
    interval_seconds: Optional[int] = None
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    enabled: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class MonitorResponse(BaseModel):
    """监控响应Schema"""

    id: int
    name: str
    description: Optional[str] = None
    monitor_type: str
    interval_seconds: int
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    enabled: bool
    status: str = "active"  # active, paused, error
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
