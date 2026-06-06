"""TDD: 国密 SM4 对称加密 + 审计链."""
import pytest


class TestSM4Cipher:
    def test_encrypt_decrypt_roundtrip(self):
        from app.services.sm_crypto import SM4Cipher
        key = bytes.fromhex("0123456789abcdeffedcba9876543210")
        cipher = SM4Cipher(key)
        pt = b"Hello SM4 Cipher!"
        ct = cipher.encrypt_ecb(pt)
        assert ct != pt
        assert len(ct) >= len(pt)
        result = cipher.decrypt_ecb(ct)
        assert result.rstrip(b"\x00") == pt  # PKCS7 unpadding

    def test_different_keys_produce_different_ciphertexts(self):
        from app.services.sm_crypto import SM4Cipher
        c1 = SM4Cipher(bytes.fromhex("0123456789abcdeffedcba9876543210"))
        c2 = SM4Cipher(bytes.fromhex("fedcba98765432100123456789abcdef"))
        pt = b"test data"
        assert c1.encrypt_ecb(pt) != c2.encrypt_ecb(pt)

    def test_wrong_key_fails(self):
        from app.services.sm_crypto import SM4Cipher
        c1 = SM4Cipher(bytes.fromhex("0123456789abcdeffedcba9876543210"))
        c2 = SM4Cipher(bytes.fromhex("fedcba98765432100123456789abcdef"))
        ct = c1.encrypt_ecb(b"secret")
        result = c2.decrypt_ecb(ct)
        # Wrong key produces garbage, which may not exactly match original
        assert result != b"secret"  # with wrong key, output is random garbage

    def test_cbc_mode_roundtrip(self):
        from app.services.sm_crypto import SM4Cipher
        key = bytes.fromhex("0123456789abcdeffedcba9876543210")
        iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        cipher = SM4Cipher(key)
        pt = b"0123456789abcdef"  # exactly 16 bytes, no padding needed
        ct = cipher.encrypt_cbc(pt, iv)
        result = cipher.decrypt_cbc(ct, iv)
        assert result == pt


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
