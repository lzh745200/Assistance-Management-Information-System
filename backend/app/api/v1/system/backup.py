"""
系统备份 API
提供数据库备份的创建、列表、统计、恢复和计划管理功能
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permission_utils import require_admin
from app.services.backup_service import get_backup_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backup", tags=["备份管理"])


# ==================== Pydantic 模型 ====================

class CreateBackupRequest(BaseModel):
    """创建备份请求"""
    description: str = Field("手动备份", description="备份描述")
    include_uploads: bool = Field(True, description="是否包含上传文件")
    password: Optional[str] = Field(None, description="加密密码（可选）")


class RestoreBackupRequest(BaseModel):
    """恢复备份请求"""
    filename: str = Field(..., description="备份文件名")
    password: Optional[str] = Field(None, description="加密密码（加密备份必需）")


class DeleteBackupRequest(BaseModel):
    """删除备份请求"""
    filename: str = Field(..., description="备份文件名")


class BackupScheduleUpdate(BaseModel):
    """备份计划更新"""
    enabled: bool = Field(..., description="是否启用自动备份")
    schedule: Optional[str] = Field(None, description="Cron 表达式或时间间隔")
    keep_count: Optional[int] = Field(10, description="保留备份数量")


# ==================== API 端点 ====================

@router.post("", summary="创建数据库备份")
async def create_backup(
    body: CreateBackupRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建系统数据库备份

    将当前数据库和上传文件打包为 ZIP 备份文件。
    支持可选的 AES-256 加密保护。
    需要管理员权限。
    """
    require_admin(current_user, error_message="仅超级管理员可创建备份")

    try:
        svc = get_backup_service(db)
        record = svc.create_backup(
            description=body.description,
            include_uploads=body.include_uploads,
            password=body.password,
        )

        logger.info(
            "备份已创建: %s，操作人: %s",
            record.file_name, getattr(current_user, "username", "unknown"),
        )

        return {
            "success": True,
            "message": "备份已创建",
            "data": {
                "backup_id": record.backup_id,
                "file_name": record.file_name,
                "file_path": record.file_path,
                "file_size": record.file_size,
                "description": record.description,
                "created_at": record.created_at.isoformat(),
            },
        }
    except Exception as e:
        logger.error("创建备份失败: %s", e)
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")


@router.get("", summary="获取备份列表")
async def list_backups(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取所有数据库备份文件列表

    按创建时间倒序排列，包含文件名、大小、描述等元信息。
    """
    try:
        svc = get_backup_service(db)
        records = svc.list_backups()

        items = []
        for r in records:
            items.append({
                "backup_id": r.backup_id,
                "file_name": r.file_name,
                "file_path": r.file_path,
                "file_size": r.file_size,
                "description": r.description,
                "created_at": r.created_at.isoformat(),
                "backup_type": r.backup_type,
            })

        return {
            "success": True,
            "data": {
                "items": items,
                "total": len(items),
            },
        }
    except Exception as e:
        logger.error("获取备份列表失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")


@router.get("/stats", summary="获取备份统计")
async def get_backup_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取备份统计信息

    返回备份总数、总大小、最早/最新备份时间等统计数据。
    """
    try:
        svc = get_backup_service(db)
        stats = svc.get_backup_statistics()

        # 获取调度器状态
        schedule_enabled = os.getenv("AUTO_BACKUP_ENABLED", "false").lower() == "true"

        return {
            "success": True,
            "data": {
                "totalBackups": stats.get("total_backups", 0),
                "totalSize": stats.get("total_size", 0),
                "totalSizeMb": stats.get("total_size_mb", 0),
                "fullBackups": stats.get("full_backups", 0),
                "incrementalBackups": stats.get("incremental_backups", 0),
                "lastBackup": stats.get("newest_backup"),
                "oldestBackup": stats.get("oldest_backup"),
                "scheduleEnabled": schedule_enabled,
            },
        }
    except Exception as e:
        logger.error("获取备份统计失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取备份统计失败: {str(e)}")


@router.get("/schedule", summary="获取备份计划配置")
async def get_backup_schedule(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取自动备份计划配置

    返回是否启用、执行时间、保留数量等计划参数。
    """
    try:
        from app.services.system_config_service import SystemConfigService
        svc = SystemConfigService(db)

        enabled = svc.get("auto_backup_enabled", "false") == "true"
        schedule = svc.get("auto_backup_schedule", "0 2 * * *")
        keep_count = int(svc.get("auto_backup_keep_count", "10"))
        next_run = svc.get("auto_backup_next_run")

        return {
            "success": True,
            "data": {
                "enabled": enabled,
                "schedule": schedule,
                "keepCount": keep_count,
                "nextRun": next_run,
            },
        }
    except Exception as e:
        logger.error("获取备份计划失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取备份计划失败: {str(e)}")


@router.put("/schedule", summary="更新备份计划配置")
async def update_backup_schedule(
    body: BackupScheduleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新自动备份计划配置

    设置是否启用自动备份、执行时间、保留数量等。
    需要管理员权限。
    """
    require_admin(current_user, error_message="仅超级管理员可修改备份计划")

    try:
        from app.services.system_config_service import SystemConfigService
        svc = SystemConfigService(db)

        svc.set("auto_backup_enabled", str(body.enabled).lower())
        if body.schedule:
            svc.set("auto_backup_schedule", body.schedule)
        if body.keep_count is not None:
            svc.set("auto_backup_keep_count", str(body.keep_count))

        logger.info(
            "备份计划已更新，操作人: %s",
            getattr(current_user, "username", "unknown"),
        )

        return {
            "success": True,
            "message": "备份计划已更新",
            "data": {
                "enabled": body.enabled,
                "schedule": body.schedule,
                "keepCount": body.keep_count,
            },
        }
    except Exception as e:
        logger.error("更新备份计划失败: %s", e)
        raise HTTPException(status_code=500, detail=f"更新备份计划失败: {str(e)}")


@router.delete("/{filename}", summary="删除指定备份")
async def delete_backup(
    filename: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除指定的备份文件

    同时删除磁盘上的备份文件和数据库中的记录。
    需要管理员权限。
    """
    require_admin(current_user, error_message="仅超级管理员可删除备份")

    try:
        svc = get_backup_service(db)
        # 查找匹配文件名的备份
        records = svc.list_backups()
        target = None
        for r in records:
            if r.file_name == filename:
                target = r
                break

        if not target:
            raise HTTPException(status_code=404, detail=f"备份文件 '{filename}' 不存在")

        success = svc.delete_backup(target.backup_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除备份失败")

        logger.info(
            "备份已删除: %s，操作人: %s",
            filename, getattr(current_user, "username", "unknown"),
        )

        return {"success": True, "message": f"备份文件 '{filename}' 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除备份失败: %s", e)
        raise HTTPException(status_code=500, detail=f"删除备份失败: {str(e)}")


@router.get("/download/{filename}", summary="下载备份文件")
async def download_backup(
    filename: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """下载指定的备份文件

    返回备份 ZIP 文件供本地保存或迁移使用。
    """
    from fastapi.responses import FileResponse
    from app.utils.paths import get_backup_path

    backup_dir = str(get_backup_path())
    file_path = os.path.join(backup_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"备份文件 '{filename}' 不存在")

    # 安全检查：确保路径在备份目录内
    real_path = os.path.realpath(file_path)
    real_backup_dir = os.path.realpath(backup_dir)
    if not real_path.startswith(real_backup_dir):
        raise HTTPException(status_code=403, detail="禁止访问备份目录外的文件")

    logger.info(
        "备份文件下载: %s，操作人: %s",
        filename, getattr(current_user, "username", "unknown"),
    )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/zip",
    )


@router.post("/restore", summary="从备份恢复系统")
async def restore_backup(
    body: RestoreBackupRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """从指定的备份文件恢复系统数据

    此操作将覆盖当前数据库和上传文件。
    需要管理员权限。
    """
    require_admin(current_user, error_message="仅超级管理员可恢复备份")

    try:
        from app.utils.paths import get_backup_path

        backup_dir = str(get_backup_path())
        file_path = os.path.join(backup_dir, body.filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"备份文件 '{body.filename}' 不存在")

        svc = get_backup_service(db)
        result = svc.restore_backup(file_path, password=body.password)

        logger.warning(
            "系统已从备份恢复: %s，操作人: %s",
            body.filename, getattr(current_user, "username", "unknown"),
        )

        # 恢复后建议重启服务以回收 SQLite 连接池
        logger.warning(
            "系统已从备份恢复，建议立即重启应用以回收数据库连接池。"
            "恢复文件: %s，操作人: %s",
            body.filename, getattr(current_user, "username", "unknown"),
        )

        return {
            "success": True,
            "message": "系统恢复成功（建议重启应用以确保数据库连接正确）",
            "data": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("恢复备份失败: %s", e)
        raise HTTPException(status_code=500, detail=f"恢复备份失败: {str(e)}")
