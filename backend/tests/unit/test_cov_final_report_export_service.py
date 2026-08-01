"""
补覆盖测试 - app.services.report_export_service

针对既有测试未覆盖的缺口行：
- generate_school_statistics_report_data()（35-54）：查询成功 / first() 为 None / 查询异常兜底
- generate_village_summary_report_data()（58-73）：scalar 成功 / scalar 为 None 的 or 0 / 异常兜底
- generate_annual_summary_report_data()（77-82）：合并四类报表数据
"""
from unittest.mock import MagicMock

from app.services.report_export_service import ReportExportService


class TestSchoolStatisticsReportData:
    """generate_school_statistics_report_data()（行 35-54）"""

    def test_query_success(self):
        """first() 返回 (学校数, 学生数, 教师数) 元组时按值填充（行 39-51）"""
        db = MagicMock(name="db")
        db.query.return_value.filter.return_value.first.return_value = (3, 120, 15)

        result = ReportExportService().generate_school_statistics_report_data(db, year=2025)

        assert result == {
            "year": 2025,
            "total_schools": 3,
            "total_students": 120,
            "total_teachers": 15,
            "sections": [],
        }

    def test_first_returns_none_falls_back_to_zero(self):
        """first() 返回 None 时 schools 为假值，三项计数取 0（行 47-49 兜底分支）"""
        db = MagicMock(name="db")
        db.query.return_value.filter.return_value.first.return_value = None

        result = ReportExportService().generate_school_statistics_report_data(db, year=2025)

        assert result["total_schools"] == 0
        assert result["total_students"] == 0
        assert result["total_teachers"] == 0
        assert result["sections"] == []

    def test_query_exception_returns_fallback(self):
        """查询抛异常时记录 debug 日志并返回全 0 兜底结构（行 52-54）"""
        db = MagicMock(name="db")
        db.query.side_effect = RuntimeError("db down")

        result = ReportExportService().generate_school_statistics_report_data(db, year=2025)

        assert result == {
            "year": 2025,
            "total_schools": 0,
            "total_students": 0,
            "total_teachers": 0,
            "sections": [],
        }


class TestVillageSummaryReportData:
    """generate_village_summary_report_data()（行 58-73）"""

    def test_scalar_success(self):
        """scalar() 返回村数时填充 total_villages（行 62-70）"""
        db = MagicMock(name="db")
        db.query.return_value.filter.return_value.scalar.return_value = 7

        result = ReportExportService().generate_village_summary_report_data(db, year=2024)

        assert result == {"year": 2024, "total_villages": 7, "sections": []}

    def test_scalar_none_falls_back_to_zero(self):
        """scalar() 返回 None 时走 `or 0` 兜底（行 64）"""
        db = MagicMock(name="db")
        db.query.return_value.filter.return_value.scalar.return_value = None

        result = ReportExportService().generate_village_summary_report_data(db, year=2024)

        assert result == {"year": 2024, "total_villages": 0, "sections": []}

    def test_query_exception_returns_fallback(self):
        """查询抛异常时记录 debug 日志并返回兜底结构（行 71-73）"""
        db = MagicMock(name="db")
        db.query.side_effect = RuntimeError("db down")

        result = ReportExportService().generate_village_summary_report_data(db, year=2024)

        assert result == {"year": 2024, "total_villages": 0, "sections": []}


class TestAnnualSummaryReportData:
    """generate_annual_summary_report_data() 合并村/学校/项目/资金（行 77-89）"""

    def test_merges_all_sub_reports(self):
        db = MagicMock(name="db")
        # village 走 scalar()，school 走 first()；同一链式 mock 上两者并存
        db.query.return_value.filter.return_value.scalar.return_value = 2
        db.query.return_value.filter.return_value.first.return_value = (1, 10, 5)

        result = ReportExportService().generate_annual_summary_report_data(db, year=2026)

        assert result["year"] == 2026
        assert result["village_summary"] == {"year": 2026, "total_villages": 2, "sections": []}
        assert result["school_statistics"]["total_schools"] == 1
        assert result["school_statistics"]["total_students"] == 10
        assert result["school_statistics"]["total_teachers"] == 5
        assert result["project_progress"] == {"year": 2026, "projects": []}
        assert result["fund_detail"] == {"year": 2026, "items": []}
        assert result["sections"] == []
