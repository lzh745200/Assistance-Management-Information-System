"""
监控API
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user, get_db
from app.models.user import User
from app.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["监控"])


@router.get("/api-performance")
async def get_api_performance(
    hours: int = Query(24, ge=1, le=168),
    endpoint: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取API性能统计
    需要管理员权限
    """
    if not current_user.is_superuser:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="需要管理员权限")

    stats = MonitoringService.get_api_performance_stats(db, hours, endpoint)
    return stats


@router.get("/endpoints")
async def get_endpoint_stats(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取各端点统计信息
    需要管理员权限
    """
    if not current_user.is_superuser:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="需要管理员权限")

    stats = MonitoringService.get_endpoint_stats(db, hours, limit)
    return {"endpoints": stats}


@router.get("/errors")
async def get_error_stats(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取错误统计
    需要管理员权限
    """
    if not current_user.is_superuser:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="需要管理员权限")

    stats = MonitoringService.get_error_stats(db, hours)
    return stats


@router.get("/resources")
async def get_resource_stats(current_user: User = Depends(get_current_active_user)):
    """
    获取系统资源统计
    需要管理员权限
    """
    if not current_user.is_superuser:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="需要管理员权限")

    stats = MonitoringService.get_resource_stats()
    return stats
