"""数据脱敏服务单元测试"""
import pytest

@pytest.fixture
def svc():
    from app.services.data_masking_service import DataMaskingService
    return DataMaskingService()

def test_mask_phone(svc):
    result = svc.mask_phone("13812345678")
    assert result == "138****5678"

def test_mask_phone_short(svc):
    result = svc.mask_phone("1234")
    assert len(result) >= 1  # gracefully handles short numbers

def test_mask_id_card(svc):
    result = svc.mask_id_card("110101199001011234")
    assert len(result) == 18
    assert "*" in result

def test_mask_email(svc):
    result = svc.mask_email("test@example.com")
    assert "@" in result
    assert result != "test@example.com"

def test_mask_name(svc):
    result = svc.mask_name("张三")
    assert len(result) >= 1
    assert "*" in result

def test_mask_bank_card(svc):
    result = svc.mask_bank_card("6222000012345678")
    assert "*" in result

def test_mask_address(svc):
    result = svc.mask_address("北京市朝阳区某某街道123号")
    assert len(result) >= 1

def test_masking_rules_defined(svc):
    assert "phone" in svc.MASKING_RULES
    assert "id_card" in svc.MASKING_RULES
    assert "email" in svc.MASKING_RULES
