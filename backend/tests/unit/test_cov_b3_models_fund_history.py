"""b3 攻坚：覆盖 app.models.fund_history 的 FundFieldChange/FundOperationLog to_dict"""
from datetime import datetime

from app.models.fund_history import (
    FundFieldChange,
    FundOperationLog,
    FundStatusHistory,
)


class TestFundStatusHistoryToDict:
    def test_to_dict(self):
        h = FundStatusHistory(
            id=1,
            fund_id=10,
            from_status="draft",
            to_status="approved",
            operation_time=datetime(2024, 3, 1, 12, 0, 0),
        )
        d = h.to_dict()
        assert d["to_status"] == "approved"
        assert d["operation_time"] == "2024-03-01T12:00:00"


class TestFundFieldChangeToDict:
    def test_to_dict(self):
        c = FundFieldChange(
            id=2,
            fund_id=10,
            field_name="amount",
            old_value="100",
            new_value="200",
            changed_at=datetime(2024, 3, 2, 8, 30, 0),
        )
        d = c.to_dict()
        assert d["field_name"] == "amount"
        assert d["old_value"] == "100"
        assert d["new_value"] == "200"
        assert d["changed_at"] == "2024-03-02T08:30:00"

    def test_to_dict_none_time(self):
        c = FundFieldChange(id=3, fund_id=10, field_name="remark")
        assert c.to_dict()["changed_at"] is None


class TestFundOperationLogToDict:
    def test_to_dict(self):
        log = FundOperationLog(
            id=4,
            fund_id=10,
            operation_type="attachment_upload",
            operation_detail='{"file": "a.pdf"}',
            created_at=datetime(2024, 3, 3, 9, 0, 0),
        )
        d = log.to_dict()
        assert d["operation_type"] == "attachment_upload"
        assert d["created_at"] == "2024-03-03T09:00:00"

    def test_to_dict_none_time(self):
        log = FundOperationLog(id=5, fund_id=10, operation_type="attachment_delete")
        assert log.to_dict()["created_at"] is None
