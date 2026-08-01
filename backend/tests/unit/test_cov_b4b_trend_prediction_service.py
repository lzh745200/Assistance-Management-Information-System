"""补齐 app.services.ai.trend_prediction_service 覆盖率缺口（102-125 行：Prophet 预测主路径）."""
from unittest.mock import MagicMock, patch

import pandas as pd

from app.services.ai.trend_prediction_service import TrendPredictionService

_MOD = "app.services.ai.trend_prediction_service"


class TestPredictWithProphet:
    def test_prophet_branch_returns_predictions(self):
        history = [{"date": f"2023-0{i}-01", "value": float(i)} for i in range(1, 4)]
        forecast = pd.DataFrame(
            {
                "ds": pd.to_datetime(
                    ["2023-01-01", "2023-02-01", "2023-03-01", "2023-04-01", "2023-05-01"]
                ),
                "yhat": [1.0, 2.0, 3.0, 4.0, 5.0],
                "yhat_lower": [0.5] * 5,
                "yhat_upper": [5.5] * 5,
            }
        )
        model = MagicMock()
        model.predict.return_value = forecast

        # create=True：prophet 未安装时模块无 Prophet 属性（try/except 导入），patch 需创建
        with patch(f"{_MOD}.Prophet", return_value=model, create=True):
            result = TrendPredictionService._predict_with_prophet(history, 2, "date", "value")

        assert result["method"] == "prophet"
        assert result["model_params"] == {"yearly_seasonality": True, "interval_width": 0.95}
        assert result["predictions"] == [
            {"date": "2023-04-01", "value": 4.0},
            {"date": "2023-05-01", "value": 5.0},
        ]
        assert result["confidence_intervals"] == [
            {"date": "2023-04-01", "lower": 0.5, "upper": 5.5},
            {"date": "2023-05-01", "lower": 0.5, "upper": 5.5},
        ]
        model.fit.assert_called_once()
