"""
验证引擎服务

提供数据验证功能
"""

from dataclasses import dataclass
import logging
from typing import Optional, Any, Dict, List, Callable
from sqlalchemy.orm import Session

from app.utils.input_validator import InputValidator


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    errors: List[str]


class ValidationEngineService:
    """
    验证引擎服务

    提供统一的数据验证功能
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._validators = {}
        self._errors = []

    def validate(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[str]:
        """
        验证数据

        Args:
            data: 待验证的数据
            rules: 验证规则

        Returns:
            List[str]: 错误列表，空列表表示验证通过
        """
        errors = []
        for field, rule in rules.items():
            if rule.get("required") and not data.get(field):
                errors.append(f"{field} is required")
        self._errors = errors
        return errors

    def register_validator(self, name: str, validator: Any):
        """注册验证器"""
        self._validators[name] = validator

    def add_rule(self, name: str, validator: Callable):
        """添加验证规则"""
        self._validators[name] = validator

    def get_errors(self) -> List[str]:
        """获取错误列表"""
        return self._errors

    def clear_errors(self):
        """清除错误"""
        self._errors = []


# 别名导出
ValidationEngine = ValidationEngineService


def validate_entity(data: Dict[str, Any], rules: Dict[str, Any]) -> ValidationResult:
    """验证实体"""
    service = ValidationEngineService()
    errors = service.validate(data, rules)
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def validate_string_length(value: str, min_len: int, max_len: int) -> bool:
    """验证字符串长度"""
    if not isinstance(value, str):
        return False
    return min_len <= len(value) <= max_len


def validate_email_format(email: str) -> bool:
    """验证邮箱格式（委托给 InputValidator）"""
    return InputValidator.validate_email(email)


def validate_phone_format(phone: str) -> bool:
    """验证手机号格式（委托给 InputValidator）"""
    return InputValidator.validate_phone(phone)


def validate_number_range(value: float, min_val: float, max_val: float) -> bool:
    """验证数字范围（委托给 InputValidator）"""
    return InputValidator.validate_number_range(value, min_val, max_val)


def validate_required_fields(data: Dict[str, Any], fields: List[str]) -> bool:
    """验证必填字段（委托给 InputValidator）"""
    try:
        InputValidator.validate_required_fields(data, fields)
        return True
    except Exception as e:
        logging.getLogger(__name__).debug("validate_required_fields failed: %s", e)
        return False
