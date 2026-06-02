"""
完整测试 - app.services.encryption_service
覆盖率目标: 100%
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from unittest.mock import MagicMock  # auto-added

class TestDataPackageEncryption:
    """测试 DataPackageEncryption 类"""

    def test_encryption_creation_with_key(self):
        """测试使用密钥创建"""
        from app.services.encryption_service import DataPackageEncryption, generate_encryption_key
        key = generate_encryption_key()
        encryption = DataPackageEncryption(key)
        assert encryption is not None
        assert encryption.key is not None

    def test_encryption_creation_without_key(self):
        """测试无密钥创建（生成新密钥）"""
        from app.services.encryption_service import DataPackageEncryption
        encryption = DataPackageEncryption()
        assert encryption is not None
        assert encryption.key is not None

    def test_get_key(self):
        """测试获取密钥"""
        from app.services.encryption_service import DataPackageEncryption
        encryption = DataPackageEncryption()
        key = encryption.get_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_encrypt_decrypt_data(self):
        """测试加密解密数据"""
        from app.services.encryption_service import DataPackageEncryption
        encryption = DataPackageEncryption()
        data = b"test data"
        encrypted = encryption.encrypt_data(data)
        decrypted = encryption.decrypt_data(encrypted)
        assert decrypted == data

    def test_decrypt_data_invalid(self):
        """测试解密无效数据"""
        from app.services.encryption_service import DataPackageEncryption
        encryption = DataPackageEncryption()
        with pytest.raises(ValueError):
            encryption.decrypt_data(b"invalid data")

    def test_encrypt_file_not_found(self):
        """测试加密不存在的文件"""
        from app.services.encryption_service import DataPackageEncryption
        encryption = DataPackageEncryption()
        with pytest.raises(FileNotFoundError):
            encryption.encrypt_file("/nonexistent/file.txt")

    def test_decrypt_file_not_found(self):
        """测试解密不存在的文件"""
        from app.services.encryption_service import DataPackageEncryption
        encryption = DataPackageEncryption()
        with pytest.raises(FileNotFoundError):
            encryption.decrypt_file("/nonexistent/file.enc", "/output/file.txt")

    def test_encrypt_decrypt_file(self, tmp_path):
        """测试加密解密文件"""
        from app.services.encryption_service import DataPackageEncryption
        encryption = DataPackageEncryption()

        # 创建测试文件
        test_file = tmp_path / "test.txt"
        test_content = b"test content"
        test_file.write_bytes(test_content)

        # 加密文件
        encrypted_path = encryption.encrypt_file(str(test_file))
        assert os.path.exists(encrypted_path)

        # 解密文件
        decrypted_path = str(tmp_path / "decrypted.txt")
        encryption.decrypt_file(encrypted_path, decrypted_path)

        # 验证内容
        decrypted_content = Path(decrypted_path).read_bytes()
        assert decrypted_content == test_content

    def test_encrypt_file_with_output_path(self, tmp_path):
        """测试加密文件指定输出路径"""
        from app.services.encryption_service import DataPackageEncryption
        encryption = DataPackageEncryption()

        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")

        output_path = str(tmp_path / "custom.enc")
        result = encryption.encrypt_file(str(test_file), output_path)
        assert result == output_path

    def test_decrypt_file_invalid_key(self, tmp_path):
        """测试解密文件使用错误密钥"""
        from app.services.encryption_service import DataPackageEncryption
        encryption1 = DataPackageEncryption()
        encryption2 = DataPackageEncryption()

        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")

        encrypted_path = encryption1.encrypt_file(str(test_file))

        with pytest.raises(ValueError):
            encryption2.decrypt_file(encrypted_path, str(tmp_path / "out.txt"))

class TestModuleFunctions:
    """测试模块级函数"""

    def test_generate_encryption_key(self):
        """测试生成加密密钥"""
        from app.services.encryption_service import generate_encryption_key
        key = generate_encryption_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_encrypt_decrypt_package(self, tmp_path):
        """测试加密解密包"""
        from app.services.encryption_service import encrypt_package, decrypt_package

        test_file = tmp_path / "package.txt"
        test_file.write_bytes(b"package content")

        encrypted_path, key = encrypt_package(str(test_file))
        assert os.path.exists(encrypted_path)
        assert key is not None

        output_path = str(tmp_path / "decrypted.txt")
        result = decrypt_package(encrypted_path, key, output_path)
        assert result == output_path
        assert Path(output_path).read_bytes() == b"package content"

    def test_encrypt_package_with_key(self, tmp_path):
        """测试使用指定密钥加密包"""
        from app.services.encryption_service import encrypt_package, generate_encryption_key

        test_file = tmp_path / "package.txt"
        test_file.write_bytes(b"content")

        key = generate_encryption_key()
        encrypted_path, returned_key = encrypt_package(str(test_file), key)
        assert returned_key == key

class TestCipherCache:
    """测试 cipher 缓存功能"""

    def test_get_cipher_with_settings_key(self):
        """测试从 settings 获取密钥创建 cipher"""
        from app.services.encryption_service import _get_cipher, _reset_cipher_cache
        from cryptography.fernet import Fernet
        _reset_cipher_cache()

        # Generate a valid Fernet key
        valid_key = Fernet.generate_key().decode()

        # settings is imported locally in _get_cipher from app.core.config
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.ENCRYPTION_KEY = valid_key
            mock_settings.encryption_key = valid_key
            cipher = _get_cipher()
            assert cipher is not None

    def test_get_cipher_with_invalid_key(self):
        """测试从 settings 获取无效密钥时回退到生成新密钥"""
        from app.services.encryption_service import _get_cipher, _reset_cipher_cache
        _reset_cipher_cache()

        with patch('app.core.config.settings') as mock_settings:
            mock_settings.ENCRYPTION_KEY = "invalid_key"
            mock_settings.encryption_key = "invalid_key"
            cipher = _get_cipher()
            assert cipher is not None

    def test_get_cipher_cache(self):
        """测试 cipher 缓存"""
        from app.services.encryption_service import _get_cipher, _reset_cipher_cache
        _reset_cipher_cache()

        cipher1 = _get_cipher()
        cipher2 = _get_cipher()
        assert cipher1 is cipher2

    def test_reset_cipher_cache(self):
        """测试重置 cipher 缓存"""
        from app.services.encryption_service import _get_cipher, _reset_cipher_cache
        _reset_cipher_cache()

        cipher1 = _get_cipher()
        _reset_cipher_cache()
        cipher2 = _get_cipher()
        assert cipher1 is not cipher2

class TestFieldEncryption:
    """测试字段加密功能"""

    def test_encrypt_decrypt_field(self):
        """测试加密解密字段"""
        from app.services.encryption_service import encrypt_field, decrypt_field, _reset_cipher_cache
        _reset_cipher_cache()

        data = "sensitive data"
        encrypted = encrypt_field(data)
        decrypted = decrypt_field(encrypted)
        assert decrypted == data

    def test_encrypt_field_bytes_input(self):
        """测试加密字段 - bytes 输入"""
        from app.services.encryption_service import encrypt_field, _reset_cipher_cache
        _reset_cipher_cache()

        data = b"bytes data"
        encrypted = encrypt_field(data)
        assert isinstance(encrypted, str)

    def test_decrypt_field_bytes_input(self):
        """测试解密字段 - bytes 输入"""
        from app.services.encryption_service import encrypt_field, decrypt_field, _reset_cipher_cache
        _reset_cipher_cache()

        original = "test data"
        encrypted = encrypt_field(original)
        decrypted = decrypt_field(encrypted)
        assert decrypted == original

class TestEncryptionServiceAlias:
    """测试别名导出"""

    def test_encryption_service_alias(self):
        """测试 EncryptionService 别名"""
        from app.services.encryption_service import EncryptionService, DataPackageEncryption
        assert EncryptionService is DataPackageEncryption

    def test_global_instance(self):
        """测试全局实例"""
        from app.services.encryption_service import encryption_service
        assert encryption_service is None
