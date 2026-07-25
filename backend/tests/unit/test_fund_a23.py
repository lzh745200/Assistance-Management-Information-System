"""补齐 app.models.fund 覆盖率缺口（a23）。

缺口：_parse_date_value (172-190)、_enrich_fund_time_fields (202-215)、
FundAttachment.to_dict (247)、BudgetRecord.to_dict (276)。
均为纯函数/纯模型方法，直接调用即可，无需数据库。
"""

from datetime import date, datetime

import pytest

from app.models.fund import (
    BudgetRecord,
    Fund,
    FundAttachment,
    _enrich_fund_time_fields,
    _parse_date_value,
)


class TestParseDateValue:
    def test_none_returns_none(self):
        assert _parse_date_value(None) is None

    def test_datetime_returns_date(self):
        assert _parse_date_value(datetime(2024, 5, 1, 10, 30)) == date(2024, 5, 1)

    def test_date_returns_itself(self):
        assert _parse_date_value(date(2024, 5, 1)) == date(2024, 5, 1)

    def test_blank_string_returns_none(self):
        assert _parse_date_value("   ") is None

    def test_iso_string_parsed_by_fromisoformat(self):
        assert _parse_date_value("2024-05-01") == date(2024, 5, 1)

    def test_iso_datetime_string_parsed(self):
        assert _parse_date_value("2024-05-01T10:30:00") == date(2024, 5, 1)

    def test_non_padded_string_falls_back_to_strptime(self):
        # fromisoformat 拒绝非零填充日期，strptime("%Y-%m-%d") 可解析
        assert _parse_date_value("2024-5-1") == date(2024, 5, 1)

    def test_unparseable_string_returns_none(self):
        assert _parse_date_value("not-a-date") is None

    def test_unsupported_type_returns_none(self):
        assert _parse_date_value(20240501) is None


class TestEnrichFundTimeFields:
    def test_date_field_populates_year_month_quarter(self):
        fund = Fund(name="项目经费", date=date(2024, 5, 10))
        _enrich_fund_time_fields(None, None, fund)
        assert fund.date == date(2024, 5, 10)
        assert fund.year == 2024
        assert fund.year_month == "2024-05"
        assert fund.year_quarter == "2024-Q2"

    def test_string_date_normalized_back_to_date(self):
        fund = Fund(name="项目经费", date="2024-11-03")
        _enrich_fund_time_fields(None, None, fund)
        assert fund.date == date(2024, 11, 3)
        assert fund.year == 2024
        assert fund.year_quarter == "2024-Q4"

    def test_fallback_to_application_date(self):
        fund = Fund(name="项目经费", date=None, application_date=datetime(2024, 2, 15, 9, 0))
        _enrich_fund_time_fields(None, None, fund)
        assert fund.year == 2024
        assert fund.year_month == "2024-02"
        assert fund.year_quarter == "2024-Q1"

    def test_no_date_fields_leaves_aggregates_untouched(self):
        fund = Fund(name="项目经费", date=None, application_date=None)
        _enrich_fund_time_fields(None, None, fund)
        assert fund.year is None
        assert fund.year_month is None
        assert fund.year_quarter is None

    def test_third_quarter(self):
        fund = Fund(name="项目经费", date=date(2024, 8, 1))
        _enrich_fund_time_fields(None, None, fund)
        assert fund.year_quarter == "2024-Q3"


class TestFundAttachmentToDict:
    def test_full_fields(self):
        att = FundAttachment(
            id=1,
            fund_id=2,
            file_name="合同.pdf",
            file_path="/uploads/合同.pdf",
            file_size=1024,
            file_type="application/pdf",
            category="contract",
            description="项目合同",
            uploaded_by="admin",
            created_at=datetime(2024, 5, 1, 12, 0),
        )
        d = att.to_dict()
        assert d["id"] == 1
        assert d["fund_id"] == 2
        assert d["file_name"] == "合同.pdf"
        assert d["category"] == "contract"
        assert d["created_at"] == "2024-05-01T12:00:00"

    def test_defaults_when_none(self):
        att = FundAttachment(id=2, fund_id=3, file_name="a.txt", file_path="/a.txt")
        d = att.to_dict()
        assert d["category"] == "other"  # None 回退为 "other"
        assert d["created_at"] is None


class TestBudgetRecordToDict:
    def test_full_fields(self):
        rec = BudgetRecord(
            id=1,
            year=2024,
            category="infrastructure",
            budget_amount=100,
            used_amount=30,
            remaining_reason=None,
            remarks="备注",
            created_at=datetime(2024, 1, 1, 8, 0),
            updated_at=datetime(2024, 6, 1, 8, 0),
        )
        d = rec.to_dict()
        assert d["year"] == 2024
        assert d["budget_amount"] == 100.0
        assert d["used_amount"] == 30.0
        assert d["remaining"] == 70.0
        assert d["created_at"] == "2024-01-01T08:00:00"
        assert d["updated_at"] == "2024-06-01T08:00:00"

    def test_none_amounts_and_timestamps(self):
        rec = BudgetRecord(id=2, year=2024, category="education")
        d = rec.to_dict()
        assert d["budget_amount"] == 0.0
        assert d["used_amount"] == 0.0
        assert d["remaining"] == 0.0
        assert d["created_at"] is None
        assert d["updated_at"] is None
