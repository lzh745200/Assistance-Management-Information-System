"""补齐 app.services.fund_event_handler 覆盖率缺口（62/90-92/96 行）."""
from unittest.mock import MagicMock

from app.models.fund_lifecycle import PhaseStatus, ProjectFundPhase
from app.services.fund_event_handler import FundEventHandler, on_project_status_change


def _db_with(phases, funds):
    db = MagicMock()
    q_phase = MagicMock()
    q_phase.filter.return_value.order_by.return_value.all.return_value = phases
    q_fund = MagicMock()
    q_fund.filter.return_value.all.return_value = funds
    db.query.side_effect = lambda model: q_phase if model is ProjectFundPhase else q_fund
    return db


class TestOnProjectStatusChange:
    def test_syncs_fund_lifecycle_phase(self):
        phase = MagicMock(
            phase=1,
            status=PhaseStatus.NOT_STARTED.value,
            completed_at=None,
            operator=None,
        )
        fund = MagicMock()
        db = _db_with([phase], [fund])

        on_project_status_change(db, 5, "draft", "approved", operator="op")

        assert fund.lifecycle_phase == 2
        assert phase.status == PhaseStatus.COMPLETED.value
        db.flush.assert_called_once()


class TestFundEventHandlerWrapper:
    def test_without_db_returns_none(self):
        handler = FundEventHandler()
        assert handler.on_project_status_change(1, "draft", "approved") is None

    def test_with_db_delegates(self):
        phase = MagicMock(
            phase=1,
            status=PhaseStatus.COMPLETED.value,
            completed_at="x",
            operator="y",
        )
        handler = FundEventHandler(_db_with([phase], []))
        handler.on_project_status_change(5, "draft", "approved")

    def test_create_returns_handler_with_db(self):
        db = MagicMock()
        handler = FundEventHandler.create(db)
        assert isinstance(handler, FundEventHandler)
        assert handler.db is db
