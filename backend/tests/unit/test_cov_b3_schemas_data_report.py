"""b3 攻坚：覆盖 app.schemas.data_report 的 DataReportReview status 映射与报错分支"""
import pytest
from pydantic import ValidationError

from app.schemas.data_report import DataReportReview, ReviewActionEnum


class TestDataReportReview:
    def test_status_reject_maps_to_action(self):
        review = DataReportReview(status="reject")
        assert review.action == ReviewActionEnum.REJECT

    def test_status_rejected_maps_to_action(self):
        review = DataReportReview(status=" Rejected ")
        assert review.action == ReviewActionEnum.REJECT

    def test_status_chinese_reject_maps_to_action(self):
        review = DataReportReview(status="驳回")
        assert review.action == ReviewActionEnum.REJECT

    def test_status_approve_maps_to_action(self):
        review = DataReportReview(status="approve")
        assert review.action == ReviewActionEnum.APPROVE

    def test_missing_action_and_status_raises(self):
        with pytest.raises(ValidationError, match="action 不能为空"):
            DataReportReview()

    def test_unknown_status_raises(self):
        with pytest.raises(ValidationError, match="action 不能为空"):
            DataReportReview(status="unknown")
