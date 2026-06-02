"""
认证与用户管理路由子模块
聚合 auth / users / user_management / rbac 路由
"""

from fastapi import APIRouter

from .auth import create_access_token
from .auth import router as auth_router
from .rbac import router as rbac_router
from .user_management import router as user_management_router
from .users import router as users_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(user_management_router)
router.include_router(rbac_router)

__all__ = ["router", "create_access_token"]
