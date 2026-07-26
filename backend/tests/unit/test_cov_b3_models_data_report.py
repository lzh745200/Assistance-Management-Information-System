"""b3 攻坚：覆盖 app.models.data_report 的状态属性与 is_overdue"""
from datetime import datetime, timedelta, timezone

from app.models.data_report import DataReport, ReportStatus


class TestDataReportProperties:
    def test_repr(self):
        r = DataReport(id=1, report_code="RPT001", status=ReportStatus.DRAFT.value)
        assert "RPT001" in repr(r)

    def test_is_pending(self):
        assert DataReport(status=ReportStatus.SUBMITTED.value).is_pending is True
        assert DataReport(status=ReportStatus.DRAFT.value).is_pending is False

    def test_is_editable(self):
        assert DataReport(status=ReportStatus.DRAFT.value).is_editable is True
        assert DataReport(status=ReportStatus.SUBMITTED.value).is_editable is False

    def test_is_reviewable(self):
        assert DataReport(status=ReportStatus.SUBMITTED.value).is_reviewable is True
        assert DataReport(status=ReportStatus.APPROVED.value).is_reviewable is False


class TestDataReportIsOverdue:
    def test_no_deadline(self):
        r = DataReport(status=ReportStatus.DRAFT.value, deadline=None)
        assert r.is_overdue is False

    def test_past_deadline_draft(self):
        r = DataReport(
            status=ReportStatus.DRAFT.value,
            deadline=datetime.now(timezone.utc) - timedelta(days=1),
        )
        assert r.is_overdue is True

    def test_past_deadline_submitted(self):
        r = DataReport(
            status=ReportStatus.SUBMITTED.value,
            deadline=datetime.now(timezone.utc) - timedelta(days=1),
        )
        assert r.is_overdue is False

    def test_future_deadline_draft(self):
        r = DataReport(
            status=ReportStatus.DRAFT.value,
            deadline=datetime.now(timezone.utc) + timedelta(days=1),
        )
        assert r.is_overdue is False
