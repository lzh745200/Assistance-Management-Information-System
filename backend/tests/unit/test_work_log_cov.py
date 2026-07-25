"""app.models.work_log 覆盖率攻坚测试

直接实例化 WorkLog，覆盖 title / work_date / log_type 三个兼容属性。
"""

from datetime import date

from app.models.work_log import WorkLog

LOG_DATE = date(2024, 3, 5)


class TestCompatProperties:
    def test_title_truncates_content_to_100(self):
        log = WorkLog(user_id=1, log_date=LOG_DATE, content="x" * 150)
        assert log.title == "x" * 100

    def test_title_empty_when_content_missing(self):
        log = WorkLog(user_id=1, log_date=LOG_DATE)
        assert log.title == ""

    def test_work_date_mirrors_log_date(self):
        log = WorkLog(user_id=1, log_date=LOG_DATE, content="内容")
        assert log.work_date == LOG_DATE

    def test_log_type_from_category(self):
        log = WorkLog(user_id=1, log_date=LOG_DATE, content="内容", category="visit")
        assert log.log_type == "visit"

    def test_log_type_defaults_to_daily(self):
        log = WorkLog(user_id=1, log_date=LOG_DATE, content="内容")
        assert log.log_type == "daily"

    def test_repr(self):
        log = WorkLog(user_id=1, log_date=LOG_DATE, content="内容")
        assert repr(log) == f"<WorkLog(id=None, date={LOG_DATE}, user_id=1)>"
