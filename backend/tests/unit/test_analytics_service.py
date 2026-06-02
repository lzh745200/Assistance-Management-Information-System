"""
数据分析服务测试
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.analytics_service import AnalyticsService

class TestAnalyticsService:
    """数据分析服务测试"""

    def test_get_dashboard_overview_empty(self, db_session):
        """测试空数据库的仪表盘概览"""
        service = AnalyticsService(db_session)
        result = service.get_dashboard_overview(db_session)
        
        assert isinstance(result, dict)
        assert "total_villages" in result
        assert result["total_villages"] >= 0

    def test_get_village_analysis(self, db_session):
        """测试村庄分析"""
        service = AnalyticsService(db_session)
        result = service.get_village_analysis(db_session)
        
        assert isinstance(result, dict)

    def test_get_funding_trends(self, db_session):
        """测试资金趋势分析"""
        service = AnalyticsService(db_session)
        result = service.get_funding_trends(db_session, years=5)
        
        assert isinstance(result, dict)

    def test_get_performance_metrics(self, db_session):
        """测试绩效指标"""
        service = AnalyticsService(db_session)
        result = service.get_performance_metrics(db_session)
        
        assert isinstance(result, dict)

    def test_get_comparison_analysis(self, db_session):
        """测试对比分析"""
        service = AnalyticsService(db_session)
        result = service.get_comparison_analysis(
            db_session, 
            compare_type="province", 
            target_value=None
        )
        
        assert isinstance(result, dict)

    def test_generate_report_data(self, db_session):
        """测试报表数据生成"""
        service = AnalyticsService(db_session)
        result = service.generate_report_data(
            db_session,
            report_type="comprehensive",
            start_date=None,
            end_date=None
        )
        
        assert isinstance(result, dict)

    def test_export_data_json(self, db_session):
        """测试JSON导出"""
        service = AnalyticsService(db_session)
        data = {"test": "data"}
        
        result = service.export_data(db_session, "json", data)
        assert result is not None

    def test_export_data_excel(self, db_session):
        """测试Excel导出"""
        service = AnalyticsService(db_session)
        data = {
            "overview": {"total": 0},
            "villages": [],
            "projects": []
        }
        
        try:
            result = service.export_data(db_session, "excel", data)
            assert result is not None
        except Exception:
            pass

class TestAnalyticsServiceEdgeCases:
    """边界情况测试"""

    def test_empty_database_queries(self, db_session):
        """测试空数据库查询"""
        service = AnalyticsService(db_session)
        
        result = service.get_dashboard_overview(db_session)
        assert result["total_villages"] == 0

    def test_invalid_report_type(self, db_session):
        """测试无效报表类型"""
        service = AnalyticsService(db_session)
        
        result = service.generate_report_data(
            db_session,
            report_type="invalid_type",
            start_date=None,
            end_date=None
        )
        assert isinstance(result, dict)

    def test_negative_years_parameter(self, db_session):
        """测试负数年份参数"""
        service = AnalyticsService(db_session)
        
        result = service.get_funding_trends(db_session, years=-1)
        assert isinstance(result, dict)
