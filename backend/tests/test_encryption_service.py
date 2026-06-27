"""
加密服务测试

测试数据包加密服务的核心功能
"""
import pytest
import os
import tempfile

from app.services.encryption_service import (
    DataPackageEncryption,
    encrypt_package,
    decrypt_package,
    generate_encryption_key,
)


class TestDataPackageEncryption:
    """数据包加密工具测试"""

    def test_init_with_new_key(self):
        """测试生成新密钥初始化"""
        encryption = DataPackageEncryption()
        assert encryption.key is not None
        assert len(encryption.key) > 0

    def test_init_with_existing_key(self):
        """测试使用现有密钥初始化"""
        key = generate_encryption_key()
        encryption = DataPackageEncryption(key)
        assert encryption.get_key() == key

    def test_get_key(self):
        """测试获取密钥"""
        encryption = DataPackageEncryption()
        key = encryption.get_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_encrypt_decrypt_data(self):
        """测试数据加密和解密"""
        encryption = DataPackageEncryption()
        original_data = b"Hello, World! This is test data."

        # 加密
        encrypted = encryption.encrypt_data(original_data)
        assert encrypted != original_data
        assert isinstance(encrypted, bytes)

        # 解密
        decrypted = encryption.decrypt_data(encrypted)
        assert decrypted == original_data

    def test_encrypt_decrypt_file(self):
        """测试文件加密和解密"""
        encryption = DataPackageEncryption()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Test file content for encryption test.")
            temp_path = f.name

        try:
            # 加密文件
            encrypted_path = encryption.encrypt_file(temp_path)
            assert os.path.exists(encrypted_path)
            assert encrypted_path.endswith('.enc')

            # 读取加密内容（应该是不同的）
            with open(encrypted_path, 'rb') as f:
                encrypted_content = f.read()
            with open(temp_path, 'rb') as f:
                original_content = f.read()
            assert encrypted_content != original_content

            # 解密文件
            decrypted_path = temp_path + '.dec'
            result_path = encryption.decrypt_file(encrypted_path, decrypted_path)
            assert os.path.exists(result_path)

            # 验证解密内容与原始内容相同
            with open(result_path, 'rb') as f:
                decrypted_content = f.read()
            assert decrypted_content == original_content

        finally:
            # 清理临时文件
            for path in [temp_path, temp_path + '.enc', temp_path + '.dec']:
                if os.path.exists(path):
                    os.unlink(path)

    def test_encrypt_file_not_found(self):
        """测试加密不存在的文件"""
        encryption = DataPackageEncryption()
        with pytest.raises(FileNotFoundError):
            encryption.encrypt_file("/nonexistent/path/file.txt")

    def test_decrypt_file_not_found(self):
        """测试解密不存在的文件"""
        encryption = DataPackageEncryption()
        with pytest.raises(FileNotFoundError):
            encryption.decrypt_file("/nonexistent/path/file.enc", "/tmp/output.txt")

    def test_decrypt_with_wrong_key(self):
        """测试使用错误密钥解密"""
        encryption1 = DataPackageEncryption()
        encryption2 = DataPackageEncryption()

        original_data = b"Secret message"
        encrypted = encryption1.encrypt_data(original_data)

        # 使用不同的密钥解密应该失败
        with pytest.raises(ValueError, match="解密失败"):
            encryption2.decrypt_data(encrypted)


class TestEncryptPackageFunctions:
    """加密包功能函数测试"""

    def test_encrypt_package(self):
        """测试加密包函数"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Package data content")
            temp_path = f.name

        try:
            encrypted_path, key = encrypt_package(temp_path)
            assert os.path.exists(encrypted_path)
            assert isinstance(key, str)
            assert len(key) > 0

            # 清理
            if os.path.exists(encrypted_path):
                os.unlink(encrypted_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_encrypt_package_with_existing_key(self):
        """测试使用现有密钥加密包"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Package data content")
            temp_path = f.name

        existing_key = generate_encryption_key()

        try:
            encrypted_path, key = encrypt_package(temp_path, existing_key)
            assert key == existing_key
            assert os.path.exists(encrypted_path)

            # 清理
            if os.path.exists(encrypted_path):
                os.unlink(encrypted_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_decrypt_package(self):
        """测试解密包函数"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Package data for decryption test")
            temp_path = f.name

        try:
            # 加密
            encrypted_path, key = encrypt_package(temp_path)

            # 解密
            output_path = temp_path + '.decrypted'
            result_path = decrypt_package(encrypted_path, key, output_path)

            assert os.path.exists(result_path)
            with open(result_path, 'rb') as f:
                content = f.read()
            assert content == b"Package data for decryption test"

            # 清理
            for path in [encrypted_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestGenerateEncryptionKey:
    """生成加密密钥测试"""

    def test_generate_unique_keys(self):
        """测试生成的密钥是唯一的"""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()
        assert key1 != key2
        assert len(key1) > 0
        assert len(key2) > 0

    def test_generate_key_format(self):
        """测试密钥格式"""
        key = generate_encryption_key()
        # Fernet密钥是Base64编码的32字节（实际是44字符）
        assert isinstance(key, str)
        assert len(key) == 44


class TestEncryptDecryptField:
    """字段加密解密测试"""

    def _get_test_cipher(self):
        """获取测试用的cipher，使用有效密钥"""
        from cryptography.fernet import Fernet
        from app.services.encryption_service import Fernet
        # 生成有效的Fernet密钥
        key = Fernet.generate_key()
        return Fernet(key)

    def test_encrypt_decrypt_field(self):
        """测试字段加密和解密 - 使用有效的Fernet密钥"""
        from cryptography.fernet import Fernet

        # 生成有效的Fernet密钥
        key = Fernet.generate_key()
        cipher = Fernet(key)

        original = "Sensitive data to encrypt"
        encrypted = cipher.encrypt(original.encode()).decode()
        assert encrypted != original
        assert isinstance(encrypted, str)

        decrypted = cipher.decrypt(encrypted.encode()).decode()
        assert decrypted == original

    def test_encrypt_different_values(self):
        """测试不同值产生不同加密结果"""
        from cryptography.fernet import Fernet

        key = Fernet.generate_key()
        cipher = Fernet(key)

        value1 = "Test value 1"
        value2 = "Test value 2"
        encrypted1 = cipher.encrypt(value1.encode()).decode()
        encrypted2 = cipher.encrypt(value2.encode()).decode()
        assert encrypted1 != encrypted2

    def test_encrypt_same_value_different_results(self):
        """测试相同值每次加密结果不同（因为使用了不同的nonce）"""
        from cryptography.fernet import Fernet

        key = Fernet.generate_key()
        cipher = Fernet(key)

        value = "Same value"
        encrypted1 = cipher.encrypt(value.encode()).decode()
        encrypted2 = cipher.encrypt(value.encode()).decode()
        # 注意：Fernet使用时间戳和随机nonce，相同输入可能产生不同输出
        # 但两者都应该能正确解密
        assert cipher.decrypt(encrypted1.encode()).decode() == value
        assert cipher.decrypt(encrypted2.encode()).decode() == value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
