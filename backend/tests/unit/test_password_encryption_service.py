"""基于密码的加密服务单元测试 (100% coverage)"""
import os
from unittest.mock import MagicMock, patch

import pytest


class TestGenerateSalt:
    def test_returns_32_bytes(self):
        from app.services.password_encryption_service import PasswordEncryptionService
        salt = PasswordEncryptionService.generate_salt()
        assert isinstance(salt, bytes)
        assert len(salt) == 32

    def test_unique(self):
        from app.services.password_encryption_service import PasswordEncryptionService
        s1 = PasswordEncryptionService.generate_salt()
        s2 = PasswordEncryptionService.generate_salt()
        assert s1 != s2


class TestDeriveKeyFromPassword:
    @pytest.fixture
    def svc(self):
        from app.services.password_encryption_service import PasswordEncryptionService
        return PasswordEncryptionService

    def test_returns_32_bytes_default(self, svc):
        salt = svc.generate_salt()
        key = svc.derive_key_from_password("password", salt)
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_custom_iterations(self, svc):
        salt = svc.generate_salt()
        key = svc.derive_key_from_password("password", salt, iterations=50000)
        assert len(key) == 32

    def test_deterministic(self, svc):
        salt = os.urandom(32)
        key1 = svc.derive_key_from_password("hello", salt, 100)
        key2 = svc.derive_key_from_password("hello", salt, 100)
        assert key1 == key2

    def test_different_passwords(self, svc):
        salt = os.urandom(32)
        key1 = svc.derive_key_from_password("pass1", salt)
        key2 = svc.derive_key_from_password("pass2", salt)
        assert key1 != key2

    def test_different_salts(self, svc):
        key1 = svc.derive_key_from_password("pass", os.urandom(32))
        key2 = svc.derive_key_from_password("pass", os.urandom(32))
        assert key1 != key2


class TestKeyToFernetKey:
    def test_returns_base64_bytes(self):
        from app.services.password_encryption_service import PasswordEncryptionService
        raw_key = b'\x00' * 32
        fernet_key = PasswordEncryptionService._key_to_fernet_key(raw_key)
        assert isinstance(fernet_key, bytes)
        assert fernet_key.endswith(b'=')


class TestEncryptDecryptData:
    @pytest.fixture
    def svc(self):
        from app.services.password_encryption_service import PasswordEncryptionService
        return PasswordEncryptionService

    def test_encrypt_decrypt_roundtrip(self, svc):
        original = b"Hello World"
        password = "mypassword"
        salt = svc.generate_salt()
        encrypted = svc.encrypt_data(original, password, salt)
        assert isinstance(encrypted, bytes)
        assert encrypted != original
        decrypted = svc.decrypt_data(encrypted, password, salt)
        assert decrypted == original

    def test_custom_iterations(self, svc):
        original = b"Test"
        salt = svc.generate_salt()
        encrypted = svc.encrypt_data(original, "pass", salt, iterations=50000)
        decrypted = svc.decrypt_data(encrypted, "pass", salt, iterations=50000)
        assert decrypted == original

    def test_wrong_password_raises_error(self, svc):
        salt = svc.generate_salt()
        encrypted = svc.encrypt_data(b"secret", "correct", salt)
        from app.services.password_encryption_service import InvalidPasswordError
        with pytest.raises(InvalidPasswordError):
            svc.decrypt_data(encrypted, "wrong", salt)

    def test_wrong_salt_raises_error(self, svc):
        salt = svc.generate_salt()
        encrypted = svc.encrypt_data(b"secret", "password", salt)
        from app.services.password_encryption_service import InvalidPasswordError
        with pytest.raises(InvalidPasswordError):
            svc.decrypt_data(encrypted, "password", svc.generate_salt())


class TestEncryptFile:
    def test_encrypt_and_return(self, tmp_path):
        from app.services.password_encryption_service import PasswordEncryptionService
        input_file = tmp_path / "plain.txt"
        output_file = tmp_path / "encrypted.bin"
        input_file.write_bytes(b"File content")

        salt_hex, iterations = PasswordEncryptionService.encrypt_file(
            str(input_file), "pass", str(output_file)
        )
        assert isinstance(salt_hex, str)
        assert len(salt_hex) == 64
        assert iterations == 100000
        assert output_file.exists()
        assert output_file.read_bytes() != b"File content"


class TestDecryptFile:
    def test_roundtrip(self, tmp_path):
        from app.services.password_encryption_service import PasswordEncryptionService
        input_file = tmp_path / "plain.txt"
        enc_file = tmp_path / "encrypted.bin"
        dec_file = tmp_path / "decrypted.txt"

        input_file.write_bytes(b"Secret data")
        salt_hex, iterations = PasswordEncryptionService.encrypt_file(
            str(input_file), "mypass", str(enc_file)
        )
        PasswordEncryptionService.decrypt_file(
            str(enc_file), "mypass", salt_hex, iterations, str(dec_file)
        )
        assert dec_file.read_bytes() == b"Secret data"

    def test_wrong_password(self, tmp_path):
        from app.services.password_encryption_service import (
            PasswordEncryptionService, InvalidPasswordError,
        )
        input_file = tmp_path / "plain.txt"
        enc_file = tmp_path / "encrypted.bin"
        out_file = tmp_path / "out.txt"

        input_file.write_bytes(b"Data")
        salt_hex, iterations = PasswordEncryptionService.encrypt_file(
            str(input_file), "pass", str(enc_file)
        )
        with pytest.raises(InvalidPasswordError):
            PasswordEncryptionService.decrypt_file(
                str(enc_file), "wrong", salt_hex, iterations, str(out_file)
            )


class TestError:
    def test_invalid_password_error(self):
        from app.services.password_encryption_service import InvalidPasswordError
        err = InvalidPasswordError()
        assert "密码错误" in str(err)

    def test_invalid_password_error_inherits(self):
        from app.services.password_encryption_service import InvalidPasswordError
        from app.core.exceptions import BusinessError
        assert issubclass(InvalidPasswordError, BusinessError)
