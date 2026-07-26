"""补齐 app.services.fund_service 覆盖率缺口（162-166/173/175/182-183 行：create_fund_for_user 兼容分支）."""
from unittest.mock import MagicMock

from app.services.fund_service import FundService


class TestCreateFundForUser:
    def test_type_compat_with_status_applicant_and_flush_only(self):
        db = MagicMock()
        svc = FundService(db)
        data = MagicMock()
        data.model_dump.return_value = {"type": "扶贫资金", "amount": 1000}

        fund = svc.create_fund_for_user(
            data,
            created_by=9,
            status="pending",
            applicant="张三",
            auto_commit=False,
        )

        assert fund.type == "扶贫资金"
        assert fund.fund_type == "扶贫资金"
        assert fund.status == "pending"
        assert fund.applicant == "张三"
        assert fund.created_by == 9
        db.add.assert_called_once_with(fund)
        db.flush.assert_called_once()
        db.commit.assert_not_called()
