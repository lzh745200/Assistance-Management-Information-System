"""补齐 app.services.smart_report 覆盖率缺口（40/49/61/67 行：空数据与正常分支）."""
from app.services.smart_report import generate_fund_summary, generate_project_summary


class TestFundSummary:
    def test_no_allocated_returns_empty_notice(self):
        assert generate_fund_summary({}) == "暂无经费数据。"

    def test_no_anomalies_reports_normal(self):
        s = generate_fund_summary(
            {"total_allocated": 10000, "total_used": 5000, "utilization_rate": 50.0}
        )
        assert "经费使用正常，无异常告警。" in s


class TestProjectSummary:
    def test_no_projects_returns_empty_notice(self):
        assert generate_project_summary({}) == "暂无项目数据。"

    def test_no_overdue_reports_normal(self):
        s = generate_project_summary({"total": 3, "in_progress": 1, "completed": 2, "overdue": 0})
        assert "所有项目进展正常。" in s
