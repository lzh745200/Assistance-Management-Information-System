"""AES-256-GCM 加密模块 — 军事级离线加密.

每个加密操作使用随机 12 字节 nonce，密文格式: [12B nonce][ciphertext+tag]
密钥可由调用方传入或自动生成，符合零信任安全标准。
"""
import os as _os
from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AESGCMCipher:
    """AES-256-GCM 加解密器.

    Usage:
        cipher = AESGCMCipher()             # 自动生成密钥
        cipher = AESGCMCipher(key=raw32)     # 使用已有密钥
        ct = cipher.encrypt(b"data")
        pt = cipher.decrypt(ct)
    """

    def __init__(self, key: Optional[bytes] = None):
        self._key = key if key and len(key) == 32 else _os.urandom(32)
        self._aesgcm = AESGCM(self._key)

    @property
    def key(self) -> bytes:
        return self._key

    @staticmethod
    def generate_key() -> bytes:
        """生成 256 位随机密钥."""
        return AESGCM.generate_key(bit_length=256)

    def encrypt(self, plaintext: bytes) -> bytes:
        """加密字节数据.

        Returns:
            [12B nonce][ciphertext + 16B auth tag]
        """
        nonce = _os.urandom(12)
        ct = self._aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ct

    def decrypt(self, ciphertext: bytes) -> bytes:
        """解密密文，自动验证完整性（GCM认证标签）.

        Raises:
            ValueError: 密钥错误或数据被篡改
        """
        if len(ciphertext) < 28:  # 12 nonce + min 16 tag
            raise ValueError("密文太短，可能已损坏")
        nonce = ciphertext[:12]
        ct = ciphertext[12:]
        try:
            return self._aesgcm.decrypt(nonce, ct, None)
        except InvalidTag:
            raise ValueError("解密失败：密钥错误或数据被篡改") from None

    # ── 便捷方法 ──

    def encrypt_string(self, text: str) -> bytes:
        return self.encrypt(text.encode("utf-8"))

    def decrypt_string(self, data: bytes) -> str:
        return self.decrypt(data).decode("utf-8")

    def encrypt_file(self, input_path: str, output_path: str) -> None:
        with open(input_path, "rb") as f:
            plaintext = f.read()
        encrypted = self.encrypt(plaintext)
        with open(output_path, "wb") as f:
            f.write(encrypted)

    def decrypt_file(self, input_path: str, output_path: str) -> None:
        with open(input_path, "rb") as f:
            ct = f.read()
        pt = self.decrypt(ct)
        with open(output_path, "wb") as f:
            f.write(pt)
