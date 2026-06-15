"""
双因素认证服务
"""

import logging
import secrets
from base64 import b64encode
from datetime import timezone, datetime
from io import BytesIO
from typing import List

import pyotp
import qrcode
from sqlalchemy.orm import Session

from app.models.two_factor_auth import TwoFactorAuth
from app.models.user import User
from app.services.encryption_service import decrypt_field, encrypt_field

logger = logging.getLogger(__name__)


class TwoFactorService:
    """双因素认证服务"""

    @staticmethod
    def generate_secret() -> str:
        """生成TOTP密钥"""
        return pyotp.random_base32()

    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """
        生成备用恢复码

        Args:
            count: 生成数量

        Returns:
            恢复码列表
        """
        codes = []
        for _ in range(count):
            # 生成8位数字恢复码
            code = "".join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(code)
        return codes

    @staticmethod
    def generate_qr_code(secret: str, user_email: str, issuer: str = "帮扶管理信息系统") -> str:
        """
        生成TOTP二维码

        Args:
            secret: TOTP密钥
            user_email: 用户邮箱
            issuer: 发行者名称

        Returns:
            Base64编码的二维码图片
        """
        # 生成TOTP URI
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=user_email, issuer_name=issuer)

        # 生成二维码
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为Base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """
        验证TOTP令牌

        Args:
            secret: TOTP密钥
            token: 用户输入的6位数字令牌

        Returns:
            是否验证成功
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # 允许前后30秒的时间窗口
        except Exception as e:
            logger.error(f"TOTP验证失败: {e}")
            return False

    @staticmethod
    def enable_two_factor(db: Session, user: User) -> dict:
        """
        为用户启用双因素认证

        Args:
            db: 数据库会话
            user: 用户对象

        Returns:
            包含密钥和二维码的字典
        """
        # 检查是否已启用
        existing = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id).first()
        if existing and existing.enabled:
            raise ValueError("双因素认证已启用")

        # 生成密钥和备用码
        secret = TwoFactorService.generate_secret()
        backup_codes = TwoFactorService.generate_backup_codes()

        # 加密存储密钥
        encrypted_secret = encrypt_field(secret)

        # 创建或更新记录
        if existing:
            existing.secret_key = encrypted_secret
            existing.backup_codes = backup_codes
            existing.enabled = False  # 需要验证后才启用
            existing.verified_at = None
            two_factor = existing
        else:
            two_factor = TwoFactorAuth(
                user_id=user.id,
                secret_key=encrypted_secret,
                backup_codes=backup_codes,
                enabled=False,
            )
            db.add(two_factor)

        db.commit()
        db.refresh(two_factor)

        # 生成二维码
        qr_code = TwoFactorService.generate_qr_code(secret, user.email)

        return {"secret": secret, "qr_code": qr_code, "backup_codes": backup_codes}

    @staticmethod
    def verify_and_enable(db: Session, user: User, token: str) -> bool:
        """
        验证TOTP令牌并启用双因素认证

        Args:
            db: 数据库会话
            user: 用户对象
            token: TOTP令牌

        Returns:
            是否验证成功
        """
        two_factor = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id).first()
        if not two_factor:
            raise ValueError("未找到双因素认证配置")

        # 解密密钥
        secret = decrypt_field(two_factor.secret_key)

        # 验证令牌
        if TwoFactorService.verify_totp(secret, token):
            two_factor.enabled = True
            two_factor.verified_at = datetime.now(timezone.utc)
            db.commit()
            return True

        return False

    @staticmethod
    def verify_login(db: Session, user: User, token: str) -> bool:
        """
        验证登录时的TOTP令牌

        Args:
            db: 数据库会话
            user: 用户对象
            token: TOTP令牌或备用码

        Returns:
            是否验证成功
        """
        two_factor = (
            db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id, TwoFactorAuth.enabled is True).first()
        )

        if not two_factor:
            return False

        # 先尝试TOTP验证
        secret = decrypt_field(two_factor.secret_key)
        if TwoFactorService.verify_totp(secret, token):
            return True

        # 尝试备用码验证
        if token in two_factor.backup_codes:
            # 使用后移除备用码
            two_factor.backup_codes.remove(token)
            db.commit()
            logger.info(f"用户 {user.username} 使用备用码登录")
            return True

        return False

    @staticmethod
    def disable_two_factor(db: Session, user: User):
        """
        禁用双因素认证

        Args:
            db: 数据库会话
            user: 用户对象
        """
        two_factor = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id).first()
        if two_factor:
            db.delete(two_factor)
            db.commit()
            logger.info(f"用户 {user.username} 已禁用双因素认证")

    @staticmethod
    def is_enabled(db: Session, user: User) -> bool:
        """
        检查用户是否启用了双因素认证

        Args:
            db: 数据库会话
            user: 用户对象

        Returns:
            是否启用
        """
        two_factor = (
            db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id, TwoFactorAuth.enabled is True).first()
        )
        return two_factor is not None
