"""
同步状态API - 兼容前端调用
提供同步状态查询（映射到 data-sync）
"""

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/sync", tags=["同步状态"])


@router.get("/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user),
):
    """
    获取同步状态

    返回当前用户的同步状态信息
    """
    return {
        "success": True,
        "data": {
            "sync_enabled": True,
            "last_sync": None,
            "pending_changes": 0,
            "sync_status": "idle",
            "message": "同步功能正常",
        },
    }
