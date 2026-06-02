"""
AI服务完整测试
覆盖 anomaly_detection_service, nlp_query_service, recommendation_service, trend_prediction_service
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, Mock
from unittest.mock import MagicMock  # auto-added

class TestAnomalyDetectionService:
    """测试异常检测服务"""

    def test_service_import(self):
        """测试服务导入"""
        from app.services.ai.anomaly_detection_service import AnomalyDetectionService
        assert AnomalyDetectionService is not None

    def test_detect_anomalies_empty_data(self):
        """测试空数据异常检测"""
        from app.services.ai.anomaly_detection_service import AnomalyDetectionService

        result = AnomalyDetectionService.detect_anomalies([])
        assert result == []

    def test_detect_anomalies_with_data(self):
        """测试数据异常检测"""
        from app.services.ai.anomaly_detection_service import AnomalyDetectionService

        data = [
            {"id": 1, "value": 100},
            {"id": 2, "value": 105},
            {"id": 3, "value": 98},
            {"id": 4, "value": 1000},  # 异常值
        ]
        result = AnomalyDetectionService.detect_anomalies(data, value_field="value")
        assert isinstance(result, list)

    def test_detect_with_zscore(self):
        """测试Z-Score方法"""
        from app.services.ai.anomaly_detection_service import AnomalyDetectionService

        data = [
            {"id": 1, "value": 100},
            {"id": 2, "value": 105},
            {"id": 3, "value": 98},
            {"id": 4, "value": 200},  # 异常值
        ]
        result = AnomalyDetectionService.detect_anomalies(data, value_field="value", method="zscore")
        assert isinstance(result, list)

    def test_detect_with_iqr(self):
        """测试IQR方法"""
        from app.services.ai.anomaly_detection_service import AnomalyDetectionService

        data = [
            {"id": 1, "value": 100},
            {"id": 2, "value": 105},
            {"id": 3, "value": 98},
            {"id": 4, "value": 200},  # 异常值
        ]
        result = AnomalyDetectionService.detect_anomalies(data, value_field="value", method="iqr")
        assert isinstance(result, list)

class TestNLPQueryService:
    """测试NLP查询服务"""

    def test_service_import(self):
        """测试服务导入"""
        from app.services.ai.nlp_query_service import NLPQueryService
        assert NLPQueryService is not None

    def test_parse_query(self):
        """测试解析查询"""
        from app.services.ai.nlp_query_service import NLPQueryService

        service = NLPQueryService()
        result = service.parse_query("查询2024年的帮扶项目")
        assert isinstance(result, dict)

class TestRecommendationService:
    """测试推荐服务"""

    def test_service_import(self):
        """测试服务导入"""
        from app.services.ai.recommendation_service import RecommendationService
        assert RecommendationService is not None

    def test_recommend_projects(self):
        """测试推荐项目"""
        from app.services.ai.recommendation_service import RecommendationService

        # 验证静态方法存在且签名正确
        import inspect
        sig = inspect.signature(RecommendationService.recommend_projects)
        params = list(sig.parameters.keys())
        assert 'db' in params
        assert 'village_id' in params
        assert 'limit' in params

class TestTrendPredictionService:
    """测试趋势预测服务"""

    def test_service_import(self):
        """测试服务导入"""
        from app.services.ai.trend_prediction_service import TrendPredictionService
        assert TrendPredictionService is not None

    def test_predict_income_trend(self):
        """测试预测收入趋势"""
        from app.services.ai.trend_prediction_service import TrendPredictionService

        service = TrendPredictionService()
        historical_data = [
            {"year": 2020, "income": 10000},
            {"year": 2021, "income": 12000},
            {"year": 2022, "income": 13500},
            {"year": 2023, "income": 15000},
        ]
        result = service.predict_income_trend(historical_data, years_ahead=3)
        assert isinstance(result, dict)

class TestAIServiceIntegration:
    """测试AI服务集成"""

    def test_anomaly_detection_integration(self):
        """测试异常检测集成"""
        from app.services.ai.anomaly_detection_service import AnomalyDetectionService

        # 模拟真实数据
        fund_data = [
            {"id": 1, "amount": 50000, "date": "2024-01-01"},
            {"id": 2, "amount": 52000, "date": "2024-01-02"},
            {"id": 3, "amount": 48000, "date": "2024-01-03"},
            {"id": 4, "amount": 500000, "date": "2024-01-04"},  # 异常
        ]
        anomalies = AnomalyDetectionService.detect_anomalies(
            fund_data, value_field="amount", method="iqr"
        )
        assert isinstance(anomalies, list)
