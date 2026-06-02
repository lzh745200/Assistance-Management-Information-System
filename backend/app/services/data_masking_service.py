"""
数据脱敏服务

提供常见敏感字段的脱敏功能：
- 手机号: 138****5678
- 身份证号: 110101********1234
- 邮箱: exa***@test.com
- 银行卡号: 6222****7890
- 姓名: 张* / 欧**
- 地址: 北京市朝阳区***

需求: 7.x - 数据安全与脱敏
"""

from typing import Any, Dict, List


class DataMaskingService:
    """数据脱敏服务（单例模式）"""

    # 脱敏规则定义
    MASKING_RULES = {
        "phone": {
            "description": "手机号脱敏 - 保留前3后4",
            "example": {"original": "13812345678", "masked": "138****5678"},
        },
        "id_card": {
            "description": "身份证号脱敏 - 保留前6后4",
            "example": {"original": "110101199001011234", "masked": "110101********1234"},
        },
        "email": {
            "description": "邮箱脱敏 - 保留前3后域名",
            "example": {"original": "example@test.com", "masked": "exa***@test.com"},
        },
        "bank_card": {
            "description": "银行卡号脱敏 - 保留前4后4",
            "example": {"original": "6222021234567890", "masked": "6222****7890"},
        },
        "name": {
            "description": "姓名脱敏 - 保留姓氏",
            "example": {"original": "张三", "masked": "张*"},
        },
        "address": {
            "description": "地址脱敏 - 保留前6字符",
            "example": {"original": "北京市朝阳区某某街道123号", "masked": "北京市朝阳区***"},
        },
    }

    def mask_phone(self, phone: str) -> str:
        """手机号脱敏: 13812345678 -> 138****5678"""
        if not phone or not isinstance(phone, str):
            return phone
        if len(phone) != 11 or not phone.isdigit():
            return phone
        return phone[:3] + "****" + phone[7:]

    def mask_id_card(self, id_card: str) -> str:
        """身份证号脱敏: 保留前6后4"""
        if not id_card or not isinstance(id_card, str):
            return id_card
        length = len(id_card)
        if length == 18:
            return id_card[:6] + "********" + id_card[14:]
        elif length == 15:
            return id_card[:6] + "******" + id_card[12:]
        return id_card

    def mask_email(self, email: str) -> str:
        """邮箱脱敏: example@test.com -> exa***@test.com"""
        if not email or not isinstance(email, str):
            return email
        if "@" not in email:
            return email
        local, domain = email.split("@", 1)
        if len(local) <= 3:
            masked_local = local[0] + "***"
        else:
            masked_local = local[:3] + "***"
        return masked_local + "@" + domain

    def mask_bank_card(self, card: str) -> str:
        """银行卡号脱敏: 6222021234567890 -> 6222****7890"""
        if not card or not isinstance(card, str):
            return card
        if len(card) < 8:
            return card
        return card[:4] + "****" + card[-4:]

    def mask_name(self, name: str) -> str:
        """姓名脱敏: 张三 -> 张*, 欧阳修 -> 欧**"""
        if not name or not isinstance(name, str):
            return name
        if len(name) <= 1:
            return name
        # 保留姓氏（第一个字），其余用 * 替换
        return name[0] + "*" * (len(name) - 1)

    def mask_address(self, address: str) -> str:
        """地址脱敏: 北京市朝阳区某某街道123号 -> 北京市朝阳区***"""
        if not address or not isinstance(address, str):
            return address
        if len(address) <= 6:
            return address
        return address[:6] + "***"

    def mask_field(self, value: Any, field_type: str) -> Any:
        """根据字段类型自动脱敏"""
        if value is None:
            return None
        if not isinstance(value, str):
            return value

        maskers = {
            "phone": self.mask_phone,
            "id_card": self.mask_id_card,
            "email": self.mask_email,
            "bank_card": self.mask_bank_card,
            "name": self.mask_name,
            "address": self.mask_address,
        }

        masker = maskers.get(field_type)
        if masker:
            return masker(value)
        return value

    def mask_record(
        self, record: Dict[str, Any], field_mappings: Dict[str, str]
    ) -> Dict[str, Any]:
        """对单条记录的指定字段脱敏

        Args:
            record: 原始记录
            field_mappings: {字段名: 脱敏类型} 映射，如 {"phone": "phone", "email": "email"}

        Returns:
            脱敏后的记录（不修改原始记录）
        """
        import copy

        result = copy.deepcopy(record)
        for field_name, field_type in field_mappings.items():
            if field_name in result:
                result[field_name] = self.mask_field(result[field_name], field_type)
        return result

    def mask_records(
        self, records: List[Dict[str, Any]], field_mappings: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """批量脱敏

        Args:
            records: 原始记录列表
            field_mappings: {字段名: 脱敏类型} 映射

        Returns:
            脱敏后的记录列表
        """
        return [self.mask_record(record, field_mappings) for record in records]

    def get_masking_rules(self) -> Dict[str, Dict[str, Any]]:
        """获取所有脱敏规则定义"""
        return self.MASKING_RULES


# 全局单例
data_masking_service = DataMaskingService()
