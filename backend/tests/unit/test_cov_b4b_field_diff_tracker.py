"""补齐 app.services.field_diff_tracker 覆盖率缺口（41/62/64/77/82 行）."""
from app.services.field_diff_tracker import _format_value, compute_diff, format_diff_for_display


class TestComputeDiff:
    def test_skip_and_underscore_fields_ignored(self):
        diff = compute_diff(
            {"id": 1, "_private": 2, "name": "a"},
            {"id": 2, "_private": 3, "name": "a"},
        )
        assert diff == []


class TestFormatDiffForDisplay:
    def test_added_field(self):
        s = format_diff_for_display([{"field": "name", "label": "名称", "old": None, "new": "新村"}])
        assert s == "新增 名称: 新村"

    def test_removed_field(self):
        s = format_diff_for_display([{"field": "name", "label": "名称", "old": "旧村", "new": None}])
        assert s == "删除 名称: 旧村"


class TestFormatValue:
    def test_none_renders_empty_placeholder(self):
        assert _format_value(None) == "(空)"

    def test_long_string_truncated(self):
        assert _format_value("x" * 60) == "x" * 47 + "..."
