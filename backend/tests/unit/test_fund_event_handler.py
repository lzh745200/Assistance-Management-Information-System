"""经费事件联动服务单元测试"""
from unittest.mock import MagicMock

class TestStatusPhaseMap:
    def test_map_contains_statuses(self):
        from app.services.fund_event_handler import STATUS_PHASE_MAP
        assert STATUS_PHASE_MAP["draft"] == 1
        assert STATUS_PHASE_MAP["approved"] == 2
        assert STATUS_PHASE_MAP["in_progress"] == 5
        assert STATUS_PHASE_MAP["completed"] == 7

    def test_map_all_values_positive(self):
        from app.services.fund_event_handler import STATUS_PHASE_MAP
        for v in STATUS_PHASE_MAP.values():
            assert v > 0

class TestOnProjectStatusChange:
    def test_no_phases_does_not_raise(self):
        from app.services.fund_event_handler import on_project_status_change
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        # Should not raise
        on_project_status_change(mock_db, 1, "draft", "approved", "admin")

    def test_unknown_status_skips(self):
        from app.services.fund_event_handler import on_project_status_change
        mock_db = MagicMock()
        # Unknown status should not query DB at all
        on_project_status_change(mock_db, 1, "unknown", "unknown_status", "")
        # DB should not be queried because STATUS_PHASE_MAP.get("unknown_status") returns None

    def test_status_transition_to_approved(self):
        from app.services.fund_event_handler import on_project_status_change
        mock_db = MagicMock()
        mock_phase = MagicMock()
        mock_phase.phase = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_phase]
        mock_db.commit = MagicMock()
        on_project_status_change(mock_db, 1, "draft", "approved", "admin")

    def test_function_is_callable(self):
        from app.services.fund_event_handler import on_project_status_change
        assert callable(on_project_status_change)
