"""
配置包管理 API
"""
from fastapi import APIRouter

router = APIRouter(prefix="/system/config-packages", tags=["配置包管理"])


@router.get("")
async def get_config_packages():
    """获取可用配置包列表"""
    return {"packages": [], "message": "配置包功能开发中"}
