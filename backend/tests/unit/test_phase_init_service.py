"""Tests for app.services.funding.phase_init_service - zero coverage → 100%"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestPhaseInitService:
    """Tests for PhaseInitService using AsyncMock for AsyncSession."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(name="AsyncSession")
        db.add = MagicMock()  # add() is synchronous in SQLAlchemy
        return db

    @pytest.fixture
    def service(self, mock_db):
        from app.services.funding.phase_init_service import PhaseInitService
        return PhaseInitService(mock_db)

    # -- list_phases --

    async def test_list_phases_returns_list(self, service, mock_db):
        mock_phase = MagicMock(name="phase")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_phase]
        mock_db.execute.return_value = mock_result

        result = await service.list_phases(5)
        mock_db.execute.assert_called_once()
        assert result == [mock_phase]

    async def test_list_phases_empty(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.list_phases(999)
        assert result == []

    # -- get_phase --

    async def test_get_phase_returns_phase(self, service, mock_db):
        mock_phase = MagicMock(name="phase")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_phase
        mock_db.execute.return_value = mock_result

        result = await service.get_phase(1)
        assert result is mock_phase

    async def test_get_phase_none(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_phase(404)
        assert result is None

    # -- init_phases --

    async def test_init_phases_creates_7_phases(self, service, mock_db):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        with patch(
            "app.services.funding.phase_init_service.ProjectFundPhase",
            autospec=True,
        ) as MockPhase:
            instances = [MagicMock(name=f"phase_{i}") for i in range(7)]
            MockPhase.side_effect = instances

            result = await service.init_phases(project_id=10, fund_id=20)
            assert len(result) == 7
            assert mock_db.add.call_count == 7
            mock_db.commit.assert_called_once()

    async def test_init_phases_first_phase_in_progress(self, service, mock_db):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        with patch(
            "app.services.funding.phase_init_service.ProjectFundPhase",
            autospec=True,
        ) as MockPhase:
            instances = [MagicMock() for _ in range(7)]
            MockPhase.side_effect = instances

            await service.init_phases(project_id=1)
            # First call: phase 1 should be IN_PROGRESS
            first_kw = MockPhase.call_args_list[0][1]
            assert first_kw["phase"] == 1
            # status should be IN_PROGRESS for phase 1
            from app.models.fund_lifecycle import PhaseStatus
            assert first_kw["status"] == PhaseStatus.IN_PROGRESS.value

    async def test_init_phases_other_phases_not_started(self, service, mock_db):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        with patch(
            "app.services.funding.phase_init_service.ProjectFundPhase",
            autospec=True,
        ) as MockPhase:
            instances = [MagicMock() for _ in range(7)]
            MockPhase.side_effect = instances

            await service.init_phases(project_id=1)
            from app.models.fund_lifecycle import PhaseStatus
            # Phase 2 should be NOT_STARTED
            second_kw = MockPhase.call_args_list[1][1]
            assert second_kw["phase"] == 2
            assert second_kw["status"] == PhaseStatus.NOT_STARTED.value

    async def test_init_phases_no_fund_id(self, service, mock_db):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        with patch(
            "app.services.funding.phase_init_service.ProjectFundPhase",
            autospec=True,
        ) as MockPhase:
            instances = [MagicMock() for _ in range(7)]
            MockPhase.side_effect = instances

            result = await service.init_phases(project_id=5)
            assert len(result) == 7
            # All phases should have fund_id=None
            for call in MockPhase.call_args_list:
                assert call[1]["fund_id"] is None

    async def test_init_phases_uses_phase_labels(self, service, mock_db):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        with patch(
            "app.services.funding.phase_init_service.ProjectFundPhase",
            autospec=True,
        ) as MockPhase:
            MockPhase.side_effect = [MagicMock() for _ in range(7)]

            await service.init_phases(project_id=1)
            from app.models.fund_lifecycle import PHASE_LABELS
            for i, call in enumerate(MockPhase.call_args_list):
                expected_remarks = PHASE_LABELS.get(i + 1, f"阶段{i + 1}")
                assert call[1]["remarks"] == expected_remarks
