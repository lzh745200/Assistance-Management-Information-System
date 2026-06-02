"""Input validation helpers.

Provides reusable validators for common user inputs: usernames, phone
numbers, ID card numbers, email addresses, and safe-string checks.
"""

import re
from typing import Tuple

# Compiled regex patterns
_PAT_USERNAME = re.compile(r"^[\w\-一-龥]{3,20}$")
_PAT_PHONE = re.compile(r"^1[3-9]\d{9}$")
_PAT_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
_PAT_ID_CARD = re.compile(r"^\d{17}[\dXx]$")
_PAT_CHINESE_NAME = re.compile(r"^[一-鿿·]{2,10}$")
_PAT_SAFE_STRING = re.compile(r"^[a-zA-Z0-9一-鿿._\- ]{1,200}$")


def validate_required(value: str, field_name: str = "字段") -> Tuple[bool, str]:
    """Validate that a value is not empty or whitespace-only."""
    if value is None or not str(value).strip():
        return False, f"{field_name}不能为空"
    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format.

    Rules: 3-20 chars; alphanumeric, underscore, dash, Chinese chars.
    """
    if not username or not isinstance(username, str):
        return False, "用户名不能为空"
    username = username.strip()
    if len(username) < 3:
        return False, "用户名长度至少3个字符"
    if len(username) > 20:
        return False, "用户名长度不能超过20个字符"
    if not _PAT_USERNAME.match(username):
        return False, "用户名只能包含字母、数字、下划线、短横线和中文字符"
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength.

    Requirements: >= 8 chars, contains upper, lower, and digit.
    """
    if not password or len(password) < 8:
        return False, "密码长度至少8位"
    if not any(c.isupper() for c in password):
        return False, "密码必须包含大写字母"
    if not any(c.islower() for c in password):
        return False, "密码必须包含小写字母"
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含数字"
    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    """Validate a Chinese mobile phone number."""
    if not phone:
        return False, "手机号不能为空"
    if not _PAT_PHONE.match(phone.strip()):
        return False, "手机号格式不正确"
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate an email address (basic format check)."""
    if not email:
        return False, "邮箱不能为空"
    if not _PAT_EMAIL.match(email.strip()):
        return False, "邮箱格式不正确"
    return True, ""


def validate_id_card(id_card: str) -> Tuple[bool, str]:
    """Validate a Chinese 18-digit ID card number (format + checksum)."""
    if not id_card:
        return False, "身份证号不能为空"
    id_card = id_card.strip().upper()
    if not _PAT_ID_CARD.match(id_card):
        return False, "身份证号格式不正确"

    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_chars = "10X98765432"
    total = sum(int(id_card[i]) * weights[i] for i in range(17))
    if check_chars[total % 11] != id_card[17]:
        return False, "身份证号校验码错误"

    return True, ""


def validate_chinese_name(name: str) -> Tuple[bool, str]:
    """Validate a Chinese personal name."""
    if not name:
        return False, "姓名不能为空"
    name = name.strip()
    if len(name) < 2:
        return False, "姓名长度至少2个字符"
    if not _PAT_CHINESE_NAME.match(name):
        return False, "姓名格式不正确"
    return True, ""


def validate_safe_string(value: str, field_name: str = "字段") -> Tuple[bool, str]:
    """Validate that a string contains only safe characters."""
    if not value:
        return False, f"{field_name}不能为空"
    if not _PAT_SAFE_STRING.match(value.strip()):
        return False, f"{field_name}包含不允许的字符"
    return True, ""


def validate_length(
    value: str, min_len: int = 1, max_len: int = 500, field_name: str = "字段"
) -> Tuple[bool, str]:
    """Validate string length within a range."""
    if not value or len(value.strip()) < min_len:
        return False, f"{field_name}长度不能少于{min_len}个字符"
    if len(value) > max_len:
        return False, f"{field_name}长度不能超过{max_len}个字符"
    return True, ""


def validate_positive_int(value, field_name: str = "字段") -> Tuple[bool, str]:
    """Validate that a value is a positive integer."""
    try:
        v = int(value)
        if v <= 0:
            return False, f"{field_name}必须为正整数"
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name}必须为整数"


def sanitize_text(value: str) -> str:
    """Strip dangerous HTML/script tags and return clean text."""
    if not value or not isinstance(value, str):
        return value or ""
    clean = re.sub(r"<[^>]*>", "", value)
    clean = re.sub(r"(?i)(javascript|vbscript|onerror|onload)\s*:", "", clean)
    return clean.strip()
