"""系统备份 API — 桩实现"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/backup")
async def create_backup():
    """创建数据库备份"""
    return {"success": True, "message": "备份已创建", "data": {"filename": "backup_latest.db"}}


@router.get("/backup")
async def list_backups():
    """获取备份列表"""
    return {"success": True, "data": {"items": [], "total": 0}}


@router.get("/backup/stats")
async def get_backup_stats():
    """获取备份统计"""
    return {"success": True, "data": {"totalBackups": 0, "lastBackup": None, "totalSize": 0}}


@router.get("/backup/schedule")
async def get_backup_schedule():
    """获取备份计划"""
    return {"success": True, "data": {"enabled": False, "schedule": None, "nextRun": None}}
