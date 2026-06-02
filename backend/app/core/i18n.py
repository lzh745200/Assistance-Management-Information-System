"""Internationalization core.

Provides a simple translation-layer stub. All user-visible strings are
currently returned in Chinese. When full i18n is needed this module can
be extended to load gettext .mo files or accept an Accept-Language header.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

_TRANSLATIONS: Dict[str, Dict[str, str]] = {}


def register_translations(lang: str, messages: Dict[str, str]) -> None:
    """Register translation strings for a language.

    Args:
        lang: ISO language code (e.g. "zh", "en").
        messages: Mapping of original message -> translated message.
    """
    _TRANSLATIONS.setdefault(lang, {}).update(messages)


def translate(message: str, lang: str = "zh", **kwargs) -> str:
    """Translate a message into the given language.

    Args:
        message: The original (usually Chinese) message.
        lang: Target language code.
        **kwargs: Optional format arguments (applied after translation).

    Returns:
        Translated string.
    """
    translated = _TRANSLATIONS.get(lang, {}).get(message, message)
    if kwargs:
        try:
            return translated.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return translated


def get_display_language(request=None) -> str:
    """Determine the preferred display language from a request.

    Currently always returns "zh".

    Args:
        request: An optional FastAPI Request.

    Returns:
        Language code.
    """
    if request is None:
        return "zh"
    return "zh"


# Register common English translations so the app can toggle to EN easily.
_COMMON_EN: Dict[str, str] = {
    "成功": "Success",
    "失败": "Failed",
    "请求参数错误": "Bad request — invalid parameters",
    "未认证": "Unauthorized",
    "无权访问": "Forbidden",
    "资源不存在": "Resource not found",
    "数据冲突": "Conflict",
    "服务器内部错误": "Internal server error",
    "用户名或密码错误": "Invalid username or password",
    "令牌已过期": "Token expired",
    "令牌无效": "Invalid token",
}

register_translations("en", _COMMON_EN)
