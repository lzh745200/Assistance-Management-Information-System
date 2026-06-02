"""
测试 - app.services.data_sync_encryption_service
覆盖率目标: 100%
"""
import pytest
import os
import json
import struct
import hashlib
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

class TestDataSyncEncryptionService:
    """测试 DataSyncEncryptionService"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        from app.services.data_sync_encryption_service import DataSyncEncryptionService
        return DataSyncEncryptionService()

    def test_service_creation(self, service):
        """测试服务创建"""
        assert service is not None
        assert service.MAGIC_NUMBER == b"RRS\x00"
        assert service.VERSION == b"1.0"
        assert service.backend is not None

    def test_derive_key_from_password(self, service):
        """测试从密码派生密钥"""
        salt = os.urandom(16)
        password = "test_password"

        key = service.derive_key_from_password(password, salt)

        assert isinstance(key, bytes)
        assert len(key) > 0

        # 相同密码和盐应该产生相同密钥
        key2 = service.derive_key_from_password(password, salt)
        assert key == key2

        # 不同密码应该产生不同密钥
        key3 = service.derive_key_from_password("different_password", salt)
        assert key != key3

    def test_create_export_package(self, service):
        """测试创建导出包"""
        data = {"users": [{"id": 1, "name": "Test"}]}
        metadata = {"version": "1.0", "timestamp": "2024-01-01"}
        password = "test_password"

        package = service.create_export_package(data, metadata, password)

        assert isinstance(package, bytes)
        assert len(package) > 0

        # 验证魔数
        assert package[:4] == b"RRS\x00"

        # 验证版本
        assert package[4:7] == b"1.0"

        # 验证盐值存在（16字节）
        salt = package[7:23]
        assert len(salt) == 16

        # 验证元数据长度（4字节大端序）
        metadata_length = struct.unpack(">I", package[23:27])[0]
        assert metadata_length > 0

    def test_parse_import_package_success(self, service):
        """测试解析导入包成功"""
        data = {"users": [{"id": 1, "name": "Test"}]}
        metadata = {"version": "1.0", "timestamp": "2024-01-01"}
        password = "test_password"

        # 创建包
        package = service.create_export_package(data, metadata, password)

        # 解析包
        parsed_metadata, parsed_data = service.parse_import_package(package, password)

        assert parsed_metadata == metadata
        assert parsed_data == data

    def test_parse_import_package_wrong_password(self, service):
        """测试解析导入包 - 错误密码"""
        data = {"users": [{"id": 1, "name": "Test"}]}
        metadata = {"version": "1.0"}
        password = "correct_password"

        package = service.create_export_package(data, metadata, password)

        # 使用错误密码解析
        with pytest.raises(ValueError, match="解密失败"):
            service.parse_import_package(package, "wrong_password")

    def test_parse_import_package_too_small(self, service):
        """测试解析导入包 - 文件太小"""
        with pytest.raises(ValueError, match="文件太小"):
            service.parse_import_package(b"too_small", "password")

    def test_parse_import_package_invalid_magic(self, service):
        """测试解析导入包 - 无效魔数"""
        # 创建一个无效魔数的包
        invalid_package = b"INVALID" + b"\x00" * 100
        with pytest.raises(ValueError, match="不是有效的 .rrs 文件"):
            service.parse_import_package(invalid_package, "password")

    def test_parse_import_package_invalid_version(self, service):
        """测试解析导入包 - 无效版本"""
        # 创建带有正确魔数但错误版本的包
        invalid_package = b"RRS\x00" + b"9.9" + b"\x00" * 100
        with pytest.raises(ValueError, match="文件版本不支持"):
            service.parse_import_package(invalid_package, "password")

    def test_parse_import_package_checksum_mismatch(self, service):
        """测试解析导入包 - 校验和不匹配"""
        # 创建一个有效的包但修改部分内容
        data = {"test": "data"}
        metadata = {"version": "1.0"}
        password = "password"

        package = service.create_export_package(data, metadata, password)

        # 修改包内容（破坏校验和）
        modified_package = package[:-32] + b"\x00" * 32

        with pytest.raises(ValueError, match="文件完整性校验失败"):
            service.parse_import_package(modified_package, password)

    def test_calculate_file_hash(self, service, tmp_path):
        """测试计算文件哈希"""
        # 创建临时文件
        test_file = tmp_path / "test_file.txt"
        test_content = b"test content for hashing"
        test_file.write_bytes(test_content)

        # 计算哈希
        file_hash = service.calculate_file_hash(str(test_file))

        # 验证哈希格式
        assert isinstance(file_hash, str)
        assert len(file_hash) == 64  # SHA256 十六进制字符串长度

        # 验证哈希值正确
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert file_hash == expected_hash

    def test_calculate_file_hash_empty_file(self, service, tmp_path):
        """测试计算空文件哈希"""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        file_hash = service.calculate_file_hash(str(test_file))
        expected_hash = hashlib.sha256(b"").hexdigest()
        assert file_hash == expected_hash

    def test_calculate_file_hash_large_file(self, service, tmp_path):
        """测试计算大文件哈希（测试分块读取）"""
        test_file = tmp_path / "large.bin"
        # 创建大于 4096 字节的文件
        test_content = b"x" * 10000
        test_file.write_bytes(test_content)

        file_hash = service.calculate_file_hash(str(test_file))
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert file_hash == expected_hash

    def test_hash_password(self, service):
        """测试密码哈希"""
        password = "test_password_123"

        hashed = service.hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

        # 相同密码应该产生不同哈希（因为有随机盐）
        hashed2 = service.hash_password(password)
        assert hashed != hashed2

        # 但两者都应该验证成功
        assert service.verify_password(password, hashed)
        assert service.verify_password(password, hashed2)

    def test_verify_password_correct(self, service):
        """测试验证密码 - 正确密码"""
        password = "correct_password"
        hashed = service.hash_password(password)

        assert service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, service):
        """测试验证密码 - 错误密码"""
        password = "correct_password"
        hashed = service.hash_password(password)

        assert service.verify_password("wrong_password", hashed) is False

    def test_verify_password_different_passwords(self, service):
        """测试验证不同密码"""
        password1 = "password_one"
        password2 = "password_two"

        hashed1 = service.hash_password(password1)
        hashed2 = service.hash_password(password2)

        assert service.verify_password(password1, hashed1) is True
        assert service.verify_password(password2, hashed2) is True
        assert service.verify_password(password1, hashed2) is False
        assert service.verify_password(password2, hashed1) is False

class TestGlobalInstance:
    """测试全局实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        from app.services.data_sync_encryption_service import data_sync_encryption_service
        assert data_sync_encryption_service is not None

    def test_global_instance_is_service(self):
        """测试全局实例是服务类型"""
        from app.services.data_sync_encryption_service import (
            data_sync_encryption_service, DataSyncEncryptionService
        )
        assert isinstance(data_sync_encryption_service, DataSyncEncryptionService)
