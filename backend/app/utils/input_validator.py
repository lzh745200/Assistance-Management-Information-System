"""输入验证工具模块

提供XSS防护、SQL注入防护、格式验证等功能
"""

import re
from typing import List, Optional

from fastapi import HTTPException, status


class InputValidator:
    """输入验证器"""

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    SQL_INJECTION_PATTERNS = [
        r"(\s|^)(union|select|insert|update|delete|drop|create|alter|exec|execute)(\s|$)",
        r"(--|#|/\*|\*/)",
        r"(\bor\b.*=.*\bor\b)",
        r"(\band\b.*=.*\band\b)",
    ]

    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """清理字符串，防止XSS攻击

        Args:
            text: 输入文本
            max_length: 最大长度

        Returns:
            清理后的文本
        """
        if not isinstance(text, str):
            return str(text)

        text = text[:max_length]

        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="输入包含不安全内容")

        text = text.replace("<", "&lt;").replace(">", "&gt;")
        return text.strip()

    @staticmethod
    def validate_sql_safe(text: str) -> str:
        """验证SQL安全性

        Args:
            text: 输入文本

        Returns:
            验证后的文本
        """
        if not isinstance(text, str):
            return str(text)

        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="检测到SQL注入风险")

        return text

    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号格式"""
        pattern = r"^1[3-9]\d{9}$"
        return bool(re.match(pattern, phone))

    @staticmethod
    def validate_id_card(id_card: str) -> bool:
        """验证身份证号格式"""
        pattern = r"^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$"
        return bool(re.match(pattern, id_card))

    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """验证文件扩展名"""
        if "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in allowed_extensions

    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
        """验证文件大小"""
        max_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_bytes

    @staticmethod
    def validate_number_range(value: float, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
        """验证数值范围"""
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True

    @staticmethod
    def validate_required_fields(data: dict, required_fields: List[str]) -> None:
        """验证必填字段"""
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]

        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必填字段: {', '.join(missing_fields)}",
            )
