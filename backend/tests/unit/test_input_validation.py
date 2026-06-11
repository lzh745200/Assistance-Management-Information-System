"""Tests for app/core/input_validation.py — 100% coverage."""
import pytest


class TestValidateRequired:
    def test_none(self):
        from app.core.input_validation import validate_required
        ok, msg = validate_required(None)
        assert ok is False
        assert "不能为空" in msg

    def test_empty_string(self):
        from app.core.input_validation import validate_required
        ok, msg = validate_required("")
        assert ok is False
        assert "不能为空" in msg

    def test_whitespace_only(self):
        from app.core.input_validation import validate_required
        ok, msg = validate_required("   ")
        assert ok is False
        assert "不能为空" in msg

    def test_valid(self):
        from app.core.input_validation import validate_required
        ok, msg = validate_required("hello")
        assert ok is True
        assert msg == ""

    def test_custom_field_name(self):
        from app.core.input_validation import validate_required
        ok, msg = validate_required("", "姓名")
        assert "姓名" in msg


class TestValidateUsername:
    def test_none(self):
        from app.core.input_validation import validate_username
        ok, msg = validate_username(None)
        assert ok is False
        assert "不能为空" in msg

    def test_non_string(self):
        from app.core.input_validation import validate_username
        ok, msg = validate_username(123)
        assert ok is False
        assert "不能为空" in msg

    def test_too_short(self):
        from app.core.input_validation import validate_username
        ok, msg = validate_username("ab")
        assert ok is False
        assert "至少3个字符" in msg

    def test_too_long(self):
        from app.core.input_validation import validate_username
        ok, msg = validate_username("a" * 21)
        assert ok is False
        assert "不能超过20个字符" in msg

    def test_invalid_chars(self):
        from app.core.input_validation import validate_username
        ok, msg = validate_username("user name!")
        assert ok is False
        assert "只能包含" in msg

    def test_valid_ascii(self):
        from app.core.input_validation import validate_username
        ok, msg = validate_username("user_name-123")
        assert ok is True
        assert msg == ""

    def test_valid_chinese(self):
        from app.core.input_validation import validate_username
        ok, msg = validate_username("张三测试")
        assert ok is True
        assert msg == ""

    def test_strips_whitespace(self):
        from app.core.input_validation import validate_username
        ok, msg = validate_username("  user123  ")
        assert ok is True
        assert msg == ""


class TestValidatePassword:
    def test_empty(self):
        from app.core.input_validation import validate_password
        ok, msg = validate_password("")
        assert ok is False
        assert "至少8位" in msg

    def test_too_short(self):
        from app.core.input_validation import validate_password
        ok, msg = validate_password("Ab1")
        assert ok is False
        assert "至少8位" in msg

    def test_missing_uppercase(self):
        from app.core.input_validation import validate_password
        ok, msg = validate_password("abcdefgh1")
        assert ok is False
        assert "大写字母" in msg

    def test_missing_lowercase(self):
        from app.core.input_validation import validate_password
        ok, msg = validate_password("ABCDEFGH1")
        assert ok is False
        assert "小写字母" in msg

    def test_missing_digit(self):
        from app.core.input_validation import validate_password
        ok, msg = validate_password("Abcdefghi")
        assert ok is False
        assert "数字" in msg

    def test_valid(self):
        from app.core.input_validation import validate_password
        ok, msg = validate_password("MyPass123")
        assert ok is True
        assert msg == ""


class TestValidatePhone:
    def test_empty(self):
        from app.core.input_validation import validate_phone
        ok, msg = validate_phone("")
        assert ok is False
        assert "不能为空" in msg

    def test_none(self):
        from app.core.input_validation import validate_phone
        ok, msg = validate_phone(None)
        assert ok is False
        assert "不能为空" in msg

    def test_invalid_format(self):
        from app.core.input_validation import validate_phone
        ok, msg = validate_phone("12345678901")
        assert ok is False
        assert "格式不正确" in msg

    def test_valid(self):
        from app.core.input_validation import validate_phone
        ok, msg = validate_phone("13800138000")
        assert ok is True
        assert msg == ""

    def test_valid_with_spaces(self):
        from app.core.input_validation import validate_phone
        ok, msg = validate_phone("  13912345678  ")
        assert ok is True
        assert msg == ""


class TestValidateEmail:
    def test_empty(self):
        from app.core.input_validation import validate_email
        ok, msg = validate_email("")
        assert ok is False
        assert "不能为空" in msg

    def test_none(self):
        from app.core.input_validation import validate_email
        ok, msg = validate_email(None)
        assert ok is False
        assert "不能为空" in msg

    def test_invalid_format(self):
        from app.core.input_validation import validate_email
        ok, msg = validate_email("not-an-email")
        assert ok is False
        assert "格式不正确" in msg

    def test_valid(self):
        from app.core.input_validation import validate_email
        ok, msg = validate_email("test@example.com")
        assert ok is True
        assert msg == ""

    def test_valid_with_spaces(self):
        from app.core.input_validation import validate_email
        ok, msg = validate_email("  user@test.cn  ")
        assert ok is True
        assert msg == ""


class TestValidateIdCard:
    def test_empty(self):
        from app.core.input_validation import validate_id_card
        ok, msg = validate_id_card("")
        assert ok is False
        assert "不能为空" in msg

    def test_none(self):
        from app.core.input_validation import validate_id_card
        ok, msg = validate_id_card(None)
        assert ok is False
        assert "不能为空" in msg

    def test_bad_format_not_18_digits(self):
        from app.core.input_validation import validate_id_card
        ok, msg = validate_id_card("12345")
        assert ok is False
        assert "格式不正确" in msg

    def test_bad_format_invalid_chars(self):
        from app.core.input_validation import validate_id_card
        ok, msg = validate_id_card("12345678901234567Z")
        assert ok is False
        assert "格式不正确" in msg

    def test_bad_checksum(self):
        from app.core.input_validation import validate_id_card
        # Valid format but wrong checksum
        ok, msg = validate_id_card("110101199001011230")
        assert ok is False
        assert "校验码错误" in msg

    def test_valid(self):
        from app.core.input_validation import validate_id_card
        # A valid Chinese ID card number with correct checksum
        ok, msg = validate_id_card("11010519491231002X")
        assert ok is True
        assert msg == ""

    def test_valid_lowercase_x(self):
        from app.core.input_validation import validate_id_card
        ok, msg = validate_id_card("11010519491231002x")
        assert ok is True
        assert msg == ""


class TestValidateChineseName:
    def test_empty(self):
        from app.core.input_validation import validate_chinese_name
        ok, msg = validate_chinese_name("")
        assert ok is False
        assert "不能为空" in msg

    def test_none(self):
        from app.core.input_validation import validate_chinese_name
        ok, msg = validate_chinese_name(None)
        assert ok is False
        assert "不能为空" in msg

    def test_too_short(self):
        from app.core.input_validation import validate_chinese_name
        ok, msg = validate_chinese_name("张")
        assert ok is False
        assert "至少2个字符" in msg

    def test_invalid_format(self):
        from app.core.input_validation import validate_chinese_name
        ok, msg = validate_chinese_name("Zhang San")
        assert ok is False
        assert "格式不正确" in msg

    def test_valid_two_chars(self):
        from app.core.input_validation import validate_chinese_name
        ok, msg = validate_chinese_name("张三")
        assert ok is True
        assert msg == ""

    def test_valid_with_middot(self):
        from app.core.input_validation import validate_chinese_name
        ok, msg = validate_chinese_name("阿卜·杜拉")
        assert ok is True
        assert msg == ""

    def test_valid_strips(self):
        from app.core.input_validation import validate_chinese_name
        ok, msg = validate_chinese_name("  李四  ")
        assert ok is True
        assert msg == ""


class TestValidateSafeString:
    def test_empty(self):
        from app.core.input_validation import validate_safe_string
        ok, msg = validate_safe_string("")
        assert ok is False
        assert "不能为空" in msg

    def test_none(self):
        from app.core.input_validation import validate_safe_string
        ok, msg = validate_safe_string(None)
        assert ok is False
        assert "不能为空" in msg

    def test_invalid_chars(self):
        from app.core.input_validation import validate_safe_string
        ok, msg = validate_safe_string("hello<script>")
        assert ok is False
        assert "不允许的字符" in msg

    def test_valid(self):
        from app.core.input_validation import validate_safe_string
        ok, msg = validate_safe_string("hello world")
        assert ok is True
        assert msg == ""

    def test_custom_field_name(self):
        from app.core.input_validation import validate_safe_string
        ok, msg = validate_safe_string("", "地址")
        assert "地址" in msg


class TestValidateLength:
    def test_empty(self):
        from app.core.input_validation import validate_length
        ok, msg = validate_length("")
        assert ok is False
        assert "不能少于" in msg

    def test_below_min(self):
        from app.core.input_validation import validate_length
        ok, msg = validate_length("ab", min_len=3)
        assert ok is False
        assert "不能少于" in msg

    def test_above_max(self):
        from app.core.input_validation import validate_length
        ok, msg = validate_length("a" * 600, max_len=500)
        assert ok is False
        assert "不能超过" in msg

    def test_valid(self):
        from app.core.input_validation import validate_length
        ok, msg = validate_length("hello")
        assert ok is True
        assert msg == ""

    def test_custom_field_name(self):
        from app.core.input_validation import validate_length
        ok, msg = validate_length("", field_name="标题")
        assert "标题" in msg

    def test_whitespace_stripped_below_min(self):
        from app.core.input_validation import validate_length
        ok, msg = validate_length("   ", min_len=1)
        assert ok is False
        assert "不能少于" in msg


class TestValidatePositiveInt:
    def test_non_numeric_string(self):
        from app.core.input_validation import validate_positive_int
        ok, msg = validate_positive_int("abc")
        assert ok is False
        assert "必须为整数" in msg

    def test_none(self):
        from app.core.input_validation import validate_positive_int
        ok, msg = validate_positive_int(None)
        assert ok is False
        assert "必须为整数" in msg

    def test_float_string(self):
        from app.core.input_validation import validate_positive_int
        ok, msg = validate_positive_int("3.14")
        assert ok is False
        assert "必须为整数" in msg

    def test_zero(self):
        from app.core.input_validation import validate_positive_int
        ok, msg = validate_positive_int(0)
        assert ok is False
        assert "必须为正整数" in msg

    def test_negative(self):
        from app.core.input_validation import validate_positive_int
        ok, msg = validate_positive_int("-5")
        assert ok is False
        assert "必须为正整数" in msg

    def test_valid_int(self):
        from app.core.input_validation import validate_positive_int
        ok, msg = validate_positive_int(42)
        assert ok is True
        assert msg == ""

    def test_valid_string(self):
        from app.core.input_validation import validate_positive_int
        ok, msg = validate_positive_int("100")
        assert ok is True
        assert msg == ""

    def test_custom_field_name(self):
        from app.core.input_validation import validate_positive_int
        ok, msg = validate_positive_int("abc", "年龄")
        assert "年龄" in msg


class TestSanitizeText:
    def test_none(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text(None)
        assert result == ""

    def test_empty_string(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text("")
        assert result == ""

    def test_non_string(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text(123)
        assert 123 == result

    def test_strips_html_tags(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text("Hello <b>world</b>")
        assert result == "Hello world"

    def test_strips_script_tags(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text("x<script>alert(1)</script>y")
        assert result == "xalert(1)y"

    def test_removes_javascript_protocol(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text('<a href="javascript:alert(1)">link</a>')
        assert "javascript" not in result

    def test_removes_onerror(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text('<img src=x onerror="alert(1)">')
        assert "onerror" not in result

    def test_removes_onload(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text('<body onload="evil()">')
        assert "onload" not in result

    def test_removes_vbscript(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text('<a href="vbscript:msgbox(1)">x</a>')
        assert "vbscript" not in result

    def test_preserves_normal_text(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text("正常文本")
        assert result == "正常文本"

    def test_strips_whitespace(self):
        from app.core.input_validation import sanitize_text
        result = sanitize_text("  hello world  ")
        assert result == "hello world"
