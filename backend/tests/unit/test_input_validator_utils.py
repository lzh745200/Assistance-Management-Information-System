"""Tests for app/utils/input_validator.py — 100% coverage."""
import pytest
from fastapi import HTTPException


class TestSanitizeString:
    def test_non_string_converts(self):
        from app.utils.input_validator import InputValidator
        result = InputValidator.sanitize_string(123)
        assert result == "123"

    def test_truncates_to_max_length(self):
        from app.utils.input_validator import InputValidator
        result = InputValidator.sanitize_string("a" * 2000, max_length=10)
        assert len(result) == 10

    def test_raises_on_xss_script_tag(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.sanitize_string("<script>alert(1)</script>")
        assert "不安全内容" in str(exc.value.detail)

    def test_raises_on_javascript_protocol(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.sanitize_string("javascript:alert(1)")
        assert "不安全内容" in str(exc.value.detail)

    def test_raises_on_event_handler(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.sanitize_string("onclick=")
        assert "不安全内容" in str(exc.value.detail)

    def test_raises_on_iframe(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.sanitize_string("<iframe src='http://evil.com'>")
        assert "不安全内容" in str(exc.value.detail)

    def test_raises_on_object_tag(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.sanitize_string("<object data='evil.swf'>")
        assert "不安全内容" in str(exc.value.detail)

    def test_raises_on_embed_tag(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.sanitize_string("<embed src='evil.swf'>")
        assert "不安全内容" in str(exc.value.detail)

    def test_escapes_angle_brackets(self):
        from app.utils.input_validator import InputValidator
        result = InputValidator.sanitize_string("<b>bold</b>")
        assert "&lt;" in result
        assert "&gt;" in result

    def test_strips_whitespace(self):
        from app.utils.input_validator import InputValidator
        result = InputValidator.sanitize_string("  hello  ")
        assert result == "hello"

    def test_plain_text_passes(self):
        from app.utils.input_validator import InputValidator
        result = InputValidator.sanitize_string("正常文本")
        assert result == "正常文本"


class TestValidateSqlSafe:
    def test_non_string_converts(self):
        from app.utils.input_validator import InputValidator
        result = InputValidator.validate_sql_safe(456)
        assert result == "456"

    def test_raises_on_union_select(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.validate_sql_safe("1 UNION SELECT * FROM users")
        assert "SQL注入" in str(exc.value.detail)

    def test_raises_on_drop_table(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.validate_sql_safe("DROP TABLE users")
        assert "SQL注入" in str(exc.value.detail)

    def test_raises_on_comment(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.validate_sql_safe("admin' --")
        assert "SQL注入" in str(exc.value.detail)

    def test_raises_on_or_condition(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.validate_sql_safe("1 OR 1=1 OR 1")
        assert "SQL注入" in str(exc.value.detail)

    def test_raises_on_and_condition(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.validate_sql_safe("1 AND 1=1 AND 1")
        assert "SQL注入" in str(exc.value.detail)

    def test_safe_text_passes(self):
        from app.utils.input_validator import InputValidator
        result = InputValidator.validate_sql_safe("hello world")
        assert result == "hello world"

    def test_empty_string_passes(self):
        from app.utils.input_validator import InputValidator
        result = InputValidator.validate_sql_safe("")
        assert result == ""


class TestValidateEmail:
    def test_valid_email(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_email("user@example.com") is True

    def test_valid_email_subdomain(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_email("user@mail.example.com.cn") is True

    def test_invalid_no_at(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_email("userexample.com") is False

    def test_invalid_empty(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_email("") is False


class TestValidatePhone:
    def test_valid_phone(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_phone("13800138000") is True

    def test_invalid_too_short(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_phone("123456789") is False

    def test_invalid_wrong_prefix(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_phone("12345678901") is False

    def test_invalid_empty(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_phone("") is False


class TestValidateIdCard:
    def test_valid_id_card(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_id_card("110101199001011234") is True

    def test_invalid_too_short(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_id_card("12345") is False

    def test_invalid_bad_date(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_id_card("110101199013011234") is False

    def test_invalid_empty(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_id_card("") is False


class TestValidateFileExtension:
    def test_valid_extension(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_file_extension("report.pdf", ["pdf", "docx"]) is True

    def test_invalid_extension(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_file_extension("evil.exe", ["pdf", "docx"]) is False

    def test_no_dot_returns_false(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_file_extension("filewithoutext", ["pdf"]) is False

    def test_case_insensitive(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_file_extension("Report.PDF", ["pdf"]) is True


class TestValidateFileSize:
    def test_within_limit(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_file_size(5 * 1024 * 1024, max_size_mb=10) is True

    def test_exceeds_limit(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_file_size(15 * 1024 * 1024, max_size_mb=10) is False

    def test_exact_limit(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_file_size(10 * 1024 * 1024, max_size_mb=10) is True


class TestValidateNumberRange:
    def test_within_range(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_number_range(5.0, min_val=0.0, max_val=10.0) is True

    def test_below_min(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_number_range(-1.0, min_val=0.0) is False

    def test_above_max(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_number_range(11.0, max_val=10.0) is False

    def test_no_bounds(self):
        from app.utils.input_validator import InputValidator
        assert InputValidator.validate_number_range(42.0) is True


class TestValidateRequiredFields:
    def test_all_fields_present(self):
        from app.utils.input_validator import InputValidator
        InputValidator.validate_required_fields({"name": "张三", "age": 30}, ["name", "age"])

    def test_missing_field_raises(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.validate_required_fields({"name": "张三"}, ["name", "age"])
        assert "缺少必填字段" in str(exc.value.detail)
        assert "age" in str(exc.value.detail)

    def test_none_field_treated_as_missing(self):
        from app.utils.input_validator import InputValidator
        with pytest.raises(HTTPException) as exc:
            InputValidator.validate_required_fields({"name": None}, ["name"])
        assert "缺少必填字段" in str(exc.value.detail)
