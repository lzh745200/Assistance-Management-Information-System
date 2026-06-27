"""TDD: 字段级变更差异追踪."""


class TestFieldDiff:
    def test_diff_detects_changed_fields(self):
        from app.services.field_diff_tracker import compute_diff
        old = {"name": "旧名", "amount": 100, "status": "draft"}
        new = {"name": "新名", "amount": 100, "status": "approved"}
        diff = compute_diff(old, new)
        assert len(diff) == 2
        assert diff[0]["field"] == "name"
        assert diff[0]["old"] == "旧名"
        assert diff[0]["new"] == "新名"

    def test_diff_ignores_unchanged(self):
        from app.services.field_diff_tracker import compute_diff
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 1, "b": 2, "c": 4}
        diff = compute_diff(old, new)
        assert len(diff) == 1

    def test_new_fields_detected(self):
        from app.services.field_diff_tracker import compute_diff
        old = {"name": "test"}
        new = {"name": "test", "new_field": "added"}
        diff = compute_diff(old, new)
        assert any(d["field"] == "new_field" and d["old"] is None for d in diff)

    def test_removed_fields_detected(self):
        from app.services.field_diff_tracker import compute_diff
        old = {"name": "test", "removed_field": "gone"}
        new = {"name": "test"}
        diff = compute_diff(old, new)
        assert any(d["field"] == "removed_field" and d["new"] is None for d in diff)

    def test_diff_format_for_display(self):
        from app.services.field_diff_tracker import format_diff_for_display
        diff = [
            {"field": "name", "old": "旧名", "new": "新名"},
            {"field": "amount", "old": 100, "new": 200},
        ]
        display = format_diff_for_display(diff)
        assert "name" in display
        assert "旧名" in display
        assert "新名" in display
        assert "100" in display
        assert "200" in display


class TestFieldLabels:
    def test_get_field_label(self):
        from app.services.field_diff_tracker import get_field_label
        assert get_field_label("village_name") == "帮扶村名称"
        assert get_field_label("amount") == "金额"
        assert get_field_label("unknown_field") == "unknown_field"
