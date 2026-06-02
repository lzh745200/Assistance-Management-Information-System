"""
完整测试 - app.services.ai_service
覆盖率目标: 100%
"""

import pytest

from datetime import date
from unittest.mock import MagicMock, patch
import numpy as np

class TestAIServiceManager:
    """测试 AIServiceManager 类"""

    @pytest.fixture
    def service(self):
        from app.services.ai_service import AIServiceManager
        return AIServiceManager()

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """测试初始化"""
        await service.initialize()
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, service):
        """测试重复初始化"""
        await service.initialize()
        await service.initialize()  # 第二次应该直接返回
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_get_service_status(self, service):
        """测试获取服务状态"""
        result = await service.get_service_status()
        assert "local_analysis" in result
        assert result["local_analysis"]["status"] == "available"

class TestAnalyzeData:
    """测试 analyze_data 方法"""

    @pytest.fixture
    def service(self):
        from app.services.ai_service import AIServiceManager
        return AIServiceManager()

    @pytest.mark.asyncio
    async def test_analyze_summary(self, service):
        """测试摘要分析"""
        data = {"key": "value", "list": [1, 2, 3]}
        result = await service.analyze_data(data, analysis_type="summary")
        assert result["type"] == "summary"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_analyze_unsupported_type(self, service):
        """测试不支持的类型"""
        result = await service.analyze_data({}, analysis_type="unknown")
        assert result["result"] == "unsupported"
        assert "message" in result

    @pytest.mark.asyncio
    async def test_analyze_trend_with_db(self, service):
        """测试趋势分析"""
        mock_db = MagicMock()
        mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            (2021, 10000.0, 5000.0, 5),
            (2022, 11000.0, 5500.0, 5),
            (2023, 12000.0, 6000.0, 5),
        ]

        result = await service.analyze_data({}, analysis_type="trend", db=mock_db)
        assert result["type"] == "income_trend"
        assert result["status"] == "completed"
        assert len(result["yearly_data"]) == 3

    @pytest.mark.asyncio
    async def test_analyze_project_progress_with_db(self, service):
        """测试项目进度分析"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "测试项目"
        mock_project.end_date = date(2024, 1, 1)
        mock_project.status = "in_progress"
        mock_project.budget = 100000
        mock_project.actual_cost = 120000

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_project],  # overdue projects
            [mock_project],  # over budget projects
        ]

        result = await service.analyze_data({}, analysis_type="project_progress", db=mock_db)
        assert result["type"] == "project_progress"
        assert "overdue_projects" in result
        assert "over_budget_projects" in result

    @pytest.mark.asyncio
    async def test_analyze_fund_efficiency_with_db(self, service):
        """测试经费效率分析"""
        mock_db = MagicMock()
        # 村庄级聚合
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (1, 100000.0, 80000.0, 60000.0),
        ]
        # 全局聚合
        mock_db.query.return_value.first.return_value = (100000.0, 80000.0, 60000.0)

        result = await service.analyze_data({}, analysis_type="fund_efficiency", db=mock_db)
        assert result["type"] == "fund_efficiency"
        assert "global" in result
        assert "by_village" in result

    @pytest.mark.asyncio
    async def test_analyze_compare_with_db(self, service):
        """测试村庄对比分析"""
        mock_db = MagicMock()
        mock_db.query.return_value.scalar.return_value = 2023
        mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.side_effect = [
            [("县A", 5, 10000.0, 5000.0)],  # county income
            [("县A", 5000, 1000)],  # county population
        ]

        result = await service.analyze_data({}, analysis_type="compare", db=mock_db)
        assert result["type"] == "village_comparison"
        assert "county_income" in result
        assert "county_population" in result

    @pytest.mark.asyncio
    async def test_analyze_data_exception(self, service):
        """测试分析异常处理"""
        with patch.object(service, '_generate_summary', side_effect=Exception("Test error")):
            with patch('app.services.ai_service.logger') as mock_logger:
                result = await service.analyze_data({}, analysis_type="summary")
                assert "error" in result
                mock_logger.error.assert_called_once()

class TestAnalyzeIncomeTrend:
    """测试 analyze_income_trend 方法"""

    def test_analyze_income_trend_success(self):
        """测试收入趋势分析成功"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            (2021, 10000.0, 5000.0, 5),
            (2022, 11000.0, 5500.0, 5),
            (2023, 12000.0, 6000.0, 5),
        ]

        result = service.analyze_income_trend(mock_db)
        assert result["type"] == "income_trend"
        assert result["status"] == "completed"
        assert result["total_years"] == 3
        assert result["cagr_per_capita_income"] is not None

    def test_analyze_income_trend_insufficient_data(self):
        """测试收入趋势分析 - 数据不足"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            (2023, 12000.0, 6000.0, 5),
        ]

        result = service.analyze_income_trend(mock_db)
        assert result["cagr_per_capita_income"] is None

    def test_analyze_income_trend_zero_first_value(self):
        """测试收入趋势分析 - 首年值为0"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            (2021, 0.0, 5000.0, 5),
            (2022, 11000.0, 5500.0, 5),
            (2023, 12000.0, 6000.0, 5),
        ]

        result = service.analyze_income_trend(mock_db)
        assert result["cagr_per_capita_income"] is None

    def test_analyze_income_trend_none_values(self):
        """测试收入趋势分析 - None值处理"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            (2021, None, None, 5),
            (2022, 11000.0, 5500.0, 5),
        ]

        result = service.analyze_income_trend(mock_db)
        assert result["type"] == "income_trend"
        assert len(result["yearly_data"]) == 2

class TestAnalyzeProjectProgress:
    """测试 analyze_project_progress 方法"""

    def test_analyze_project_progress_success(self):
        """测试项目进度分析成功"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "测试项目"
        mock_project.end_date = date(2024, 1, 1)
        mock_project.status = "in_progress"
        mock_project.budget = 100000
        mock_project.actual_cost = 120000

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_project],  # overdue
            [mock_project],  # over budget
        ]

        result = service.analyze_project_progress(mock_db)
        assert result["type"] == "project_progress"
        assert result["overdue_count"] == 1
        assert result["over_budget_count"] == 1
        assert len(result["overdue_projects"]) == 1
        assert len(result["over_budget_projects"]) == 1

    def test_analyze_project_progress_no_issues(self):
        """测试项目进度分析 - 无问题项目"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [],  # no overdue
            [],  # no over budget
        ]

        result = service.analyze_project_progress(mock_db)
        assert result["overdue_count"] == 0
        assert result["over_budget_count"] == 0

    def test_analyze_project_progress_none_end_date(self):
        """测试项目进度分析 - 无结束日期"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "测试项目"
        mock_project.end_date = None
        mock_project.status = "in_progress"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_project],
            [],
        ]

        result = service.analyze_project_progress(mock_db)
        assert result["overdue_count"] == 1
        assert result["overdue_projects"][0]["overdue_days"] == 0

class TestAnalyzeFundEfficiency:
    """测试 analyze_fund_efficiency 方法"""

    def test_analyze_fund_efficiency_success(self):
        """测试经费效率分析成功"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (1, 100000.0, 80000.0, 60000.0),
            (2, 50000.0, 40000.0, 30000.0),
        ]
        mock_db.query.return_value.first.return_value = (150000.0, 120000.0, 90000.0)

        result = service.analyze_fund_efficiency(mock_db)
        assert result["type"] == "fund_efficiency"
        assert "global" in result
        assert "by_village" in result
        assert len(result["by_village"]) == 2

    def test_analyze_fund_efficiency_zero_total(self):
        """测试经费效率分析 - 总额为0"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (1, 0.0, 0.0, 0.0),
        ]
        mock_db.query.return_value.first.return_value = (0.0, 0.0, 0.0)

        result = service.analyze_fund_efficiency(mock_db)
        assert result["global"]["allocation_rate"] == 0
        assert result["global"]["usage_rate"] == 0

class TestCompareVillages:
    """测试 compare_villages 方法"""

    def test_compare_villages_success(self):
        """测试村庄对比成功"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.scalar.side_effect = [2023, 2023]  # latest_income_year, latest_pop_year
        mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.side_effect = [
            [("县A", 5, 10000.0, 5000.0), ("县B", 3, 8000.0, 4000.0)],
            [("县A", 5000, 1000), ("县B", 3000, 600)],
        ]

        result = service.compare_villages(mock_db)
        assert result["type"] == "village_comparison"
        assert len(result["county_income"]) == 2
        assert len(result["county_population"]) == 2

    def test_compare_villages_no_income_data(self):
        """测试村庄对比 - 无收入数据"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.scalar.side_effect = [None, 2023]
        # 人口数据查询返回 (county, total_pop, total_hh) 三元组
        mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("县A", 5000, 1000),
        ]

        result = service.compare_villages(mock_db)
        assert result["county_income"] == []
        assert len(result["county_population"]) == 1

    def test_compare_villages_none_county(self):
        """测试村庄对比 - None县名处理"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.scalar.side_effect = [2023, 2023]
        mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.side_effect = [
            [(None, 5, 10000.0, 5000.0)],
            [(None, 5000, 1000)],
        ]

        result = service.compare_villages(mock_db)
        assert result["county_income"][0]["county"] == "未知"
        assert result["county_population"][0]["county"] == "未知"

class TestForecastIncomeTrend:
    """测试 forecast_income_trend 方法"""

    def test_forecast_income_trend_success(self):
        """测试收入趋势预测成功"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            (2021, 10000.0, 5000.0),
            (2022, 11000.0, 5500.0),
            (2023, 12000.0, 6000.0),
        ]

        with patch('sklearn.linear_model.LinearRegression') as mock_lr:
            mock_model = MagicMock()
            mock_model.fit.return_value = mock_model
            mock_model.score.return_value = 0.95
            mock_model.predict.side_effect = [
                np.array([13000.0]),
                np.array([6500.0]),
            ]
            mock_lr.return_value = mock_model

            result = service.forecast_income_trend(mock_db, forecast_years=1)

        assert result["type"] == "income_forecast"
        assert result["status"] == "completed"
        assert len(result["forecast"]) == 1
        assert "model_confidence" in result

    def test_forecast_income_trend_insufficient_data(self):
        """测试收入趋势预测 - 数据不足"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            (2023, 12000.0, 6000.0),
        ]

        result = service.forecast_income_trend(mock_db, forecast_years=2)
        assert result["status"] == "insufficient_data"
        assert "message" in result

class TestForecastFundCompletion:
    """测试 forecast_fund_completion 方法"""

    def test_forecast_fund_completion_low_risk(self):
        """测试经费完成率预测 - 低风险"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            100000.0,  # total
            90000.0,   # allocated
            85000.0,   # used (高使用率)
        )

        result = service.forecast_fund_completion(mock_db)
        assert result["type"] == "fund_completion_forecast"
        assert result["risk_level"] == "low"

    def test_forecast_fund_completion_high_risk(self):
        """测试经费完成率预测 - 高风险"""
        from app.services.ai_service import AIServiceManager
        from datetime import date
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            100000.0,  # total
            50000.0,   # allocated (低拨付)
            30000.0,   # used (低使用)
        )

        # 模拟年底(12月)，使得 year_progress 很高，projected_rate 很低
        with patch('app.services.ai_service.date') as mock_date:
            mock_date.today.return_value = date(2024, 12, 20)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            result = service.forecast_fund_completion(mock_db)

        assert result["type"] == "fund_completion_forecast"
        assert result["risk_level"] == "high"

    def test_forecast_fund_completion_zero_allocated(self):
        """测试经费完成率预测 - 拨付为0"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            100000.0,  # total
            0.0,       # allocated
            0.0,       # used
        )

        result = service.forecast_fund_completion(mock_db)
        assert result["current"]["usage_rate"] == 0.0

    def test_forecast_fund_completion_medium_risk(self):
        """测试经费完成率预测 - 中风险 (覆盖442-443行)"""
        from app.services.ai_service import AIServiceManager
        from datetime import date
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            100000.0,  # total
            80000.0,   # allocated
            50000.0,   # used (使用率 0.625)
        )

        # 模拟10月底，使得 projected_rate 在 0.7-0.9 之间
        # year_progress ~ 0.83, projected_rate = 0.625/0.83 ~ 0.75
        with patch('app.services.ai_service.date') as mock_date:
            mock_date.today.return_value = date(2024, 10, 25)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            result = service.forecast_fund_completion(mock_db)

        assert result["type"] == "fund_completion_forecast"
        assert result["risk_level"] == "medium"
        assert result["risk_label"] == "中风险"

class TestGenerateSummary:
    """测试 _generate_summary 方法"""

    def test_generate_summary_list(self):
        """测试生成摘要 - 列表数据"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        data = [1, 2, 3, 4, 5]
        result = service._generate_summary(data)
        assert result["type"] == "summary"
        assert result["total_records"] == 5

    def test_generate_summary_dict(self):
        """测试生成摘要 - 字典数据"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        data = {"a": 1, "b": 2, "c": 3}
        result = service._generate_summary(data)
        assert result["total_records"] == 3

    def test_generate_summary_other(self):
        """测试生成摘要 - 其他类型数据"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        data = "string"
        result = service._generate_summary(data)
        assert result["total_records"] == 0

class TestGetRecommendations:
    """测试 get_recommendations 方法"""

    @pytest.mark.asyncio
    async def test_get_recommendations_with_overdue(self):
        """测试获取建议 - 有逾期项目"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [MagicMock()],  # overdue
            [],  # over budget
        ]

        result = await service.get_recommendations({}, db=mock_db)
        assert len(result) == 1
        assert result[0]["type"] == "warning"
        assert "逾期" in result[0]["content"]

    @pytest.mark.asyncio
    async def test_get_recommendations_with_over_budget(self):
        """测试获取建议 - 有超支项目"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [],  # no overdue
            [MagicMock(), MagicMock()],  # over budget
        ]

        result = await service.get_recommendations({}, db=mock_db)
        assert len(result) == 1
        assert "超支" in result[0]["content"]

    @pytest.mark.asyncio
    async def test_get_recommendations_no_issues(self):
        """测试获取建议 - 无问题"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [],  # no overdue
            [],  # no over budget
        ]

        result = await service.get_recommendations({}, db=mock_db)
        assert len(result) == 1
        assert result[0]["type"] == "suggestion"

    @pytest.mark.asyncio
    async def test_get_recommendations_exception(self):
        """测试获取建议 - 异常处理"""
        from app.services.ai_service import AIServiceManager
        service = AIServiceManager()

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB error")

        with patch('app.services.ai_service.logger') as mock_logger:
            result = await service.get_recommendations({}, db=mock_db)
            assert len(result) == 1
            mock_logger.warning.assert_called_once()

class TestGlobalInstance:
    """测试全局实例"""

    def test_ai_service_manager_global(self):
        """测试全局ai_service_manager实例"""
        from app.services.ai_service import ai_service_manager, AIServiceManager
        assert isinstance(ai_service_manager, AIServiceManager)
