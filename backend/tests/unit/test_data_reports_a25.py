"""Tests for app.api.v1.data.data.data_reports — 补齐 /received 列表端点。"""

from unittest.mock import MagicMock, patch

from app.api.v1.data.data import data_reports as dr


def _query_mock():
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.offset.return_value = q
    q.limit.return_value = q
    q.count.return_value = 0
    q.all.return_value = []
    return q


class TestListReceivedReports:
    async def test_no_org_returns_empty(self):
        service = MagicMock()
        with patch.object(dr, "get_user_org_id", return_value=None):
            resp = await dr.list_received_reports(
                status=None, page=1, page_size=20,
                current_user=MagicMock(), service=service,
            )
        assert resp["success"] is True
        assert resp["data"]["total"] == 0
        assert resp["data"]["items"] == []

    async def test_with_org_no_status_filter(self):
        service = MagicMock()
        service.db.query.return_value = _query_mock()
        with patch.object(dr, "get_user_org_id", return_value=10):
            resp = await dr.list_received_reports(
                status=None, page=1, page_size=20,
                current_user=MagicMock(), service=service,
            )
        assert resp["success"] is True
        assert resp["data"]["total"] == 0

    async def test_with_org_and_status_filter(self):
        service = MagicMock()
        q = _query_mock()
        service.db.query.return_value = q
        with patch.object(dr, "get_user_org_id", return_value=10):
            resp = await dr.list_received_reports(
                status="submitted", page=2, page_size=10,
                current_user=MagicMock(), service=service,
            )
        assert resp["success"] is True
        assert q.filter.call_count >= 2
