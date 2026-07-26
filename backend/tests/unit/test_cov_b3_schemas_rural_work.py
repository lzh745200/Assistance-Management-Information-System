"""b3 攻坚：覆盖 app.schemas.rural_work 的 _parse_date 时区分支与非字符串分支"""
from datetime import datetime, timezone

from app.schemas.rural_work import RuralWorkCreate, _parse_date


class TestParseDateTimezoneBranch:
    def test_z_suffix_sets_utc(self):
        work = RuralWorkCreate(name="修路", start_date="2024-06-01T12:30:45Z")
        assert work.start_date == datetime(2024, 6, 1, 12, 30, 45, tzinfo=timezone.utc)

    def test_fractional_seconds_z_sets_utc(self):
        work = RuralWorkCreate(name="修路", start_date="2024-06-01T12:30:45.123456Z")
        assert work.start_date.tzinfo == timezone.utc
        assert work.start_date.microsecond == 123456


class TestParseDateNonString:
    def test_non_string_returned_as_is(self):
        assert _parse_date(123) == 123

    def test_none_passthrough(self):
        assert _parse_date(None) is None

    def test_datetime_passthrough(self):
        dt = datetime(2024, 1, 1)
        assert _parse_date(dt) is dt
