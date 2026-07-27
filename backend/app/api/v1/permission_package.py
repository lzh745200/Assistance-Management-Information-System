"""
权限配置包 API 路由

提供权限配置包的导出/导入功能，用于离线多机协作场景下的权限同步。
"""

import logging
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.schemas.permission_package import (
    PermissionPackageConfirmRequest,
    PermissionPackageConfirmResult,
    PermissionPackageExportRequest,
    PermissionPackageExportResult,
    PermissionPackageImportResult,
)
from app.services.permission_package_service import PermissionPackageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/permission-packages", tags=["权限配置包"])


@router.post("/export", response_model=PermissionPackageExportResult, summary="导出权限配置包")
def export_permission_package(
    body: PermissionPackageExportRequest = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    导出完整权限配置为 ZIP 包。

    包含: RBAC 角色、角色权限、用户-角色关联、用户直接权限、
    用户菜单覆盖、用户遗留权限字段。
    """
    service = PermissionPackageService(db)
    result = service.export_package(
        password=body.password if body else None,
        description=body.description if body else None,
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message", "导出失败"))

    return JSONResponse(content=result)


@router.get("/download/{file_name}", summary="下载权限配置包文件")
def download_permission_package(
    file_name: str,
    current_user: User = Depends(require_admin),
):
    """
    下载已导出的权限配置包 ZIP 文件。
    """
    from app.utils.paths import get_uploads_path

    upload_dir = str(get_uploads_path("permission_packages"))
    file_path = os.path.join(upload_dir, file_name)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="文件不存在或已被清理")

    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.post("/import", response_model=PermissionPackageImportResult, summary="导入权限配置包（验证预览）")
async def import_permission_package(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    上传权限配置包 ZIP 文件，进行验证并返回预览数据。

    此步骤不实际修改数据库，让管理员确认后再执行导入。
    """
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="请上传 .zip 格式的权限配置包文件")

    from app.utils.paths import get_uploads_path
    # Save to permanent upload dir so confirm step can find it
    upload_dir = str(get_uploads_path("permission_packages"))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    tmp_path = file_path
    try:
        service = PermissionPackageService(db)
        result = service.import_package(tmp_path)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error("权限配置包导入预览失败: %s", e, exc_info=True)
        # Clean up on error since confirm won't need it
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail=f"导入预览失败: {e}")


@router.post("/confirm/{file_name}", response_model=PermissionPackageConfirmResult, summary="确认导入权限配置包")
def confirm_import_permission_package(
    file_name: str,
    body: PermissionPackageConfirmRequest = PermissionPackageConfirmRequest(),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    确认导入权限配置包，将所有权限配置写入数据库。

    导入策略: 完全替换（mirror mode）。
    警告: 此操作会删除目标电脑上的现有 RBAC 权限配置（系统角色除外）。
    """
    from app.utils.paths import get_uploads_path

    upload_dir = str(get_uploads_path("permission_packages"))
    file_path = os.path.join(upload_dir, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="导入文件不存在，请先通过 /import 上传")

    service = PermissionPackageService(db)
    try:
        result = service.confirm_import(file_path, overwrite_existing=body.overwrite_existing)
    finally:
        # Clean up the uploaded file after import (success or failure)
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except OSError:
            pass

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message", "导入失败"))

    return JSONResponse(content=result)
