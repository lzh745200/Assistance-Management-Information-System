"""app.services.entity_import_validator 覆盖率攻坚测试

补齐缺口：
- to_dict（59, 79）、空文件名（228）、int/bool 字段校验（248, 265-266, 326, 330）
- 空值短路（319）、未知字段跳过（372）、行数超限（382）、重复行重算（407-409）
- 未知字段 label 回退（461）、convert_row_types 空值/bool/异常分支（468-469, 478, 488-489）
"""

import pytest

from app.services.entity_import_validator import (
    EntityImportValidator,
    ValidationError,
    ValidationErrorCode,
    ValidationResult,
)


class TestToDict:
    def test_validation_error_to_dict(self):
        err = ValidationError(
            row_number=3,
            field_name="name",
            error_code=ValidationErrorCode.MISSING_REQUIRED_FIELD,
            message="必填字段 'name' 不能为空",
            value="x",
        )
        assert err.to_dict() == {
            "row_number": 3,
            "field_name": "name",
            "error_code": "IMPORT_003",
            "message": "必填字段 'name' 不能为空",
            "value": "x",
        }

    def test_validation_error_to_dict_none_value(self):
        err = ValidationError(
            row_number=1,
            field_name="f",
            error_code=ValidationErrorCode.INVALID_DATA_FORMAT,
            message="m",
        )
        assert err.to_dict()["value"] is None

    def test_validation_result_to_dict(self):
        err = ValidationError(
            row_number=2,
            field_name="amount",
            error_code=ValidationErrorCode.VALUE_OUT_OF_RANGE,
            message="不能为负数",
            value=-5,
        )
        result = ValidationResult(
            is_valid=False, total_rows=2, valid_rows=1, errors=[err], warnings=["w1"]
        )
        d = result.to_dict()
        assert d["is_valid"] is False
        assert d["total_rows"] == 2
        assert d["valid_rows"] == 1
        assert d["error_count"] == 1
        assert d["errors"][0]["error_code"] == "IMPORT_011"
        assert d["errors"][0]["value"] == "-5"
        assert d["warnings"] == ["w1"]


class TestValidateFileFormat:
    def test_empty_filename_rejected(self):
        v = EntityImportValidator("project")
        ok, msg = v.validate_file_format("")
        assert ok is False
        assert msg == "文件名不能为空"


class TestFieldFormatValidators:
    def test_int_field_valid(self):
        v = EntityImportValidator("school")
        assert v._validate_field_format("student_count", "520", "int", 1) is None

    def test_bool_field_invalid_returns_error(self):
        v = EntityImportValidator("project")
        err = v._validate_field_format("some_flag", "maybe", "bool", 2)
        assert err is not None
        assert err.error_code is ValidationErrorCode.INVALID_DATA_FORMAT
        assert err.row_number == 2
        assert "请填写" in err.message

    def test_bool_field_direct_raises(self):
        v = EntityImportValidator("project")
        with pytest.raises(ValueError, match="请填写"):
            v._validate_bool_field("maybe")

    def test_empty_value_returns_none(self):
        v = EntityImportValidator("project")
        assert v._validate_field_format("budget", None, "float", 1) is None
        assert v._validate_field_format("budget", "   ", "float", 1) is None


class TestValidateRow:
    def test_unknown_field_skipped(self):
        v = EntityImportValidator("project")
        errors = v.validate_row({"name": "项目A", "type": "基础设施", "mystery": "x"}, 1)
        assert errors == []


class TestValidateBatch:
    def test_row_limit_exceeded(self):
        v = EntityImportValidator("project")
        rows = [{"name": f"P{i}", "type": "基础设施"} for i in range(1001)]
        result = v.validate_batch(rows)
        assert result.is_valid is False
        assert result.total_rows == 1001
        assert result.valid_rows == 0
        assert len(result.errors) == 1
        assert result.errors[0].error_code is ValidationErrorCode.ROW_LIMIT_EXCEEDED

    def test_duplicates_reduce_valid_count(self):
        v = EntityImportValidator("project")
        rows = [
            {"name": "项目A", "type": "基础设施"},
            {"name": "项目A", "type": "基础设施"},
            {"name": "项目B", "type": "基础设施"},
        ]
        result = v.validate_batch(rows)
        assert result.is_valid is False
        assert any(e.error_code is ValidationErrorCode.DUPLICATE_DATA for e in result.errors)
        # 第 2 行重复 → 有效行从 3 重算为 2
        assert result.valid_rows == 2
        assert result.total_rows == 3


class TestGetFieldLabel:
    def test_unknown_field_falls_back_to_name(self):
        v = EntityImportValidator("project")
        assert v._get_field_label("no_such_field") == "no_such_field"
        assert v._get_field_label("name") == "项目名称"


class TestGetFieldDefinitions:
    def test_returns_config_fields(self):
        v = EntityImportValidator("project")
        fields = v.get_field_definitions()
        assert fields is v.config["fields"]
        assert any(f["name"] == "name" for f in fields)

    def test_unknown_entity_returns_empty(self):
        v = EntityImportValidator("supported_village")  # 无配置 → 空表
        assert v.get_field_definitions() == []


class TestConvertRowTypes:
    def test_none_and_blank_become_none(self):
        v = EntityImportValidator("project")
        converted = v.convert_row_types({"name": None, "code": "   ", "budget": "12.5"})
        assert converted["name"] is None
        assert converted["code"] is None
        assert converted["budget"] == 12.5

    def test_bool_conversion(self):
        v = EntityImportValidator("project")
        # 实例级配置注入 bool 类型字段（内置三类实体均无 bool 字段），不污染类属性
        v.config = {**v.config, "fields": [{"name": "active", "label": "激活", "type": "bool"}]}
        converted = v.convert_row_types({"active": "是"})
        assert converted["active"] is True

    def test_invalid_numeric_kept_as_string(self):
        v = EntityImportValidator("school")
        converted = v.convert_row_types({"student_count": "abc"})
        assert converted["student_count"] == "abc"
