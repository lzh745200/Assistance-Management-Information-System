"""TDD: 国密 SM4 对称加密 + 审计链."""
import pytest


class TestAuditChain:
    def test_chain_hash_linking(self):
        from app.services.sm_crypto import AuditChain
        chain = AuditChain()
        e1 = chain.add_entry("user_login", {"user": "admin"})
        e2 = chain.add_entry("fund_create", {"fund_id": 1})
        assert e1["sequence"] == 1 and e2["sequence"] == 2
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
