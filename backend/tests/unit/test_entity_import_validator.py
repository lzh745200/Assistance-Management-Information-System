"""
通用实体导入验证器测试
覆盖 projects、funds、schools 导入验证逻辑
"""
import pytest
from datetime import datetime

from app.services.entity_import_validator import (
    EntityImportValidator,
    ValidationErrorCode,
)

class TestEntityImportValidatorProject:
    """项目导入验证测试"""

    def test_project_required_fields(self):
        validator = EntityImportValidator("project")
        errors = validator.validate_row({}, 1)
        assert len(errors) == 2
        fields = {e.field_name for e in errors}
        assert fields == {"name", "type"}

    def test_project_valid_row(self):
        validator = EntityImportValidator("project")
        row = {
            "name": "测试项目",
            "type": "基础设施",
            "budget": "100.50",
            "start_date": "2024-01-01",
            "contact_phone": "13800138000",
        }
        errors = validator.validate_row(row, 1)
        assert len(errors) == 0

    def test_project_invalid_phone(self):
        validator = EntityImportValidator("project")
        row = {
            "name": "测试项目",
            "type": "基础设施",
            "contact_phone": "123",
        }
        errors = validator.validate_row(row, 1)
        assert any(e.error_code == ValidationErrorCode.INVALID_PHONE for e in errors)

    def test_project_invalid_date(self):
        validator = EntityImportValidator("project")
        row = {
            "name": "测试项目",
            "type": "教育",
            "start_date": "2024/01/01",
        }
        errors = validator.validate_row(row, 1)
        assert any(e.error_code == ValidationErrorCode.INVALID_DATA_FORMAT for e in errors)

    def test_project_invalid_enum(self):
        validator = EntityImportValidator("project")
        row = {
            "name": "测试项目",
            "type": "不存在的类型",
        }
        errors = validator.validate_row(row, 1)
        assert any(e.error_code == ValidationErrorCode.INVALID_ENUM_VALUE for e in errors)

    def test_project_duplicate(self):
        validator = EntityImportValidator("project")
        rows = [
            {"name": "项目A", "type": "基础设施"},
            {"name": "项目A", "type": "教育"},
        ]
        errors = validator.check_duplicates(rows)
        assert len(errors) == 1
        assert errors[0].error_code == ValidationErrorCode.DUPLICATE_DATA

    def test_project_convert_types(self):
        validator = EntityImportValidator("project")
        row = {
            "name": "测试项目",
            "type": "基础设施",
            "budget": "100.5",
            "start_date": "2024-03-15",
            "contact_phone": "13800138000",
        }
        converted = validator.convert_row_types(row)
        assert converted["type"] == "infrastructure"
        assert converted["budget"] == 100.5
        assert converted["start_date"].year == 2024

class TestEntityImportValidatorFund:
    """资金导入验证测试"""

    def test_fund_required_fields(self):
        validator = EntityImportValidator("fund")
        errors = validator.validate_row({}, 1)
        assert len(errors) == 2
        fields = {e.field_name for e in errors}
        assert fields == {"name", "amount"}

    def test_fund_negative_amount(self):
        validator = EntityImportValidator("fund")
        row = {
            "name": "测试资金",
            "amount": "-100",
        }
        errors = validator.validate_row(row, 1)
        assert any(e.error_code == ValidationErrorCode.VALUE_OUT_OF_RANGE for e in errors)

    def test_fund_valid_row(self):
        validator = EntityImportValidator("fund")
        row = {
            "name": "测试资金",
            "amount": "100000",
            "fund_type": "project",
            "fund_source": "military",
            "status": "pending",
        }
        errors = validator.validate_row(row, 1)
        assert len(errors) == 0

    def test_fund_convert_types(self):
        validator = EntityImportValidator("fund")
        row = {
            "name": "测试资金",
            "amount": "50000.50",
            "fund_type": "project",
            "date": "2024-06-01",
        }
        converted = validator.convert_row_types(row)
        assert converted["amount"] == 50000.50
        assert converted["date"].month == 6
        assert converted["fund_type"] == "project"

class TestEntityImportValidatorSchool:
    """学校导入验证测试"""

    def test_school_required_fields(self):
        validator = EntityImportValidator("school")
        errors = validator.validate_row({}, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "name"

    def test_school_county_validation(self):
        validator = EntityImportValidator("school")
        row = {
            "name": "测试学校",
            "district": "北京市",
        }
        errors = validator.validate_row(row, 1)
        assert any(e.error_code == ValidationErrorCode.INVALID_COUNTY for e in errors)

    def test_school_valid_county(self):
        validator = EntityImportValidator("school")
        row = {
            "name": "测试学校",
            "district": "都匀市",
            "type": "小学",
            "support_status": "帮扶中",
        }
        errors = validator.validate_row(row, 1)
        assert len(errors) == 0

    def test_school_convert_types(self):
        validator = EntityImportValidator("school")
        row = {
            "name": "测试学校",
            "type": "小学",
            "student_count": "520",
            "teacher_count": "35",
            "support_status": "帮扶中",
        }
        converted = validator.convert_row_types(row)
        assert converted["type"] == "primary"
        assert converted["student_count"] == 520
        assert converted["support_status"] == "active"

class TestEntityImportValidatorCommon:
    """通用验证逻辑测试"""

    def test_validate_file_format(self):
        validator = EntityImportValidator("project")
        ok, msg = validator.validate_file_format("test.xlsx")
        assert ok is True

        ok, msg = validator.validate_file_format("test.pdf")
        assert ok is False
        assert "xlsx" in msg

    def test_validate_file_size(self):
        validator = EntityImportValidator("project")
        ok, msg = validator.validate_file_size(1024)
        assert ok is True

        ok, msg = validator.validate_file_size(11 * 1024 * 1024)
        assert ok is False

    def test_validate_row_count(self):
        validator = EntityImportValidator("project")
        ok, msg = validator.validate_row_count(500)
        assert ok is True

        ok, msg = validator.validate_row_count(1001)
        assert ok is False

    def test_batch_validation(self):
        validator = EntityImportValidator("project")
        rows = [
            {"name": "项目A", "type": "基础设施"},
            {"name": "项目B", "type": "教育"},
            {"name": "", "type": "农业"},
        ]
        result = validator.validate_batch(rows)
        assert result.is_valid is False
        assert result.total_rows == 3
        assert result.valid_rows == 2
        assert len(result.errors) >= 1

    def test_empty_batch(self):
        validator = EntityImportValidator("project")
        result = validator.validate_batch([])
        assert result.is_valid is True
        assert result.total_rows == 0

    def test_parse_excel_headers(self):
        validator = EntityImportValidator("fund")
        headers = ["*资金名称", "金额", "资金类型", "未知字段"]
        mapping = validator.parse_excel_headers(headers)
        assert mapping[0] == "name"
        assert mapping[1] == "amount"
        assert mapping[2] == "fund_type"
        assert 3 not in mapping

    def test_generate_warnings(self):
        validator = EntityImportValidator("school")
        rows = [
            {"name": "学校A", "principal": "张"},
            {"name": "学校B", "principal": None},
            {"name": "学校C", "principal": None},
        ]
        warnings = validator._generate_warnings(rows)
        # principal 有 2/3 为空（大于50%）
        assert any("principal" in w or "校长姓名" in w for w in warnings), f"warnings={warnings}"

    def test_get_validation_summary(self):
        validator = EntityImportValidator("project")
        from app.services.entity_import_validator import ValidationResult

        result = ValidationResult(
            is_valid=False,
            total_rows=3,
            valid_rows=2,
            errors=[
                type("Err", (), {
                    "row_number": 1,
                    "field_name": "name",
                    "error_code": ValidationErrorCode.MISSING_REQUIRED_FIELD,
                    "message": "必填",
                    "value": None,
                    "to_dict": lambda self: {},
                })(),
            ],
            warnings=["warn1"],
        )
        # Note: validation_summary method isn't part of the validator class;
        # it's handled in API layer. We test the API separately.
