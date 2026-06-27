"""Tests for app.core.i18n - zero coverage → 100%"""

import app.core.i18n as i18n


class TestRegisterTranslations:
    def test_register_new_language(self):
        i18n._TRANSLATIONS.clear()
        i18n.register_translations("en", {"成功": "Success"})
        assert "en" in i18n._TRANSLATIONS
        assert i18n._TRANSLATIONS["en"]["成功"] == "Success"

    def test_register_appends_existing_language(self):
        i18n._TRANSLATIONS.clear()
        i18n.register_translations("en", {"成功": "Success"})
        i18n.register_translations("en", {"失败": "Failed"})
        assert i18n._TRANSLATIONS["en"]["成功"] == "Success"
        assert i18n._TRANSLATIONS["en"]["失败"] == "Failed"

    def test_register_multiple_languages(self):
        i18n._TRANSLATIONS.clear()
        i18n.register_translations("en", {"成功": "Success"})
        i18n.register_translations("ja", {"成功": "成功"})
        assert "en" in i18n._TRANSLATIONS
        assert "ja" in i18n._TRANSLATIONS

    def test_register_overwrites_existing_key(self):
        i18n._TRANSLATIONS.clear()
        i18n.register_translations("en", {"成功": "Success"})
        i18n.register_translations("en", {"成功": "Great Success"})
        assert i18n._TRANSLATIONS["en"]["成功"] == "Great Success"


class TestTranslate:
    def test_translate_existing_key(self):
        i18n._TRANSLATIONS.clear()
        i18n.register_translations("en", {"成功": "Success"})
        assert i18n.translate("成功", "en") == "Success"

    def test_translate_missing_key_returns_original(self):
        i18n._TRANSLATIONS.clear()
        assert i18n.translate("未知词汇", "en") == "未知词汇"

    def test_translate_missing_lang_returns_original(self):
        i18n._TRANSLATIONS.clear()
        assert i18n.translate("成功", "fr") == "成功"

    def test_translate_default_lang_is_zh(self):
        i18n._TRANSLATIONS.clear()
        assert i18n.translate("成功") == "成功"

    def test_translate_with_format_kwargs(self):
        i18n._TRANSLATIONS.clear()
        i18n.register_translations("en", {"Hello {name}": "你好 {name}"})
        assert i18n.translate("Hello {name}", "en", name="World") == "你好 World"

    def test_translate_with_missing_format_key(self):
        i18n._TRANSLATIONS.clear()
        i18n.register_translations("en", {"Hello {name}": "你好 {name}"})
        # Missing format key → falls back to untemplated translation
        result = i18n.translate("Hello {name}", "en", wrong_key="x")
        assert result == "你好 {name}"

    def test_translate_format_with_non_string_return(self):
        i18n._TRANSLATIONS.clear()
        i18n.register_translations("en", {"count": "{n}"})
        result = i18n.translate("count", "en", n=5)
        assert result == "5"

    def test_translate_empty_message(self):
        i18n._TRANSLATIONS.clear()
        assert i18n.translate("", "en") == ""


class TestGetDisplayLanguage:
    def test_no_request_returns_zh(self):
        assert i18n.get_display_language() == "zh"

    def test_with_request_also_returns_zh(self):
        class MockRequest:
            pass
        assert i18n.get_display_language(MockRequest()) == "zh"

    def test_with_none_request_returns_zh(self):
        assert i18n.get_display_language(None) == "zh"
