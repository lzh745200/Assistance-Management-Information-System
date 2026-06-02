"""
导入导出路由子模块
聚合 export / async_export / import_data / chunked_upload 路由
"""

from fastapi import APIRouter

from .async_export import router as async_export_router
from .chunked_upload import router as chunked_upload_router
from .export import router as export_router
from .import_data import router as import_data_router

router = APIRouter()

router.include_router(export_router)
router.include_router(async_export_router)
router.include_router(import_data_router)
router.include_router(chunked_upload_router)

__all__ = ["router"]
