"""
数据包加密服务
支持数据包的加密和解密
"""

import os
from typing import Optional

from cryptography.fernet import Fernet


class DataPackageEncryption:
    """数据包加密工具"""

    def __init__(self, key: Optional[str] = None):
        """
        初始化加密工具

        Args:
            key: 加密密钥（Base64编码的字符串），如果为None则生成新密钥
        """
        if key:
            self.key = key.encode() if isinstance(key, str) else key
            self.cipher = Fernet(self.key)
        else:
            # 生成新密钥
            self.key = Fernet.generate_key()
            self.cipher = Fernet(self.key)

    def get_key(self) -> str:
        """
        获取加密密钥

        Returns:
            Base64编码的密钥字符串
        """
        return self.key.decode()

    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        加密文件

        Args:
            file_path: 源文件路径
            output_path: 输出文件路径，如果为None则在源文件路径后添加.enc

        Returns:
            加密后的文件路径
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 读取文件内容
        with open(file_path, "rb") as f:
            data = f.read()

        # 加密数据
        encrypted = self.cipher.encrypt(data)

        # 确定输出路径
        if output_path is None:
            output_path = file_path + ".enc"

        # 写入加密文件
        with open(output_path, "wb") as f:
            f.write(encrypted)

        return output_path

    def decrypt_file(self, encrypted_path: str, output_path: str) -> str:
        """
        解密文件

        Args:
            encrypted_path: 加密文件路径
            output_path: 输出文件路径

        Returns:
            解密后的文件路径
        """
        if not os.path.exists(encrypted_path):
            raise FileNotFoundError(f"加密文件不存在: {encrypted_path}")

        # 读取加密文件
        with open(encrypted_path, "rb") as f:
            encrypted = f.read()

        # 解密数据
        try:
            decrypted = self.cipher.decrypt(encrypted)
        except Exception as e:
            raise ValueError(f"解密失败，可能是密钥错误: {str(e)}")

        # 写入解密文件
        with open(output_path, "wb") as f:
            f.write(decrypted)

        return output_path

    def encrypt_data(self, data: bytes) -> bytes:
        """
        加密数据

        Args:
            data: 原始数据

        Returns:
            加密后的数据
        """
        return self.cipher.encrypt(data)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        解密数据

        Args:
            encrypted_data: 加密的数据

        Returns:
            解密后的数据
        """
        try:
            return self.cipher.decrypt(encrypted_data)
        except Exception as e:
            raise ValueError(f"解密失败: {str(e)}")


def generate_encryption_key() -> str:
    """
    生成新的加密密钥

    Returns:
        Base64编码的密钥字符串
    """
    key = Fernet.generate_key()
    return key.decode()


def encrypt_package(package_path: str, key: Optional[str] = None) -> tuple[str, str]:
    """
    加密数据包

    Args:
        package_path: 数据包文件路径
        key: 加密密钥，如果为None则生成新密钥

    Returns:
        (加密文件路径, 加密密钥)
    """
    encryption = DataPackageEncryption(key)
    encrypted_path = encryption.encrypt_file(package_path)
    return encrypted_path, encryption.get_key()


def decrypt_package(encrypted_path: str, key: str, output_path: str) -> str:
    """
    解密数据包

    Args:
        encrypted_path: 加密文件路径
        key: 解密密钥
        output_path: 输出文件路径

    Returns:
        解密后的文件路径
    """
    encryption = DataPackageEncryption(key)
    return encryption.decrypt_file(encrypted_path, output_path)


# 创建全局实例
encryption_service = None  # 需要时动态创建

# 别名导出
EncryptionService = DataPackageEncryption

# 缓存的 Fernet cipher 实例（惰性初始化）
_cipher_cache = None


def _get_cipher() -> Fernet:
    """获取或创建 Fernet cipher 实例（带缓存）。

    密钥优先级：
    1. 环境变量/配置文件中的 ENCRYPTION_KEY
    2. 运行时密钥存储中的持久化密钥（跨重启保持）
    3. 新生成并持久化到运行时密钥存储的密钥
    """
    global _cipher_cache

    if _cipher_cache is not None:
        return _cipher_cache

    from app.core.config import settings

    key = getattr(settings, "ENCRYPTION_KEY", None)

    if key and key.strip():
        try:
            key_bytes = key.encode() if isinstance(key, str) else key
            _cipher_cache = Fernet(key_bytes)
            return _cipher_cache
        except ValueError:
            pass

    # 尝试从运行时密钥存储加载持久化密钥
    import logging
    _log = logging.getLogger(__name__)

    try:
        from app.utils.runtime_secrets import get_or_create_secret
        persisted_key = get_or_create_secret(
            "ENCRYPTION_FERNET_KEY",
            generate=lambda: Fernet.generate_key().decode()
        )
        _cipher_cache = Fernet(persisted_key.encode())
        _log.info("已从运行时密钥存储加载持久化加密密钥")
        return _cipher_cache
    except Exception as e:
        _log.error("无法加载或创建持久化加密密钥: %s", e)
        raise RuntimeError(
            "加密密钥初始化失败：无法加载或创建持久化加密密钥。"
            "请检查 runtime_secrets.json 文件权限和磁盘空间。"
        ) from e


def _reset_cipher_cache():
    """重置 cipher 缓存（用于测试）"""
    global _cipher_cache
    _cipher_cache = None


def encrypt_field(data: str) -> str:
    """
    加密单个字段数据

    Args:
        data: 原始字符串数据

    Returns:
        加密后的字符串（Base64编码）
    """
    cipher = _get_cipher()
    encrypted = cipher.encrypt(data.encode() if isinstance(data, str) else data)
    return encrypted.decode()


def decrypt_field(encrypted_data: str) -> str:
    """
    解密单个字段数据

    Args:
        encrypted_data: 加密后的字符串（Base64编码）

    Returns:
        解密后的原始字符串
    """
    cipher = _get_cipher()
    decrypted = cipher.decrypt(encrypted_data.encode() if isinstance(encrypted_data, str) else encrypted_data)
    return decrypted.decode()
