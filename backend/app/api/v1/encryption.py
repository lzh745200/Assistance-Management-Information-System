"""数据库加密管理API"""

import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.system_config import get_system_config, set_system_config
from app.core.database import get_db
from app.core.permission_utils import require_admin
from app.core.security import get_current_user
from app.models.system_config import SystemConfig
from app.services.password_encryption_service import PasswordEncryptionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/encryption", tags=["数据库加密"])

# 加密配置键名
_CONFIG_KEY_ENABLED = "encryption_enabled"
_CONFIG_KEY_SALT = "encryption_salt"
_CONFIG_KEY_ITERATIONS = "encryption_iterations"
_CONFIG_KEY_VERIFY_HASH = "encryption_verify_hash"


class InitializeEncryptionRequest(BaseModel):
    password: str
    confirm_password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class DisableEncryptionRequest(BaseModel):
    password: str


def _verify_encryption_password(db: Session, password: str) -> None:
    """验证加密密码是否正确"""
    salt_hex = get_system_config(db, _CONFIG_KEY_SALT)
    if not salt_hex:
        raise HTTPException(status_code=400, detail="加密未初始化")

    iterations = int(
        get_system_config(db, _CONFIG_KEY_ITERATIONS) or PasswordEncryptionService.DEFAULT_ITERATIONS
    )
    salt = bytes.fromhex(salt_hex)
    key = PasswordEncryptionService.derive_key(password, salt, iterations)

    stored_hash = get_system_config(db, _CONFIG_KEY_VERIFY_HASH)
    if stored_hash:
        computed_hash = hashlib.sha256(key).hexdigest()
        if computed_hash != stored_hash:
            raise HTTPException(status_code=400, detail="密码不正确")
    else:
        raise HTTPException(status_code=400, detail="加密验证数据不完整，请联系管理员")


@router.post("/initialize")
async def initialize_encryption(
    request: InitializeEncryptionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """初始化数据库加密"""
    require_admin(current_user, "仅管理员可管理加密设置")

    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")

    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    # 检查是否已初始化
    if get_system_config(db, _CONFIG_KEY_ENABLED) == "true":
        raise HTTPException(status_code=400, detail="加密已初始化，请使用修改密码功能")

    # 生成盐值
    salt = PasswordEncryptionService.generate_salt()
    salt_hex = salt.hex()
    iterations = PasswordEncryptionService.DEFAULT_ITERATIONS

    # 生成验证哈希
    verify_key = PasswordEncryptionService.derive_key(request.password, salt, iterations)
    verify_hash = hashlib.sha256(verify_key).hexdigest()

    # 存储配置（不存储密码本身，只存储派生参数）
    set_system_config(db, _CONFIG_KEY_ENABLED, "true", "数据库加密已启用")
    set_system_config(db, _CONFIG_KEY_SALT, salt_hex, "加密盐值")
    set_system_config(db, _CONFIG_KEY_ITERATIONS, str(iterations), "PBKDF2迭代次数")
    set_system_config(db, _CONFIG_KEY_VERIFY_HASH, verify_hash, "加密验证哈希")

    logger.info("数据库加密已初始化")
    return {"success": True, "message": "数据库加密已启用"}


@router.post("/change-password")
async def change_encryption_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """修改加密密码（验证旧密码后更新派生参数）"""
    require_admin(current_user, "仅管理员可管理加密设置")

    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")

    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")

    # 验证旧密码
    _verify_encryption_password(db, request.old_password)

    # 重新生成盐值和验证哈希
    salt = PasswordEncryptionService.generate_salt()
    salt_hex = salt.hex()
    iterations = PasswordEncryptionService.DEFAULT_ITERATIONS

    verify_key = PasswordEncryptionService.derive_key(request.new_password, salt, iterations)
    verify_hash = hashlib.sha256(verify_key).hexdigest()

    set_system_config(db, _CONFIG_KEY_SALT, salt_hex)
    set_system_config(db, _CONFIG_KEY_ITERATIONS, str(iterations))
    set_system_config(db, _CONFIG_KEY_VERIFY_HASH, verify_hash)

    logger.info("加密密码参数已更新")
    return {"success": True, "message": "加密密码已更新"}


@router.get("/status")
async def get_encryption_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取加密状态"""
    enabled = get_system_config(db, _CONFIG_KEY_ENABLED)
    salt = get_system_config(db, _CONFIG_KEY_SALT)
    iterations = get_system_config(db, _CONFIG_KEY_ITERATIONS)

    status = {
        "is_enabled": enabled == "true",
        "has_salt": salt is not None and len(salt) > 0,
        "iterations": int(iterations) if iterations else PasswordEncryptionService.DEFAULT_ITERATIONS,
    }
    return {"success": True, "data": status}


@router.post("/disable")
async def disable_encryption(
    request: DisableEncryptionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """禁用数据库加密"""
    require_admin(current_user, "仅管理员可管理加密设置")

    # 验证密码
    _verify_encryption_password(db, request.password)

    # 清除加密配置
    for key in [_CONFIG_KEY_ENABLED, _CONFIG_KEY_SALT, _CONFIG_KEY_ITERATIONS, _CONFIG_KEY_VERIFY_HASH]:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            db.delete(config)
    db.commit()

    logger.info("数据库加密已禁用")
    return {"success": True, "message": "数据库加密已禁用"}
