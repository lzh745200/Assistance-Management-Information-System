"""
数据同步加密服务
支持基于密码的加密和自定义 .rrs 文件格式
"""

import hashlib
import json
import struct
from typing import Dict, Any, Tuple
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64


class DataSyncEncryptionService:
    """数据同步加密服务"""

    # .rrs 文件格式魔数
    MAGIC_NUMBER = b"RRS\x00"
    VERSION = b"1.0"

    def __init__(self):
        self.backend = default_backend()

    def derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """
        从密码派生加密密钥

        Args:
            password: 用户密码
            salt: 盐值（16字节）

        Returns:
            32字节的加密密钥
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend,
        )
        key = kdf.derive(password.encode("utf-8"))
        return base64.urlsafe_b64encode(key)

    def create_export_package(self, data: Dict[str, Any], metadata: Dict[str, Any], password: str) -> bytes:
        """
        创建加密导出包

        文件格式:
        - 魔数 (4字节): RRS\x00
        - 版本 (3字节): 1.0
        - 盐值 (16字节): 随机生成
        - 元数据长度 (4字节): 大端序整数
        - 加密的元数据 (变长)
        - 加密的数据 (变长)
        - SHA256校验和 (32字节)

        Args:
            data: 要导出的数据
            metadata: 元数据
            password: 加密密码

        Returns:
            加密后的字节数据
        """
        # 生成随机盐值
        import os

        salt = os.urandom(16)

        # 从密码派生密钥
        key = self.derive_key_from_password(password, salt)
        cipher = Fernet(key)

        # 序列化元数据和数据
        metadata_json = json.dumps(metadata, ensure_ascii=False).encode("utf-8")
        data_json = json.dumps(data, ensure_ascii=False).encode("utf-8")

        # 加密元数据和数据
        encrypted_metadata = cipher.encrypt(metadata_json)
        encrypted_data = cipher.encrypt(data_json)

        # 构建文件内容（不包含校验和）
        content = bytearray()
        content.extend(self.MAGIC_NUMBER)
        content.extend(self.VERSION)
        content.extend(salt)
        content.extend(struct.pack(">I", len(encrypted_metadata)))
        content.extend(encrypted_metadata)
        content.extend(encrypted_data)

        # 计算校验和
        checksum = hashlib.sha256(bytes(content)).digest()

        # 添加校验和
        content.extend(checksum)

        return bytes(content)

    def parse_import_package(self, package_bytes: bytes, password: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        解析导入包

        Args:
            package_bytes: 加密的包数据
            password: 解密密码

        Returns:
            (metadata, data) 元组

        Raises:
            ValueError: 文件格式错误或密码错误
        """
        # 验证最小长度
        min_length = 4 + 3 + 16 + 4 + 32  # 魔数 + 版本 + 盐 + 元数据长度 + 校验和
        if len(package_bytes) < min_length:
            raise ValueError("文件格式错误: 文件太小")

        offset = 0

        # 验证魔数
        magic = package_bytes[offset: offset + 4]
        if magic != self.MAGIC_NUMBER:
            raise ValueError("文件格式错误: 不是有效的 .rrs 文件")
        offset += 4

        # 验证版本
        version = package_bytes[offset: offset + 3]
        if version != self.VERSION:
            raise ValueError(f"文件版本不支持: {version.decode('utf-8', errors='ignore')}")
        offset += 3

        # 提取盐值
        salt = package_bytes[offset: offset + 16]
        offset += 16

        # 提取元数据长度
        metadata_length = struct.unpack(">I", package_bytes[offset: offset + 4])[0]
        offset += 4

        # 验证校验和
        checksum_start = len(package_bytes) - 32
        stored_checksum = package_bytes[checksum_start:]
        content_to_verify = package_bytes[:checksum_start]
        calculated_checksum = hashlib.sha256(content_to_verify).digest()

        if stored_checksum != calculated_checksum:
            raise ValueError("文件完整性校验失败")

        # 提取加密的元数据和数据
        encrypted_metadata = package_bytes[offset: offset + metadata_length]
        offset += metadata_length
        encrypted_data = package_bytes[offset:checksum_start]

        # 从密码派生密钥
        try:
            key = self.derive_key_from_password(password, salt)
            cipher = Fernet(key)

            # 解密元数据和数据
            metadata_json = cipher.decrypt(encrypted_metadata)
            data_json = cipher.decrypt(encrypted_data)

            # 反序列化
            metadata = json.loads(metadata_json.decode("utf-8"))
            data = json.loads(data_json.decode("utf-8"))

            return metadata, data

        except Exception as e:
            raise ValueError(f"解密失败，可能是密码错误: {str(e)}")

    def calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件的 SHA256 哈希值

        Args:
            file_path: 文件路径

        Returns:
            十六进制哈希字符串
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def hash_password(self, password: str) -> str:
        """
        对密码进行哈希（用于存储）

        Args:
            password: 原始密码

        Returns:
            哈希后的密码
        """
        import bcrypt

        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        验证密码

        Args:
            password: 原始密码
            hashed: 哈希后的密码

        Returns:
            是否匹配
        """
        import bcrypt

        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# 创建全局实例
data_sync_encryption_service = DataSyncEncryptionService()
