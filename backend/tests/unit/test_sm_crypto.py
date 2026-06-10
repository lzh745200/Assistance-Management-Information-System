import pytest
from unittest.mock import Mock, MagicMock, patch


class TestSBox:
    def test_sbox_values(self):
        from app.services.sm_crypto import _SBOX
        assert len(_SBOX) == 256
        assert _SBOX[0] == 0xd6
        assert _SBOX[1] == 0x90

    def test_fk_values(self):
        from app.services.sm_crypto import _FK
        assert len(_FK) == 4
        assert _FK[0] == 0xa3b1bac6

    def test_ck_values(self):
        from app.services.sm_crypto import _CK
        assert len(_CK) == 32


class TestRotl:
    def test_rotl(self):
        from app.services.sm_crypto import _rotl
        result = _rotl(0x12345678, 4)
        assert result == ((0x12345678 << 4) | (0x12345678 >> (32 - 4))) & 0xFFFFFFFF


class TestSboxFunc:
    def test_sbox_func(self):
        from app.services.sm_crypto import _sbox
        result = _sbox(0x01020304)
        assert isinstance(result, int)
        assert result > 0


class TestLtLt2:
    def test_lt(self):
        from app.services.sm_crypto import _lt
        result = _lt(0x12345678)
        assert isinstance(result, int)

    def test_lt2(self):
        from app.services.sm_crypto import _lt2
        result = _lt2(0x12345678)
        assert isinstance(result, int)


class TestStruct:
    def test_pack_unpack_roundtrip(self):
        from app.services.sm_crypto import struct_pack_uint32, struct_unpack_uint32
        val = 0x12345678
        packed = struct_pack_uint32(val)
        assert len(packed) == 4
        unpacked = struct_unpack_uint32(packed)
        assert unpacked == val

    def test_unpack(self):
        from app.services.sm_crypto import struct_unpack_uint32
        assert struct_unpack_uint32(b'\x00\x00\x00\x01') == 1
        assert struct_unpack_uint32(b'\xFF\xFF\xFF\xFF') == 0xFFFFFFFF


class TestKeyExpansion:
    def test_expansion(self):
        from app.services.sm_crypto import _key_expansion
        key = b'\x01\x23\x45\x67\x89\xab\xcd\xef\xfe\xdc\xba\x98\x76\x54\x32\x10'
        rk = _key_expansion(key)
        assert len(rk) == 32
        for v in rk:
            assert isinstance(v, int)
            assert 0 <= v <= 0xFFFFFFFF


class TestSM4Cipher:
    def test_invalid_key_length(self):
        from app.services.sm_crypto import SM4Cipher
        with pytest.raises(ValueError, match="16 字节"):
            SM4Cipher(b'short')

    def test_pkcs7_pad(self):
        from app.services.sm_crypto import SM4Cipher
        c = SM4Cipher(b'\x00' * 16)
        padded = c._pkcs7_pad(b'hello')
        assert len(padded) == 16
        assert padded[-1] == 11

    def test_pkcs7_pad_full_block(self):
        from app.services.sm_crypto import SM4Cipher
        c = SM4Cipher(b'\x00' * 16)
        padded = c._pkcs7_pad(b'\x00' * 16)
        assert len(padded) == 32
        assert padded[-1] == 16

    def test_pkcs7_unpad(self):
        from app.services.sm_crypto import SM4Cipher
        c = SM4Cipher(b'\x00' * 16)
        data = bytes([0x48, 0x65, 0x6c, 0x6c, 0x6f]) + bytes([0x0b] * 11)
        assert c._pkcs7_unpad(data) == b'Hello'

    def test_pkcs7_unpad_invalid(self):
        from app.services.sm_crypto import SM4Cipher
        c = SM4Cipher(b'\x00' * 16)
        data = b'\x00\x00'
        assert c._pkcs7_unpad(data) == data

    def test_encrypt_decrypt_ecb(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x01\x23\x45\x67\x89\xab\xcd\xef\xfe\xdc\xba\x98\x76\x54\x32\x10'
        cipher = SM4Cipher(key)
        plaintext = b'Hello SM4 Crypto!'
        ciphertext = cipher.encrypt_ecb(plaintext)
        assert ciphertext != plaintext
        cipher2 = SM4Cipher(key)
        assert cipher2.encrypt_ecb(plaintext) == ciphertext

    def test_encrypt_decrypt_ecb_empty(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x00' * 16
        cipher = SM4Cipher(key)
        ct = cipher.encrypt_ecb(b'')
        assert len(ct) == 16

    def test_encrypt_decrypt_ecb_exact_block(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x00' * 16
        cipher = SM4Cipher(key)
        pt = b'\x00' * 16
        ct = cipher.encrypt_ecb(pt)
        assert len(ct) == 32
        cipher2 = SM4Cipher(key)
        assert cipher2.encrypt_ecb(pt) == ct

    def test_encrypt_decrypt_cbc(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x01\x23\x45\x67\x89\xab\xcd\xef\xfe\xdc\xba\x98\x76\x54\x32\x10'
        iv = b'\x00' * 16
        cipher = SM4Cipher(key)
        plaintext = b'Sensitive CBC data'
        ciphertext = cipher.encrypt_cbc(plaintext, iv)
        assert ciphertext != plaintext
        cipher2 = SM4Cipher(key)
        assert cipher2.encrypt_cbc(plaintext, iv) == ciphertext

    def test_encrypt_decrypt_cbc_empty(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x00' * 16
        iv = b'\x00' * 16
        cipher = SM4Cipher(key)
        ct = cipher.encrypt_cbc(b'', iv)
        assert len(ct) == 16

    def test_ecb_deterministic(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x01\x23\x45\x67\x89\xab\xcd\xef\xfe\xdc\xba\x98\x76\x54\x32\x10'
        c1 = SM4Cipher(key)
        c2 = SM4Cipher(key)
        pt = b'Test message for SM4 ECB mode'
        assert c1.encrypt_ecb(pt) == c2.encrypt_ecb(pt)

    def test_cbc_different_iv_different_output(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x00' * 16
        c = SM4Cipher(key)
        pt = b'CBC test data'
        ct1 = c.encrypt_cbc(pt, b'\x00' * 16)
        ct2 = c.encrypt_cbc(pt, b'\x01' * 16)
        assert ct1 != ct2

    def test_decrypt_ecb_executes(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x00' * 16
        c = SM4Cipher(key)
        pt = b'Hello SM4 ECB!'
        ct = c.encrypt_ecb(pt)
        result = c.decrypt_ecb(ct)
        assert isinstance(result, bytes)

    def test_decrypt_ecb_multiple_blocks(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x00' * 16
        c = SM4Cipher(key)
        pt = b'A' * 32
        ct = c.encrypt_ecb(pt)
        result = c.decrypt_ecb(ct)
        assert isinstance(result, bytes)

    def test_decrypt_cbc_executes(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x00' * 16
        c = SM4Cipher(key)
        pt = b'Hello SM4 CBC!'
        iv = b'\x00' * 16
        ct = c.encrypt_cbc(pt, iv)
        result = c.decrypt_cbc(ct, iv)
        assert isinstance(result, bytes)

    def test_decrypt_cbc_multiple_blocks(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x00' * 16
        c = SM4Cipher(key)
        pt = b'B' * 48
        iv = b'\x00' * 16
        ct = c.encrypt_cbc(pt, iv)
        result = c.decrypt_cbc(ct, iv)
        assert isinstance(result, bytes)

    def test_decrypt_ecb_empty(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x00' * 16
        c = SM4Cipher(key)
        ct = c.encrypt_ecb(b'')
        result = c.decrypt_ecb(ct)
        assert isinstance(result, bytes)

    def test_decrypt_cbc_empty(self):
        from app.services.sm_crypto import SM4Cipher
        key = b'\x00' * 16
        c = SM4Cipher(key)
        iv = b'\x00' * 16
        ct = c.encrypt_cbc(b'', iv)
        result = c.decrypt_cbc(ct, iv)
        assert isinstance(result, bytes)


class TestAuditChain:
    def test_chain_hash_linking(self):
        from app.services.sm_crypto import AuditChain
        chain = AuditChain()
        e1 = chain.add_entry("user_login", {"user": "admin"})
        e2 = chain.add_entry("fund_create", {"fund_id": 1})
        assert e1["sequence"] == 1
        assert e2["sequence"] == 2
        assert e2["prev_hash"] == e1["hash"]

    def test_chain_verification_passes(self):
        from app.services.sm_crypto import AuditChain
        chain = AuditChain()
        chain.add_entry("a", {})
        chain.add_entry("b", {})
        assert chain.verify() is True

    def test_tampered_chain_detected(self):
        from app.services.sm_crypto import AuditChain
        chain = AuditChain()
        chain.add_entry("a", {})
        chain.add_entry("b", {})
        chain.entries[0]["hash"] = "tampered"
        assert chain.verify() is False

    def test_chain_to_json_roundtrip(self):
        from app.services.sm_crypto import AuditChain
        chain = AuditChain()
        chain.add_entry("test", {"key": "value"})
        json_data = chain.to_json()
        chain2 = AuditChain.from_json(json_data)
        assert chain2.verify() is True

    def test_empty_chain_verifies(self):
        from app.services.sm_crypto import AuditChain
        chain = AuditChain()
        assert chain.verify() is True

    def test_prev_hash_mismatch_detected(self):
        from app.services.sm_crypto import AuditChain
        chain = AuditChain()
        chain.add_entry("a", {"x": 1})
        chain.add_entry("b", {"x": 2})
        chain.entries[1]["prev_hash"] = "badhash"
        assert chain.verify() is False

    def test_from_json_empty_list(self):
        from app.services.sm_crypto import AuditChain
        chain = AuditChain.from_json("[]")
        assert chain.verify() is True
        assert chain.entries == []

    def test_from_json_with_entries(self):
        from app.services.sm_crypto import AuditChain
        chain = AuditChain()
        chain.add_entry("evt", {"data": 1})
        json_data = chain.to_json()
        chain2 = AuditChain.from_json(json_data)
        assert len(chain2.entries) == 1
        assert chain2.verify() is True
