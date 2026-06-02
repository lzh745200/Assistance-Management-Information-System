"""监控子模块"""

from fastapi import APIRouter
from .metrics import router as metrics_router
from .secrets import router as secrets_router
from .data_tier import router as data_tier_router

# 组合路由供 api/v1/__init__.py 加载
router = APIRouter()
router.include_router(metrics_router)
router.include_router(secrets_router)
router.include_router(data_tier_router)

__all__ = ["metrics", "secrets", "data_tier", "router"]
