"""Tests for app.services.metrics_service — 100% coverage target."""

from unittest.mock import AsyncMock, MagicMock, patch


from app.services.metrics_service import MetricsService


class TestMetricsService:
    @patch("app.services.metrics_service.BusinessMetricsService")
    def test_get_kpi_dashboard(self, mock_bms_class):
        mock_db = MagicMock()
        mock_instance = mock_bms_class.return_value
        mock_instance.get_all_metrics = MagicMock(return_value={"total_funds": 100})

        result = MetricsService.get_kpi_dashboard(mock_db)
        # get_kpi_dashboard is async — we get back a coroutine
        import asyncio
        result = asyncio.run(result)

        mock_bms_class.assert_called_once_with()
        mock_instance.get_all_metrics.assert_called_once()
        assert result == {"total_funds": 100}
