"""TDD: AES-256-GCM 加密模块测试."""
import pytest
import os
import tempfile


class TestAESGCMCipher:
    """验证 AES-256-GCM 加解密正确性."""

    @pytest.fixture
    def cipher(self):
        from app.services.aes_gcm_cipher import AESGCMCipher
        return AESGCMCipher()

    @pytest.fixture
    def fixed_key_cipher(self):
        from app.services.aes_gcm_cipher import AESGCMCipher
        import secrets
        key = secrets.token_bytes(32)
        return AESGCMCipher(key=key)

    def test_encrypt_decrypt_roundtrip(self, cipher):
        plaintext = b"Hello AES-256-GCM!"
        ciphertext = cipher.encrypt(plaintext)
        assert ciphertext != plaintext
        assert len(ciphertext) > len(plaintext)  # includes nonce + tag
        decrypted = cipher.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_encrypt_string_roundtrip(self, cipher):
        text = "帮扶管理信息系统测试数据"
        encrypted = cipher.encrypt_string(text)
        decrypted = cipher.decrypt_string(encrypted)
        assert decrypted == text

    def test_different_encryptions_produce_different_outputs(self, cipher):
        """相同明文两次加密结果应不同（不同nonce）."""
        ct1 = cipher.encrypt(b"test data")
        ct2 = cipher.encrypt(b"test data")
        assert ct1 != ct2

    def test_tampered_data_rejected(self, fixed_key_cipher):
        """篡改密文应被检测并拒绝."""
        ct = fixed_key_cipher.encrypt(b"important data")
        # 翻转中间某个字节
        tampered = bytearray(ct)
        tampered[len(tampered) // 2] ^= 0xFF
        with pytest.raises(ValueError, match="解密|密钥|篡改|损坏"):
            fixed_key_cipher.decrypt(bytes(tampered))

    def test_wrong_key_cannot_decrypt(self):
        from app.services.aes_gcm_cipher import AESGCMCipher
        import secrets
        c1 = AESGCMCipher(key=secrets.token_bytes(32))
        c2 = AESGCMCipher(key=secrets.token_bytes(32))
        ct = c1.encrypt(b"secret")
        with pytest.raises(ValueError, match="解密|密钥|篡改|损坏"):
            c2.decrypt(ct)

    def test_empty_data(self, cipher):
        ct = cipher.encrypt(b"")
        assert cipher.decrypt(ct) == b""

    def test_large_data(self, cipher):
        data = os.urandom(1024 * 1024)  # 1MB
        ct = cipher.encrypt(data)
        assert cipher.decrypt(ct) == data

    def test_key_generation_is_random(self, cipher):
        key1 = cipher.generate_key()
        key2 = cipher.generate_key()
        assert key1 != key2
        assert len(key1) == 32  # AES-256


class TestEncryptedPackage:
    """验证离线加密数据包生成/解析."""

    def test_create_and_extract_package(self, tmp_path):
        from app.services.encrypted_package import (
            create_encrypted_package,
            extract_encrypted_package,
        )
        data = {
            "villages": [{"id": 1, "name": "幸福村"}],
            "funds": [{"id": 1, "amount": 100000}],
        }
        password = "secure-password-123"
        out_path = tmp_path / "export.rrs"
        create_encrypted_package(data, str(out_path), password)
        assert out_path.exists()
        assert out_path.stat().st_size > 0
        extracted = extract_encrypted_package(str(out_path), password)
        assert extracted == data

    def test_wrong_password_fails(self, tmp_path):
        from app.services.encrypted_package import (
            create_encrypted_package,
            extract_encrypted_package,
        )
        data = {"test": "data"}
        out_path = tmp_path / "test.rrs"
        create_encrypted_package(data, str(out_path), "correct-password")
        with pytest.raises(ValueError):
            extract_encrypted_package(str(out_path), "wrong-password")

    def test_tampered_file_rejected(self, tmp_path):
        from app.services.encrypted_package import (
            create_encrypted_package,
            extract_encrypted_package,
        )
        data = {"test": "data"}
        out_path = tmp_path / "tamper.rrs"
        create_encrypted_package(data, str(out_path), "password")
        # 篡改文件
        with open(out_path, "rb+") as f:
            f.seek(50)
            f.write(b"\xFF" * 10)
        with pytest.raises(ValueError):
            extract_encrypted_package(str(out_path), "password")

    def test_magic_number_preserved(self, tmp_path):
        """验证 .rrs 格式魔数."""
        from app.services.encrypted_package import create_encrypted_package
        data = {"test": "x"}
        out_path = tmp_path / "magic.rrs"
        create_encrypted_package(data, str(out_path), "pass")
        with open(out_path, "rb") as f:
            magic = f.read(4)
        assert magic == b"RRS\x00"


class TestMachineCodeJWT:
    """验证 JWT 机器码绑定."""

    def test_token_contains_machine_code(self):
        from app.core.security import create_access_token_with_machine_code
        token = create_access_token_with_machine_code(
            data={"sub": "admin"},
            machine_code="MACHINE-HASH-ABC123",
        )
        assert token is not None
        assert len(token) > 20

    def test_token_validation_with_matching_machine_code(self):
        from app.core.security import (
            create_access_token_with_machine_code,
            decode_token_with_machine_code,
        )
        mc = "DEVICE-XYZ-456"
        token = create_access_token_with_machine_code(
            data={"sub": "admin"},
            machine_code=mc,
        )
        payload = decode_token_with_machine_code(token, expected_machine_code=mc)
        assert payload["sub"] == "admin"
        assert payload["machine_code"] == mc

    def test_token_rejected_with_mismatched_machine_code(self):
        from app.core.security import (
            create_access_token_with_machine_code,
            decode_token_with_machine_code,
        )
        token = create_access_token_with_machine_code(
            data={"sub": "admin"},
            machine_code="DEVICE-A",
        )
        with pytest.raises(ValueError, match="设备|绑定|machine"):
            decode_token_with_machine_code(token, expected_machine_code="DEVICE-B")

    def test_old_token_without_machine_code_still_valid(self):
        """向后兼容: 旧Token(无machine_code)不应被拒绝."""
        from app.core.security import (
            create_access_token,
            decode_token_with_machine_code,
        )
        token = create_access_token(data={"sub": "admin"})
        # 验证时不传 machine_code → 跳过校验
        payload = decode_token_with_machine_code(token, expected_machine_code=None)
        assert payload["sub"] == "admin"
