"""Tests for app.services.funding.phase_budget_service - zero coverage → 100%"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestPhaseBudgetService:
    """Tests for PhaseBudgetService using AsyncMock for AsyncSession."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock(name="AsyncSession")

    @pytest.fixture
    def service(self, mock_db):
        from app.services.funding.phase_budget_service import PhaseBudgetService
        return PhaseBudgetService(mock_db)

    # -- list_baselines --

    async def test_list_baselines_returns_list(self, service, mock_db):
        mock_baseline = MagicMock(name="baseline")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_baseline]
        mock_db.execute.return_value = mock_result

        result = await service.list_baselines(42)
        mock_db.execute.assert_called_once()
        assert result == [mock_baseline]

    async def test_list_baselines_empty(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.list_baselines(99)
        assert result == []

    # -- create_baseline --

    async def test_create_baseline_creates_and_commits(self, service, mock_db):
        mock_db.refresh = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch(
            "app.services.funding.phase_budget_service.BudgetBaseline",
            autospec=True,
        ) as MockBaseline:
            mock_instance = MagicMock(name="baseline_instance")
            MockBaseline.return_value = mock_instance
            result = await service.create_baseline(fund_id=10, baseline_amount=5000)
            MockBaseline.assert_called_once_with(fund_id=10, baseline_amount=5000)
            mock_db.add.assert_called_once_with(mock_instance)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_instance)
            assert result is mock_instance

    # -- get_budget_summary --

    async def test_get_budget_summary_aggregates_correctly(self, service):
        b1 = MagicMock()
        b1.baseline_amount = 1000.0
        b1.locked_at = None
        b2 = MagicMock()
        b2.baseline_amount = 2000.0
        b2.locked_at = "2024-01-01"
        b3 = MagicMock()
        b3.baseline_amount = 500.0
        b3.locked_at = "2024-02-02"

        service.list_baselines = AsyncMock(return_value=[b1, b2, b3])
        result = await service.get_budget_summary(7)
        assert result["fund_id"] == 7
        assert result["total_baseline_amount"] == 3500.0
        assert result["baseline_count"] == 3
        assert result["locked_count"] == 2

    async def test_get_budget_summary_empty(self, service):
        service.list_baselines = AsyncMock(return_value=[])
        result = await service.get_budget_summary(1)
        assert result["fund_id"] == 1
        assert result["total_baseline_amount"] == 0
        assert result["baseline_count"] == 0
        assert result["locked_count"] == 0

    async def test_get_budget_summary_none_baseline_amount(self, service):
        b1 = MagicMock()
        b1.baseline_amount = None
        b1.locked_at = None
        service.list_baselines = AsyncMock(return_value=[b1])
        result = await service.get_budget_summary(1)
        assert result["total_baseline_amount"] == 0.0
