"""数据脱敏服务单元测试 — 100% line/branch coverage"""
import pytest


@pytest.fixture
def svc():
    from app.services.data_masking_service import DataMaskingService
    return DataMaskingService()


class TestMaskPhone:
    def test_normal_11_digits(self, svc):
        assert svc.mask_phone("13812345678") == "138****5678"

    def test_not_string(self, svc):
        assert svc.mask_phone(13812345678) == 13812345678

    def test_empty_string(self, svc):
        assert svc.mask_phone("") == ""

    def test_none(self, svc):
        assert svc.mask_phone(None) is None

    def test_not_11_digits(self, svc):
        assert svc.mask_phone("1381234567") == "1381234567"

    def test_not_all_digits(self, svc):
        assert svc.mask_phone("138abc45678") == "138abc45678"


class TestMaskIdCard:
    def test_18_digits(self, svc):
        assert svc.mask_id_card("110101199001011234") == "110101********1234"

    def test_15_digits(self, svc):
        assert svc.mask_id_card("110101900101123") == "110101******123"

    def test_not_string(self, svc):
        assert svc.mask_id_card(123) == 123

    def test_empty_string(self, svc):
        assert svc.mask_id_card("") == ""

    def test_none(self, svc):
        assert svc.mask_id_card(None) is None

    def test_other_length(self, svc):
        assert svc.mask_id_card("1234567890") == "1234567890"


class TestMaskEmail:
    def test_typical_email(self, svc):
        assert svc.mask_email("example@test.com") == "exa***@test.com"

    def test_short_local_name(self, svc):
        assert svc.mask_email("ab@test.com") == "a***@test.com"

    def test_single_char_local(self, svc):
        assert svc.mask_email("a@test.com") == "a***@test.com"

    def test_not_string(self, svc):
        assert svc.mask_email(123) == 123

    def test_empty_string(self, svc):
        assert svc.mask_email("") == ""

    def test_none(self, svc):
        assert svc.mask_email(None) is None

    def test_no_at_sign(self, svc):
        assert svc.mask_email("notanemail") == "notanemail"


class TestMaskBankCard:
    def test_normal_16_digits(self, svc):
        assert svc.mask_bank_card("6222021234567890") == "6222****7890"

    def test_19_digits(self, svc):
        assert svc.mask_bank_card("6222021234567890123") == "6222****0123"

    def test_less_than_8_digits(self, svc):
        assert svc.mask_bank_card("1234567") == "1234567"

    def test_exactly_8_digits(self, svc):
        assert svc.mask_bank_card("12345678") == "1234****5678"

    def test_not_string(self, svc):
        assert svc.mask_bank_card(12345678) == 12345678

    def test_empty_string(self, svc):
        assert svc.mask_bank_card("") == ""

    def test_none(self, svc):
        assert svc.mask_bank_card(None) is None


class TestMaskName:
    def test_two_chars(self, svc):
        assert svc.mask_name("张三") == "张*"

    def test_three_chars(self, svc):
        assert svc.mask_name("欧阳修") == "欧**"

    def test_single_char(self, svc):
        assert svc.mask_name("李") == "李"

    def test_not_string(self, svc):
        assert svc.mask_name(123) == 123

    def test_empty_string(self, svc):
        assert svc.mask_name("") == ""

    def test_none(self, svc):
        assert svc.mask_name(None) is None


class TestMaskAddress:
    def test_long_address(self, svc):
        assert svc.mask_address("北京市朝阳区某某街道123号") == "北京市朝阳区***"

    def test_exactly_6_chars(self, svc):
        assert svc.mask_address("北京市朝阳") == "北京市朝阳"

    def test_less_than_6_chars(self, svc):
        assert svc.mask_address("北京") == "北京"

    def test_not_string(self, svc):
        assert svc.mask_address(123) == 123

    def test_empty_string(self, svc):
        assert svc.mask_address("") == ""

    def test_none(self, svc):
        assert svc.mask_address(None) is None


class TestMaskField:
    def test_phone(self, svc):
        assert svc.mask_field("13812345678", "phone") == "138****5678"

    def test_id_card(self, svc):
        assert svc.mask_field("110101199001011234", "id_card") == "110101********1234"

    def test_email(self, svc):
        assert svc.mask_field("example@test.com", "email") == "exa***@test.com"

    def test_bank_card(self, svc):
        assert svc.mask_field("6222021234567890", "bank_card") == "6222****7890"

    def test_name(self, svc):
        assert svc.mask_field("张三", "name") == "张*"

    def test_address(self, svc):
        assert svc.mask_field("北京市朝阳区某某街道123号", "address") == "北京市朝阳区***"

    def test_unknown_type(self, svc):
        assert svc.mask_field("some value", "unknown_type") == "some value"

    def test_none_value(self, svc):
        assert svc.mask_field(None, "phone") is None

    def test_non_string_value(self, svc):
        assert svc.mask_field(12345, "phone") == 12345


class TestMaskRecord:
    def test_mask_single_field(self, svc):
        record = {"name": "张三", "phone": "13812345678", "status": "active"}
        result = svc.mask_record(record, {"phone": "phone"})
        assert result == {"name": "张三", "phone": "138****5678", "status": "active"}
        # 原记录不变
        assert record["phone"] == "13812345678"

    def test_mask_multiple_fields(self, svc):
        record = {"name": "张三", "phone": "13812345678", "id_card": "110101199001011234"}
        result = svc.mask_record(record, {"phone": "phone", "id_card": "id_card"})
        assert result["phone"] == "138****5678"
        assert result["id_card"] == "110101********1234"
        assert result["name"] == "张三"

    def test_field_not_in_record(self, svc):
        record = {"name": "张三"}
        result = svc.mask_record(record, {"phone": "phone"})
        assert result == {"name": "张三"}

    def test_deep_copy(self, svc):
        record = {"nested": {"key": "value"}, "phone": "13812345678"}
        result = svc.mask_record(record, {"phone": "phone"})
        assert result["phone"] == "138****5678"
        assert result["nested"]["key"] == "value"
        assert record["nested"] is not result["nested"]


class TestMaskRecords:
    def test_multiple_records(self, svc):
        records = [
            {"name": "张三", "phone": "13812345678"},
            {"name": "李四", "phone": "13912345679"},
        ]
        result = svc.mask_records(records, {"phone": "phone"})
        assert len(result) == 2
        assert result[0]["phone"] == "138****5678"
        assert result[1]["phone"] == "139****5679"

    def test_empty_list(self, svc):
        assert svc.mask_records([], {"phone": "phone"}) == []


class TestGetMaskingRules:
    def test_returns_rules(self, svc):
        rules = svc.get_masking_rules()
        assert isinstance(rules, dict)
        assert "phone" in rules
        assert "id_card" in rules
        assert "email" in rules
        assert "bank_card" in rules
        assert "name" in rules
        assert "address" in rules
        assert rules["phone"]["description"] == "手机号脱敏 - 保留前3后4"


class TestSingleton:
    def test_global_instance_exists(self):
        from app.services.data_masking_service import data_masking_service
        assert data_masking_service is not None
