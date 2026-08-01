"""补齐 app.services.import_conflict_detector 覆盖率缺口。

目标行：93（None → None）、95（datetime 原样返回）、98-99（非法字符串 → None）。
"""

from datetime import datetime

from app.services.import_conflict_detector import _parse_ts


class TestParseTs:
    def test_none_returns_none(self):
        assert _parse_ts(None) is None

    def test_datetime_passthrough(self):
        dt = datetime(2026, 1, 1, 12, 0, 0)
        assert _parse_ts(dt) is dt

    def test_invalid_string_returns_none(self):
        assert _parse_ts("not-a-date") is None

    def test_valid_iso_string_parsed(self):
        assert _parse_ts("2026-01-01T00:00:00Z") is not None
