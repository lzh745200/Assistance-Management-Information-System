"""
完整测试 - app.services.validation_engine_service
覆盖率目标: 100%
"""
import pytest
from unittest.mock import MagicMock, patch

class TestValidationResult:
    """测试 ValidationResult 数据类"""

    def test_validation_result_valid(self):
        """测试有效验证结果"""
        from app.services.validation_engine_service import ValidationResult

        result = ValidationResult(is_valid=True, errors=[])
        assert result.is_valid is True
        assert result.errors == []

    def test_validation_result_invalid(self):
        """测试无效验证结果"""
        from app.services.validation_engine_service import ValidationResult

        result = ValidationResult(is_valid=False, errors=["error1", "error2"])
        assert result.is_valid is False
        assert result.errors == ["error1", "error2"]

class TestValidationEngineService:
    """测试 ValidationEngineService 类"""

    def test_service_creation_no_db(self):
        """测试创建服务 - 无数据库"""
        from app.services.validation_engine_service import ValidationEngineService

        service = ValidationEngineService(db=None)
        assert service.db is None
        assert service._validators == {}
        assert service._errors == []

    def test_service_creation_with_db(self):
        """测试创建服务 - 有数据库"""
        from app.services.validation_engine_service import ValidationEngineService

        mock_db = MagicMock()
        service = ValidationEngineService(db=mock_db)
        assert service.db is mock_db

    def test_validate_pass(self):
        """测试验证通过"""
        from app.services.validation_engine_service import ValidationEngineService

        service = ValidationEngineService()
        data = {"name": "test", "email": "test@example.com"}
        rules = {"name": {"required": True}, "email": {"required": True}}

        errors = service.validate(data, rules)

        assert errors == []

    def test_validate_fail_required(self):
        """测试验证失败 - 必填字段缺失"""
        from app.services.validation_engine_service import ValidationEngineService

        service = ValidationEngineService()
        data = {"name": "test"}  # 缺少 email
        rules = {"name": {"required": True}, "email": {"required": True}}

        errors = service.validate(data, rules)

        assert len(errors) == 1
        assert "email is required" in errors

    def test_validate_multiple_errors(self):
        """测试验证 - 多个错误"""
        from app.services.validation_engine_service import ValidationEngineService

        service = ValidationEngineService()
        data = {}  # 缺少所有字段
        rules = {"name": {"required": True}, "email": {"required": True}}

        errors = service.validate(data, rules)

        assert len(errors) == 2

    def test_validate_not_required(self):
        """测试验证 - 非必填字段"""
        from app.services.validation_engine_service import ValidationEngineService

        service = ValidationEngineService()
        data = {"name": "test"}  # email 不是必填
        rules = {"name": {"required": True}, "email": {"required": False}}

        errors = service.validate(data, rules)

        assert errors == []

    def test_register_validator(self):
        """测试注册验证器"""
        from app.services.validation_engine_service import ValidationEngineService

        service = ValidationEngineService()
        validator_func = lambda x: True

        service.register_validator("custom", validator_func)

        assert service._validators["custom"] == validator_func

    def test_add_rule(self):
        """测试添加验证规则"""
        from app.services.validation_engine_service import ValidationEngineService

        service = ValidationEngineService()
        rule_func = lambda x: True

        service.add_rule("custom_rule", rule_func)

        assert service._validators["custom_rule"] == rule_func

    def test_get_errors(self):
        """测试获取错误列表"""
        from app.services.validation_engine_service import ValidationEngineService

        service = ValidationEngineService()
        service._errors = ["error1", "error2"]

        errors = service.get_errors()

        assert errors == ["error1", "error2"]

    def test_clear_errors(self):
        """测试清除错误"""
        from app.services.validation_engine_service import ValidationEngineService

        service = ValidationEngineService()
        service._errors = ["error1", "error2"]

        service.clear_errors()

        assert service._errors == []

class TestAliasExport:
    """测试别名导出"""

    def test_validation_engine_alias(self):
        """测试 ValidationEngine 别名"""
        from app.services.validation_engine_service import ValidationEngine, ValidationEngineService
        assert ValidationEngine is ValidationEngineService

class TestValidateEntity:
    """测试 validate_entity 函数"""

    def test_validate_entity_valid(self):
        """测试验证实体 - 有效"""
        from app.services.validation_engine_service import validate_entity

        data = {"name": "test", "email": "test@example.com"}
        rules = {"name": {"required": True}, "email": {"required": True}}

        result = validate_entity(data, rules)

        assert result.is_valid is True
        assert result.errors == []

    def test_validate_entity_invalid(self):
        """测试验证实体 - 无效"""
        from app.services.validation_engine_service import validate_entity

        data = {"name": "test"}
        rules = {"name": {"required": True}, "email": {"required": True}}

        result = validate_entity(data, rules)

        assert result.is_valid is False
        assert len(result.errors) == 1

class TestValidateStringLength:
    """测试 validate_string_length 函数"""

    def test_validate_string_length_valid(self):
        """测试字符串长度验证 - 有效"""
        from app.services.validation_engine_service import validate_string_length

        assert validate_string_length("hello", 3, 10) is True
        assert validate_string_length("hello", 5, 5) is True

    def test_validate_string_length_too_short(self):
        """测试字符串长度验证 - 太短"""
        from app.services.validation_engine_service import validate_string_length

        assert validate_string_length("hi", 3, 10) is False

    def test_validate_string_length_too_long(self):
        """测试字符串长度验证 - 太长"""
        from app.services.validation_engine_service import validate_string_length

        assert validate_string_length("hello world", 3, 5) is False

    def test_validate_string_length_not_string(self):
        """测试字符串长度验证 - 非字符串"""
        from app.services.validation_engine_service import validate_string_length

        assert validate_string_length(123, 3, 10) is False

class TestValidateEmailFormat:
    """测试 validate_email_format 函数"""

    def test_validate_email_format_valid(self):
        """测试邮箱格式验证 - 有效"""
        from app.services.validation_engine_service import validate_email_format

        with patch('app.services.validation_engine_service.InputValidator.validate_email', return_value=True):
            assert validate_email_format("test@example.com") is True

    def test_validate_email_format_invalid(self):
        """测试邮箱格式验证 - 无效"""
        from app.services.validation_engine_service import validate_email_format

        with patch('app.services.validation_engine_service.InputValidator.validate_email', return_value=False):
            assert validate_email_format("invalid-email") is False

class TestValidatePhoneFormat:
    """测试 validate_phone_format 函数"""

    def test_validate_phone_format_valid(self):
        """测试手机号格式验证 - 有效"""
        from app.services.validation_engine_service import validate_phone_format

        with patch('app.services.validation_engine_service.InputValidator.validate_phone', return_value=True):
            assert validate_phone_format("13800138000") is True

    def test_validate_phone_format_invalid(self):
        """测试手机号格式验证 - 无效"""
        from app.services.validation_engine_service import validate_phone_format

        with patch('app.services.validation_engine_service.InputValidator.validate_phone', return_value=False):
            assert validate_phone_format("123") is False

class TestValidateNumberRange:
    """测试 validate_number_range 函数"""

    def test_validate_number_range_valid(self):
        """测试数字范围验证 - 有效"""
        from app.services.validation_engine_service import validate_number_range

        with patch('app.services.validation_engine_service.InputValidator.validate_number_range', return_value=True):
            assert validate_number_range(50, 0, 100) is True

    def test_validate_number_range_invalid(self):
        """测试数字范围验证 - 无效"""
        from app.services.validation_engine_service import validate_number_range

        with patch('app.services.validation_engine_service.InputValidator.validate_number_range', return_value=False):
            assert validate_number_range(150, 0, 100) is False

class TestValidateRequiredFields:
    """测试 validate_required_fields 函数"""

    def test_validate_required_fields_valid(self):
        """测试必填字段验证 - 有效"""
        from app.services.validation_engine_service import validate_required_fields

        data = {"name": "test", "email": "test@example.com"}
        fields = ["name", "email"]

        with patch('app.services.validation_engine_service.InputValidator.validate_required_fields'):
            assert validate_required_fields(data, fields) is True

    def test_validate_required_fields_invalid(self):
        """测试必填字段验证 - 无效"""
        from app.services.validation_engine_service import validate_required_fields

        data = {"name": "test"}
        fields = ["name", "email"]

        with patch('app.services.validation_engine_service.InputValidator.validate_required_fields', side_effect=Exception("Missing field")):
            assert validate_required_fields(data, fields) is False
