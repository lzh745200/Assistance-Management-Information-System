from unittest.mock import MagicMock, AsyncMock

import pytest

from app.services.fund_health_service import FundHealthService


@pytest.fixture
def db():
    return AsyncMock()


@pytest.fixture
def svc(db):
    return FundHealthService(db)


@pytest.fixture(autouse=True)
def _execute_result():
    result = MagicMock()
    result.scalar.return_value = 0
    return result


class TestFundHealthService:
    async def _setup(self, svc, db, approved_amount=100, planned_amount=0,
                     amount=0, used_amount=0, anomalies=0, get_returns=True):
        fund = None
        if get_returns:
            fund = MagicMock()
            fund.approved_amount = approved_amount
            fund.planned_amount = planned_amount
            fund.amount = amount
            fund.used_amount = used_amount
        db.get.return_value = fund
        execute_result = MagicMock()
        execute_result.scalar.return_value = anomalies
        db.execute.return_value = execute_result
        return fund

    async def test_fund_not_found(self, svc, db):
        db.get.return_value = None
        result = await svc.calculate_health_score(999)
        assert result == {"fund_id": 999, "score": 0, "status": "not_found"}

    async def test_healthy_score(self, svc, db):
        await self._setup(svc, db, used_amount=30, anomalies=0)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 100
        assert result["status"] == "healthy"

    async def test_unresolved_anomalies_capped(self, svc, db):
        await self._setup(svc, db, used_amount=0, anomalies=5)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 60
        assert result["status"] == "warning"
        assert result["unresolved_anomalies"] == 5

    async def test_over_budget(self, svc, db):
        await self._setup(svc, db, used_amount=120, anomalies=0)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 80
        assert result["status"] == "healthy"

    async def test_near_budget(self, svc, db):
        await self._setup(svc, db, used_amount=95, anomalies=0)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 95
        assert result["status"] == "healthy"

    async def test_over_budget_and_anomalies_combined(self, svc, db):
        await self._setup(svc, db, used_amount=120, anomalies=3)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 50
        assert result["status"] == "critical"

    async def test_critical_status(self, svc, db):
        await self._setup(svc, db, used_amount=120, anomalies=5)
        result = await svc.calculate_health_score(1)
        assert result["status"] == "critical"
        assert result["score"] == 40

    async def test_budget_uses_planned_amount(self, svc, db):
        await self._setup(svc, db, approved_amount=None, planned_amount=200,
                          used_amount=100, anomalies=0)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 100

    async def test_budget_uses_amount_as_fallback(self, svc, db):
        await self._setup(svc, db, approved_amount=None, planned_amount=None,
                          amount=50, used_amount=10, anomalies=0)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 100

    async def test_budget_none_usage_skipped(self, svc, db):
        await self._setup(svc, db, approved_amount=None, planned_amount=None,
                          amount=0, used_amount=10, anomalies=0)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 100

    async def test_min_score_floor(self, svc, db):
        await self._setup(svc, db, used_amount=0, anomalies=100)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 60
        assert result["status"] == "warning"

    async def test_score_clamped_above_100(self, svc, db):
        await self._setup(svc, db, used_amount=80, anomalies=-5)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 100

    async def test_usage_rate_zero(self, svc, db):
        await self._setup(svc, db, used_amount=0, anomalies=0)
        result = await svc.calculate_health_score(1)
        assert result["score"] == 100
        assert result["status"] == "healthy"
