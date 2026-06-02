"""
数据脱敏服务测试
"""
import pytest
from app.services.data_masking_service import data_masking_service



class TestDataMaskingService:
    """数据脱敏服务测试"""

    def test_mask_phone(self):
        """测试手机号脱敏"""
        phone = "13812345678"
        masked = data_masking_service.mask_phone(phone)
        assert masked == "138****5678"

    def test_mask_phone_invalid(self):
        """测试无效手机号"""
        phone = "123"
        masked = data_masking_service.mask_phone(phone)
        assert masked == phone  # 无效号码不脱敏

    def test_mask_id_card(self):
        """测试身份证号脱敏"""
        id_card = "110101199001011234"
        masked = data_masking_service.mask_id_card(id_card)
        assert masked == "110101********1234"

    def test_mask_id_card_15_digits(self):
        """测试15位身份证号脱敏"""
        id_card = "110101900101123"
        masked = data_masking_service.mask_id_card(id_card)
        assert "******" in masked

    def test_mask_email(self):
        """测试邮箱脱敏"""
        email = "example@test.com"
        masked = data_masking_service.mask_email(email)
        assert masked == "exa***@test.com"

    def test_mask_email_short(self):
        """测试短邮箱脱敏"""
        email = "ab@test.com"
        masked = data_masking_service.mask_email(email)
        assert "***@" in masked

    def test_mask_bank_card(self):
        """测试银行卡号脱敏"""
        card = "6222021234567890"
        masked = data_masking_service.mask_bank_card(card)
        assert masked == "6222****7890"

    def test_mask_name(self):
        """测试姓名脱敏"""
        name = "张三"
        masked = data_masking_service.mask_name(name)
        assert masked == "张*"

        name = "欧阳修"
        masked = data_masking_service.mask_name(name)
        assert masked == "欧**"

    def test_mask_address(self):
        """测试地址脱敏"""
        address = "北京市朝阳区某某街道123号"
        masked = data_masking_service.mask_address(address)
        assert masked == "北京市朝阳区***"

    def test_mask_address_short(self):
        """测试短地址"""
        address = "北京"
        masked = data_masking_service.mask_address(address)
        assert masked == address  # 太短不脱敏

    def test_mask_field(self):
        """测试字段脱敏"""
        phone = "13812345678"
        masked = data_masking_service.mask_field(phone, "phone")
        assert masked == "138****5678"

    def test_mask_field_none(self):
        """测试空值脱敏"""
        masked = data_masking_service.mask_field(None, "phone")
        assert masked is None

    def test_mask_record(self):
        """测试记录脱敏"""
        record = {
            "name": "张三",
            "phone": "13812345678",
            "email": "test@example.com",
            "other": "不脱敏字段"
        }

        field_mappings = {
            "name": "name",
            "phone": "phone",
            "email": "email"
        }

        masked = data_masking_service.mask_record(record, field_mappings)

        assert masked["name"] == "张*"
        assert masked["phone"] == "138****5678"
        assert "***@" in masked["email"]
        assert masked["other"] == "不脱敏字段"

    def test_mask_records(self):
        """测试批量脱敏"""
        records = [
            {"name": "张三", "phone": "13812345678"},
            {"name": "李四", "phone": "13987654321"}
        ]

        field_mappings = {"name": "name", "phone": "phone"}

        masked = data_masking_service.mask_records(records, field_mappings)

        assert len(masked) == 2
        assert masked[0]["name"] == "张*"
        assert masked[1]["name"] == "李*"

    def test_get_masking_rules(self):
        """测试获取脱敏规则"""
        rules = data_masking_service.get_masking_rules()

        assert isinstance(rules, dict)
        assert "phone" in rules
        assert "id_card" in rules
        assert "email" in rules

        # 检查规则包含描述和示例
        phone_rule = rules["phone"]
        assert "description" in phone_rule
        assert "example" in phone_rule
        assert "original" in phone_rule["example"]
        assert "masked" in phone_rule["example"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
