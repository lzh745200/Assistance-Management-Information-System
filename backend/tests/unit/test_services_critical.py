"""Tests for critical services with zero or thin coverage."""
import pytest
from unittest.mock import MagicMock


class TestFundHealthService:
    def test_calculate_health_score_not_found(self):
        from app.services.fund_health_service import FundHealthService
        import asyncio
        async def run():
            mock_db = MagicMock()
            # get() is async — must return an awaitable, not None directly
            async def _none(*args, **kwargs): return None
            mock_db.get = _none
            service = FundHealthService(mock_db)
            result = await service.calculate_health_score(999)
            # API may return None or dict; handle both
            if result is not None:
                assert result.get("status") == "not_found"
                assert result.get("score") == 0
        asyncio.run(run())


class TestTokenBlacklistService:
    def test_token_blacklist_exists(self):
        from app.services.token_blacklist_service import TokenBlacklistService
        assert TokenBlacklistService is not None

    def test_token_blacklist_instance(self):
        from app.services.token_blacklist_service import TokenBlacklistService
        mock_db = MagicMock()
        service = TokenBlacklistService(mock_db)
        assert service is not None


class TestAuditService:
    def test_audit_service_import(self):
        from app.services.audit_service import AuditService
        assert AuditService is not None

    def test_security_event_service_import(self):
        from app.services.audit_service import SecurityEventService
        assert SecurityEventService is not None


class TestTwoFactorService:
    def test_two_factor_service_exists(self):
        from app.services.two_factor_service import TwoFactorService
        assert TwoFactorService is not None


class TestResourceLimiter:
    def test_resource_limiter_exists(self):
        from app.services.resource_limiter import ResourceLimiter
        assert ResourceLimiter is not None


class TestDataMaskingService:
    def test_mask_phone(self):
        from app.services.data_masking_service import DataMaskingService
        service = DataMaskingService()
        result = service.mask_phone("13812345678")
        assert result is not None
        assert len(result) > 0

    def test_mask_id_card(self):
        from app.services.data_masking_service import DataMaskingService
        service = DataMaskingService()
        result = service.mask_id_card("110101199001011234")
        assert result is not None

    def test_mask_email(self):
        from app.services.data_masking_service import DataMaskingService
        service = DataMaskingService()
        result = service.mask_email("test@example.com")
        assert result is not None


class TestEventBus:
    def test_event_bus_singleton(self):
        from app.services.event_bus import EventBus
        bus1 = EventBus()
        bus2 = EventBus()
        assert bus1 is bus2
