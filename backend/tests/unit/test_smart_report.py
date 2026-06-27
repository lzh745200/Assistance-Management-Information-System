"""TDD: 智能报表摘要生成."""


class TestSmartSummary:
    def test_generate_village_summary(self):
        from app.services.smart_report import generate_village_summary
        data = {
            "total_villages": 50,
            "total_population": 25000,
            "total_funds": 5000000.0,
            "total_projects": 12,
            "completed_projects": 8,
            "avg_income_growth": 15.3,
        }
        summary = generate_village_summary(data)
        assert "50" in summary or "个帮扶村" in summary
        assert "25000" in summary or "人" in summary
        assert len(summary) > 50

    def test_generate_fund_summary(self):
        from app.services.smart_report import generate_fund_summary
        data = {
            "total_allocated": 10000000.0,
            "total_used": 8500000.0,
            "utilization_rate": 85.0,
            "anomaly_count": 3,
            "warning_count": 5,
        }
        summary = generate_fund_summary(data)
        assert "85" in summary or "%" in summary
        assert "3" in summary or "异常" in summary
        assert len(summary) > 30

    def test_generate_project_summary(self):
        from app.services.smart_report import generate_project_summary
        data = {
            "total": 20,
            "in_progress": 8,
            "completed": 10,
            "overdue": 2,
            "on_track": 10,
        }
        summary = generate_project_summary(data)
        assert "20" in summary or "个项目" in summary
        assert "2" in summary or "延期" in summary

    def test_empty_data_handled(self):
        from app.services.smart_report import generate_village_summary
        summary = generate_village_summary({})
        assert "暂无" in summary or "无数据" in summary or len(summary) > 0


class TestReportTemplate:
    def test_fill_template(self):
        from app.services.smart_report import fill_report_template
        result = fill_report_template(
            "日期: {date}, 作者: {author}, 亮点: {highlights}",
            {"date": "2026-06-06", "author": "系统", "highlights": "新增3个示范村"},
        )
        assert "2026-06-06" in result
        assert "系统" in result
        assert "示范村" in result

    def test_template_with_missing_vars(self):
        from app.services.smart_report import fill_report_template
        result = fill_report_template(
            "年度总结 - {year}年",
            {"year": "2026"},
        )
        assert "2026" in result
