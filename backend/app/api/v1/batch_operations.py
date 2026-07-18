"""批量操作API路由"""

from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import logging

from app.core.exceptions import BusinessError, ValidationError, DatabaseError
from app.core.permission_utils import require_admin
from app.core.security import get_current_user
from app.models.user import User
from app.services.batch_service import batch_service, TABLE_MODEL_MAP

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/batch", tags=["批量操作"])


class BatchUpdateRequest(BaseModel):
    table_name: str = Field(..., description="表名")
    ids: List[int] = Field(..., min_length=1, max_length=1000, description="ID列表")
    updates: Dict[str, Any] = Field(..., min_length=1, description="更新字段")

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        """验证表名是否在白名单中"""
        if v not in TABLE_MODEL_MAP:
            raise ValueError(f"不允许的表名: {v}")
        return v

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v: List[int]) -> List[int]:
        """验证ID列表"""
        if not v:
            raise ValueError("ID列表不能为空")
        if len(v) > 1000:
            raise ValueError("单次批量操作最多支持1000条记录")
        if any(id <= 0 for id in v):
            raise ValueError("ID必须为正整数")
        return v

    @field_validator("updates")
    @classmethod
    def validate_updates(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """验证更新字段"""
        if not v:
            raise ValueError("更新字段不能为空")
        forbidden_fields = {
            "id", "created_at", "organization_id",
            # 账号权限类字段：批量接口绝不允许更新（提权通道封堵）
            "role", "is_superuser", "hashed_password", "password",
            "permissions", "token_version", "allowed_menus", "allowed_permissions",
        }
        if any(field in forbidden_fields for field in v.keys()):
            raise ValueError("不允许更新敏感字段")
        return v


class BatchDeleteRequest(BaseModel):
    table_name: str = Field(..., description="表名")
    ids: List[int] = Field(..., min_length=1, max_length=1000, description="ID列表")
    soft_delete: bool = Field(True, description="是否软删除")

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        if v not in TABLE_MODEL_MAP:
            raise ValueError(f"不允许的表名: {v}")
        return v

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError("ID列表不能为空")
        if len(v) > 1000:
            raise ValueError("单次批量操作最多支持1000条记录")
        if any(id <= 0 for id in v):
            raise ValueError("ID必须为正整数")
        return v


class BatchExportRequest(BaseModel):
    table_name: str = Field(..., description="表名")
    ids: List[int] = Field(..., min_length=1, max_length=5000, description="ID列表")
    format: str = Field("xlsx", description="导出格式")

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        if v not in TABLE_MODEL_MAP:
            raise ValueError(f"不允许的表名: {v}")
        return v

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError("ID列表不能为空")
        if len(v) > 5000:
            raise ValueError("单次导出最多支持5000条记录")
        if any(id <= 0 for id in v):
            raise ValueError("ID必须为正整数")
        return v

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        allowed_formats = {"xlsx", "csv", "json"}
        if v not in allowed_formats:
            raise ValueError(f"不支持的导出格式: {v}")
        return v


@router.post("/update")
async def batch_update(
    request: BatchUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """批量更新（仅管理员）"""
    require_admin(current_user)
    try:
        result = await batch_service.batch_update(
            table_name=request.table_name, ids=request.ids, updates=request.updates
        )
        return result
    except ValidationError:
        # 验证错误直接抛出，让全局处理器处理
        raise
    except DatabaseError:
        # 数据库错误直接抛出
        raise
    except Exception as e:
        # 未预期的错误，记录详细日志
        logger.error(f"批量更新未预期错误: {e}", exc_info=True)
        raise BusinessError("批量更新失败，请稍后重试")


@router.post("/delete")
async def batch_delete(
    request: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
):
    """批量删除（仅管理员）"""
    require_admin(current_user)
    try:
        result = await batch_service.batch_delete(
            table_name=request.table_name,
            ids=request.ids,
            soft_delete=request.soft_delete,
        )
        return result
    except ValidationError:
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"批量删除未预期错误: {e}", exc_info=True)
        raise BusinessError("批量删除失败，请稍后重试")


@router.post("/export")
async def batch_export(
    request: BatchExportRequest,
    current_user: User = Depends(get_current_user),
):
    """批量导出（仅管理员）"""
    require_admin(current_user)
    try:
        result = await batch_service.batch_export(table_name=request.table_name, ids=request.ids, format=request.format)
        return result
    except ValidationError:
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"批量导出未预期错误: {e}", exc_info=True)
        raise BusinessError("批量导出失败，请稍后重试")


@router.post("/validate")
async def validate_batch(
    table_name: str = Query(..., description="表名"),
    ids: List[int] = Query(..., description="ID列表"),
    current_user: User = Depends(get_current_user),
):
    """验证批量操作"""
    try:
        result = await batch_service.validate_batch(table_name=table_name, ids=ids)
        return result
    except ValidationError:
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"验证批量操作未预期错误: {e}", exc_info=True)
        raise BusinessError("验证批量操作失败，请稍后重试")


@router.get("/status")
async def get_batch_status(
    current_user: User = Depends(get_current_user),
):
    """
    获取批量操作状态
    """
    return {
        "success": True,
        "data": {"status": "idle", "pending_tasks": 0, "completed_tasks": 0, "message": "批量操作服务正常"},
    }
