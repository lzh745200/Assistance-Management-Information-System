"""
Data Package API
数据包管理接口 - 导入导出功能
"""
import logging
import os
import tempfile
import time
from typing import List, Optional

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     Request, UploadFile, status)
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessError, NotFoundException
from app.core.security import get_current_user
from app.core.permission_utils import get_org_with_fallback
from app.models.import_export_history import OperationResult
from app.models.data_package import PackageType
from app.schemas.data_package import (DataPackageConfirmRequest,
                                      DataPackageConfirmResult,
                                      DataPackageExportRequest,
                                      DataPackageExportResult,
                                      DataPackageImportResult,
                                      DataPackageListResponse,
                                      DataPackagePreviewData,
                                      DataPackageResponse,
                                      DataPackageValidationResult)
from app.services.data_package_service import DataPackageService
from app.services.import_export_history_service import \
    ImportExportHistoryService
from app.core.transaction import safe_commit
from app.services.organization_permission_service import \
    OrganizationPermissionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-packages", tags=["数据包管理"])

# ==================== 错误消息常量 ====================
ORG_NOT_BOUND_ERROR = "当前用户未绑定组织，无法执行此操作。请联系管理员在系统管理中为您分配组织。"

# 一键上报默认导出的数据类型
ONE_CLICK_DATA_TYPES = ["villages", "projects", "funds", "schools"]


def get_package_service(db: Session = Depends(get_db)) -> DataPackageService:
    return DataPackageService(db)


def get_history_service(db: Session = Depends(get_db)) -> ImportExportHistoryService:
    return ImportExportHistoryService(db)


def get_permission_service(db: Session = Depends(get_db)) -> OrganizationPermissionService:
    return OrganizationPermissionService(db)


def get_client_ip(request: Request) -> str:
    """获取客户端IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_first_active_org(db: Session) -> Optional[int]:
    """获取第一个活跃组织的ID（内部辅助函数）"""
    from app.models.organization import Organization

    first_org = db.query(Organization).filter(Organization.is_active == True).first()  # noqa: E712
    return first_org.id if first_org else None


class OneClickReportRequest(BaseModel):
    """一键上报请求体（可选）"""

    year: Optional[int] = None
    data_types: Optional[List[str]] = None
    remarks: Optional[str] = None
    description: Optional[str] = None


@router.post("/one-click-report")
async def one_click_report(
    request: Request,
    body: Optional[OneClickReportRequest] = None,
    description: Optional[str] = None,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    history_service: ImportExportHistoryService = Depends(get_history_service),
):
    """
    一键生成上报数据包
    自动收集当前用户所属组织的所有数据类型，打包导出并返回下载文件流。
    支持前端发送 JSON body 包含 year/data_types/remarks 字段。
    """
    # 获取组织ID（支持超级管理员回退到第一个可用组织）
    org_id = get_org_with_fallback(
        current_user=current_user,
        requested_org_id=None,
        get_first_org_callback=lambda: _get_first_active_org(service.db),
    )

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ORG_NOT_BOUND_ERROR
        )

    # 从 body 中提取参数（如果前端发送了 JSON body）
    data_types = ONE_CLICK_DATA_TYPES
    desc = description or "一键上报数据包"
    if body:
        if body.data_types:
            data_types = body.data_types
        if body.remarks:
            desc = body.remarks
        if body.description:
            desc = body.description

    start_time = time.time()

    try:
        result = await service.export_package(
            org_id=org_id,
            data_types=data_types,
            export_by=current_user.id,
            description=desc,
            package_type=PackageType.report,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # 记录导出历史
        try:
            history_service.record_export(
                package_id=result.package_id,
                org_id=org_id,
                user_id=current_user.id,
                file_name=result.file_name,
                file_size=result.file_size,
                record_count=sum(result.manifest.record_counts.values()) if result.manifest else 0,
                data_types=ONE_CLICK_DATA_TYPES,
                duration_ms=duration_ms,
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
            )
        except Exception as e:
            logger.warning(f"记录一键上报历史失败: {e}")

        # 直接返回文件流
        file_path = getattr(result, "file_path", None)
        if file_path and os.path.exists(file_path):
            return FileResponse(
                path=file_path,
                filename=result.file_name or "report_package.zip",
                media_type="application/zip",
                headers={
                    "X-Package-Id": str(result.package_id),
                    "X-Record-Count": str(sum(result.manifest.record_counts.values()) if result.manifest else 0),
                },
            )

        # file_path 不可用时返回元数据（前端走 download 接口）
        return {
            "success": True,
            "package_id": result.package_id,
            "file_name": result.file_name,
            "file_size": result.file_size,
            "download_url": f"/api/v1/data-packages/{result.package_id}/download",
            "manifest": result.manifest.model_dump() if result.manifest else None,
        }

    except Exception as e:
        import traceback

        logger.error(f"一键上报失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"生成上报数据包失败: {str(e)}")


@router.get("", response_model=DataPackageListResponse)
async def list_data_packages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    org_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    type_filter: Optional[str] = Query(None, alias="type"),
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    permission_service: OrganizationPermissionService = Depends(get_permission_service),
):
    """获取数据包列表"""
    # 确定查询的组织ID（多级回退）
    target_org_id = org_id
    if not target_org_id:
        target_org_id = getattr(current_user, "organization_id", None) or getattr(current_user, "org_id", None)

    if not target_org_id:
        return DataPackageListResponse(total=0, page=page, page_size=page_size, items=[])

    # 检查权限 - 普通用户无权限时返回空列表而不是403，确保页面正常加载
    if not permission_service.can_access_organization(current_user.id, target_org_id):
        return DataPackageListResponse(total=0, page=page, page_size=page_size, items=[])

    packages = service.get_packages_by_org(
        target_org_id, status=status_filter, type_filter=type_filter, skip=(page - 1) * page_size, limit=page_size
    )

    total = len(packages)  # 简化实现，实际应该单独查询总数

    return DataPackageListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[DataPackageResponse.model_validate(pkg) for pkg in packages],
    )


@router.get("/{package_id}", response_model=DataPackageResponse)
async def get_data_package(
    package_id: int,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    permission_service: OrganizationPermissionService = Depends(get_permission_service),
):
    """获取数据包详情"""
    package = service.get_package(package_id)
    if not package:
        raise NotFoundException("数据包不存在")

    # 检查权限 - 普通用户无权限时抛出404而不是403，避免前端看到错误
    if not permission_service.can_access_organization(current_user.id, package.org_id):
        raise NotFoundException("数据包不存在")

    return DataPackageResponse.model_validate(package)


@router.post("/preview")
async def preview_data_for_export(
    data: DataPackageExportRequest,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
):
    """预览导出数据的统计信息（不生成包，仅返回各数据类型记录数）"""
    # 获取组织ID（支持超级管理员回退到第一个可用组织）
    org_id = get_org_with_fallback(
        current_user=current_user,
        requested_org_id=data.org_id,
        get_first_org_callback=lambda: _get_first_active_org(service.db),
    )

    from app.services.data_package_service import DATA_TYPE_MODELS

    counts = {}
    data_types = data.data_types or ["villages", "projects", "funds", "schools"]
    for dt in data_types:
        model = DATA_TYPE_MODELS.get(dt)
        if model:
            query = service.db.query(model)
            if org_id and hasattr(model, "org_id"):
                query = query.filter(model.org_id == org_id)
            counts[dt] = query.count()
        else:
            counts[dt] = 0

    return {"counts": counts}


@router.post("/export", response_model=DataPackageExportResult)
async def export_data_package(
    data: DataPackageExportRequest,
    request: Request,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    history_service: ImportExportHistoryService = Depends(get_history_service),
    permission_service: OrganizationPermissionService = Depends(get_permission_service),
):
    """导出数据包"""
    # 获取组织ID（支持超级管理员回退到第一个可用组织）
    org_id = get_org_with_fallback(
        current_user=current_user,
        requested_org_id=data.org_id,
        get_first_org_callback=lambda: _get_first_active_org(service.db),
    )

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ORG_NOT_BOUND_ERROR
        )

    # 检查权限
    if not permission_service.can_access_organization(current_user.id, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您没有权限访问该组织的数据。请联系管理员为您分配正确的组织权限。"
        )

    start_time = time.time()

    try:
        result = await service.export_package(
            org_id=org_id,
            data_types=data.data_types,
            export_by=current_user.id,
            description=data.description,
            package_type=data.type,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # 记录导出历史
        try:
            history_service.record_export(
                package_id=result.package_id,
                org_id=org_id,
                user_id=current_user.id,
                file_name=result.file_name,
                file_size=result.file_size,
                record_count=sum(result.manifest.record_counts.values()) if result.manifest else 0,
                data_types=data.data_types,
                duration_ms=duration_ms,
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
            )
        except Exception as e:
            logger.warning(f"记录导出历史失败: {e}")

        return result

    except BusinessError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback

        logger.error(f"导出数据包失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"导出失败: {str(e)}")


@router.post("/import", response_model=DataPackageImportResult)
async def import_data_package(
    file: UploadFile = File(...),
    org_id: Optional[int] = None,
    request: Request = None,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    history_service: ImportExportHistoryService = Depends(get_history_service),
    permission_service: OrganizationPermissionService = Depends(get_permission_service),
):
    """导入数据包"""
    # 验证文件
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="未选择文件")

    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="文件格式错误，仅支持 .zip 格式的数据包"
        )

    # 确定组织ID
    target_org_id = org_id
    if not target_org_id and hasattr(current_user, "org_id"):
        target_org_id = current_user.org_id

    if not target_org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未指定目标组织ID")

    # 检查权限
    if not permission_service.can_access_organization(current_user.id, target_org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权向该组织导入数据")

    start_time = time.time()

    # 保存上传文件到临时目录
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        content = await file.read()

        # 检查文件大小
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="文件为空，请选择有效的数据包文件"
            )

        if len(content) > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="文件过大，数据包大小不能超过 100MB"
            )

        temp_file.write(content)
        temp_file.close()

        result = await service.import_package(
            file_path=temp_file.name, file_name=file.filename, org_id=target_org_id, imported_by=current_user.id
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # 记录导入历史
        op_result = OperationResult.SUCCESS if result.validation.is_valid else OperationResult.FAILED
        error_msg = None
        if not result.validation.is_valid:
            error_msg = "; ".join([e.message for e in result.validation.errors[:3]])

        history_service.record_import(
            package_id=result.package_id,
            org_id=target_org_id,
            user_id=current_user.id,
            file_name=file.filename,
            file_size=len(content),
            record_count=sum(result.manifest.record_counts.values()) if result.manifest else 0,
            data_types=result.manifest.data_types if result.manifest else [],
            duration_ms=duration_ms,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.headers.get("User-Agent") if request else None,
            result=op_result,
            error_message=error_msg,
        )

        return result

    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except BusinessError as e:
        # 业务错误转换为友好提示
        error_detail = str(e)
        if "无法解压" in error_detail or "not a zip file" in error_detail.lower():
            error_detail = "数据包文件损坏或格式错误，请重新导出后再试"
        elif "manifest" in error_detail.lower():
            error_detail = "数据包清单文件缺失或格式错误，请使用系统导出的标准数据包"

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
    except Exception as e:
        logger.error(f"导入数据包失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )

    finally:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@router.post("/{package_id}/validate", response_model=DataPackageValidationResult)
async def validate_data_package(
    package_id: int,
    request: Request,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    history_service: ImportExportHistoryService = Depends(get_history_service),
):
    """验证数据包"""
    package = service.get_package(package_id)
    if not package:
        raise NotFoundException("数据包不存在")

    result = await service.validate_package(package.file_path)

    # 记录验证历史
    op_result = OperationResult.SUCCESS if result.is_valid else OperationResult.FAILED
    history_service.record_validate(
        package_id=package_id,
        org_id=package.org_id,
        user_id=current_user.id,
        result=op_result,
        error_message="; ".join([e.message for e in result.errors]) if result.errors else None,
        ip_address=get_client_ip(request),
    )

    return result


@router.get("/{package_id}/preview", response_model=List[DataPackagePreviewData])
async def preview_data_package(
    package_id: int,
    request: Request,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    history_service: ImportExportHistoryService = Depends(get_history_service),
    permission_service: OrganizationPermissionService = Depends(get_permission_service),
):
    """预览数据包内容"""
    package = service.get_package(package_id)
    if not package:
        raise NotFoundException("数据包不存在")

    # 检查权限 - 无权限时返回空列表
    if not permission_service.can_access_organization(current_user.id, package.org_id):
        return []

    preview = await service.preview_package_data(package_id)

    # 记录预览历史
    history_service.record_preview(
        package_id=package_id, org_id=package.org_id, user_id=current_user.id, ip_address=get_client_ip(request)
    )

    return preview


@router.post("/{package_id}/confirm", response_model=DataPackageConfirmResult)
async def confirm_import(
    package_id: int,
    data: DataPackageConfirmRequest,
    request: Request,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    history_service: ImportExportHistoryService = Depends(get_history_service),
    permission_service: OrganizationPermissionService = Depends(get_permission_service),
):
    """确认导入数据"""
    package = service.get_package(package_id)
    if not package:
        raise NotFoundException("数据包不存在")

    # 检查权限
    if not permission_service.can_access_organization(current_user.id, package.org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权确认该数据包导入")

    start_time = time.time()

    try:
        result = await service.confirm_import(
            package_id=package_id,
            confirmed_by=current_user.id,
            overwrite_existing=data.overwrite_existing,
            selected_types=data.selected_types,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # 记录确认历史
        op_result = OperationResult.SUCCESS if result.success else OperationResult.FAILED
        total_imported = sum(result.imported_counts.values())

        history_service.record_confirm(
            package_id=package_id,
            org_id=package.org_id,
            user_id=current_user.id,
            record_count=total_imported,
            data_types=data.selected_types,
            duration_ms=duration_ms,
            result=op_result,
            details={
                "imported_counts": result.imported_counts,
                "skipped_counts": result.skipped_counts,
                "error_counts": result.error_counts,
            },
            ip_address=get_client_ip(request),
        )

        return result

    except BusinessError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{package_id}/download")
async def download_data_package(
    package_id: int,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    permission_service: OrganizationPermissionService = Depends(get_permission_service),
):
    """下载数据包"""
    package = service.get_package(package_id)
    if not package:
        raise NotFoundException("数据包不存在")

    # 检查权限 - 无权限时返回404
    if not permission_service.can_access_organization(current_user.id, package.org_id):
        raise NotFoundException("数据包不存在")

    if not package.file_path or not os.path.exists(package.file_path):
        raise NotFoundException("数据包文件不存在")

    return FileResponse(
        path=package.file_path,
        filename=package.file_name or f"{package.package_code}.zip",
        media_type="application/zip",
    )


@router.delete("/{package_id}")
async def delete_data_package(
    package_id: int,
    reason: Optional[str] = None,
    request: Request = None,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    history_service: ImportExportHistoryService = Depends(get_history_service),
    permission_service: OrganizationPermissionService = Depends(get_permission_service),
    db: Session = Depends(get_db),
):
    """删除数据包"""
    package = service.get_package(package_id)
    if not package:
        raise NotFoundException("数据包不存在")

    # 检查权限
    if not permission_service.can_access_organization(current_user.id, package.org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该数据包")

    org_id = package.org_id

    # 记录删除历史
    history_service.record_delete(
        package_id=package_id,
        org_id=org_id,
        user_id=current_user.id,
        reason=reason,
        ip_address=get_client_ip(request) if request else None,
    )

    # 删除文件
    if package.file_path and os.path.exists(package.file_path):
        os.unlink(package.file_path)

    # 删除数据库记录
    db.delete(package)
    safe_commit(db)

    return {"message": "删除成功"}


@router.get("/{package_id}/history")
async def get_package_history(
    package_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    history_service: ImportExportHistoryService = Depends(get_history_service),
    permission_service: OrganizationPermissionService = Depends(get_permission_service),
):
    """获取数据包操作历史"""
    package = service.get_package(package_id)
    if not package:
        raise NotFoundException("数据包不存在")

    # 检查权限 - 无权限时返回空历史
    if not permission_service.can_access_organization(current_user.id, package.org_id):
        return {
            "package_id": package_id,
            "items": [],
        }

    history = history_service.get_history_by_package(package_id, skip=(page - 1) * page_size, limit=page_size)

    return {
        "package_id": package_id,
        "items": [
            {
                "id": h.id,
                "operation_type": h.operation_type,
                "result": h.result,
                "user_id": h.user_id,
                "operation_time": h.operation_time,
                "duration_ms": h.duration_ms,
                "error_message": h.error_message,
            }
            for h in history
        ],
    }


# ========================================================================
# 加密导入导出端点
# ========================================================================


class ExportEncryptedRequest(BaseModel):
    """加密导出请求（密码经请求体传输，避免落入 URL/请求日志）"""

    data_types: List[str]
    password: Optional[str] = None
    description: Optional[str] = None
    package_type: PackageType = PackageType.report


@router.post("/export-encrypted", response_model=DataPackageExportResult)
async def export_encrypted_package(
    request: Request,
    body: ExportEncryptedRequest,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    history_service: ImportExportHistoryService = Depends(get_history_service),
):
    """
    导出加密数据包

    支持密码加密，使用PBKDF2密钥派生和Fernet加密
    """
    password = body.password
    data_types = body.data_types
    description = body.description
    package_type = body.package_type

    # 获取组织ID（支持超级管理员回退到第一个可用组织）
    org_id = get_org_with_fallback(
        current_user=current_user,
        requested_org_id=None,
        get_first_org_callback=lambda: _get_first_active_org(service.db),
    )

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ORG_NOT_BOUND_ERROR
        )

    # 验证密码强度
    if password and len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码长度至少8位")

    start_time = time.time()
    client_ip = get_client_ip(request)

    try:
        result = await service.export_encrypted_package(
            org_id=org_id,
            data_types=data_types,
            export_by=current_user.id,
            password=password,
            description=description,
            package_type=package_type,
        )

        # 记录历史
        duration_ms = int((time.time() - start_time) * 1000)
        try:
            history_service.create_history(
                package_id=result.package_id,
                operation_type="export_encrypted" if password else "export",
                result=OperationResult.SUCCESS,
                user_id=current_user.id,
                duration_ms=duration_ms,
                client_ip=client_ip,
            )
        except Exception as e:
            logger.warning(f"记录导出加密历史失败: {e}")

        return result

    except Exception as e:
        logger.error(f"导出加密数据包失败: {str(e)}", exc_info=True)
        duration_ms = int((time.time() - start_time) * 1000)
        try:
            history_service.create_history(
                package_id=None,
                operation_type="export_encrypted" if password else "export",
                result=OperationResult.FAILED,
                user_id=current_user.id,
                duration_ms=duration_ms,
                client_ip=client_ip,
                error_message=str(e),
            )
        except Exception as hist_err:
            logger.warning(f"记录导出加密历史失败: {hist_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class UploadEncryptedPackageRequest(BaseModel):
    """上传加密包请求"""

    password: Optional[str] = None


@router.post("/upload-encrypted", response_model=DataPackageResponse)
async def upload_encrypted_package(
    request: Request,
    file: UploadFile = File(...),
    password: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
):
    """
    上传加密数据包（第一步：上传并检测加密）

    返回数据包ID和是否需要密码（密码经 multipart 表单字段传输，避免落入 URL/请求日志）
    """
    # 获取组织ID（支持超级管理员回退到第一个可用组织）
    org_id = get_org_with_fallback(
        current_user=current_user,
        requested_org_id=None,
        get_first_org_callback=lambda: _get_first_active_org(service.db),
    )

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ORG_NOT_BOUND_ERROR
        )

    # 保存上传文件
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"upload_{int(time.time())}_{file.filename}")

    try:
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 检测是否加密
        import zipfile

        is_encrypted = False
        try:
            with zipfile.ZipFile(temp_file_path, "r") as zf:
                zf.read("manifest.json")
        except (zipfile.BadZipFile, KeyError):
            is_encrypted = True

        # 创建数据包记录
        from app.models.data_package import PackageStatus

        package = service._create_package_record(
            file_path=temp_file_path,
            file_name=file.filename,
            org_id=org_id,
            created_by=current_user.id,
            status=PackageStatus.pending,
        )

        # 如果检测到加密，更新记录
        if is_encrypted:
            package.is_encrypted = True
            safe_commit(service.db)

        return DataPackageResponse(
            id=package.id,
            package_code=package.package_code,
            org_id=package.org_id,
            file_name=package.file_name,
            file_size=package.file_size,
            status=package.status,
            is_encrypted=is_encrypted,
            created_at=package.created_at,
        )

    except Exception as e:
        logger.error(f"上传加密数据包失败: {str(e)}", exc_info=True)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class DecryptPreviewRequest(BaseModel):
    """解密预览请求（密码经请求体传输，避免落入 URL/请求日志）"""

    password: str


@router.post("/decrypt-preview/{package_id}")
async def decrypt_and_preview_package(
    package_id: int,
    body: DecryptPreviewRequest,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
):
    """
    解密并预览数据包（第二步：提供密码解密）

    返回预览数据和冲突信息
    """
    try:
        result = await service.decrypt_and_preview_package(package_id, body.password)
        return result
    except BusinessError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"解密预览失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class ConfirmImportRequest(BaseModel):
    """确认导入请求"""

    conflict_strategy: str = "KEEP_BOTH"


@router.post("/confirm-import/{package_id}")
async def confirm_import_with_conflict_resolution(
    request: Request,
    package_id: int,
    body: ConfirmImportRequest,
    current_user=Depends(get_current_user),
    service: DataPackageService = Depends(get_package_service),
    history_service: ImportExportHistoryService = Depends(get_history_service),
):
    """
    确认导入并处理冲突（第三步：选择冲突策略并导入）

    支持的策略：SKIP, OVERWRITE, KEEP_BOTH, MERGE
    """
    start_time = time.time()
    client_ip = get_client_ip(request)

    try:
        result = await service.confirm_import_with_conflict_resolution(package_id, body.conflict_strategy)

        # 记录历史
        duration_ms = int((time.time() - start_time) * 1000)
        history_service.create_history(
            package_id=package_id,
            operation_type="import",
            result=OperationResult.SUCCESS,
            user_id=current_user.id,
            duration_ms=duration_ms,
            client_ip=client_ip,
        )

        return result

    except Exception as e:
        logger.error(f"确认导入失败: {str(e)}", exc_info=True)
        duration_ms = int((time.time() - start_time) * 1000)
        history_service.create_history(
            package_id=package_id,
            operation_type="import",
            result=OperationResult.FAILED,
            user_id=current_user.id,
            duration_ms=duration_ms,
            client_ip=client_ip,
            error_message=str(e),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
