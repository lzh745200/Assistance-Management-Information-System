"""
经费管理服务层单元测试
覆盖: app/services/fund_service.py
"""
import pytest


def _import_fund_service():
    """延迟导入以避免循环依赖"""
    from app.services.fund_service import (
        calculate_utilization_rate,
        calculate_total_from_yearly_values,
        FundStatistics,
        YearlyFundSummary,
        FUND_TYPES,
    )
    return (
        calculate_utilization_rate,
        calculate_total_from_yearly_values,
        FundStatistics,
        YearlyFundSummary,
        FUND_TYPES,
    )

class TestCalculateUtilizationRate:
    def setup_method(self):
        self.fn = _import_fund_service()[0]

    def test_normal_rate(self):
        assert self.fn(50, 100) == 50.0

    def test_full_utilization(self):
        assert self.fn(100, 100) == 100.0

    def test_zero_planned_zero_actual(self):
        assert self.fn(0, 0) == 0.0

    def test_zero_planned_positive_actual(self):
        assert self.fn(50, 0) == 100.0

    def test_negative_planned_zero_actual(self):
        assert self.fn(0, -10) == 0.0

    def test_over_utilization_capped(self):
        """超额投入应被截止为100%"""
        assert self.fn(200, 100) == 100.0

    def test_partial_utilization(self):
        rate = self.fn(33, 100)
        assert rate == 33.0

    def test_small_values(self):
        rate = self.fn(0.5, 1.0)
        assert rate == 50.0

    def test_large_values(self):
        rate = self.fn(500000, 1000000)
        assert rate == 50.0

# ==================== calculate_total_from_yearly_values 测试 ====================

class TestCalculateTotalFromYearlyValues:
    def setup_method(self):
        self.fn = _import_fund_service()[1]

    def test_normal_values(self):
        assert self.fn([10.0, 20.0, 30.0]) == 60.0

    def test_empty_list(self):
        assert self.fn([]) == 0

    def test_with_none_values(self):
        assert self.fn([10.0, None, 30.0]) == 40.0

    def test_all_none(self):
        assert self.fn([None, None]) == 0

    def test_single_value(self):
        assert self.fn([100.0]) == 100.0

    def test_negative_values(self):
        """负值也应参与求和"""
        assert self.fn([10.0, -5.0, 20.0]) == 25.0

# ==================== FundStatistics 测试 ====================

class TestFundStatistics:
    def setup_method(self):
        self.FundStatistics = _import_fund_service()[2]

    def test_create_default(self):
        fs = self.FundStatistics("transition", "过渡期经费")
        assert fs.fund_type == "transition"
        assert fs.fund_type_label == "过渡期经费"
        assert fs.military_investment == 0.0
        assert fs.local_investment == 0.0
        assert fs.planned_investment == 0.0
        assert fs.total_investment == 0.0
        assert fs.utilization_rate == 0.0

    def test_create_with_values(self):
        fs = self.FundStatistics(
            fund_type="industry",
            fund_type_label="产业帮扶",
            military_investment=100.0,
            local_investment=50.0,
            planned_investment=200.0,
            total_investment=150.0,
            utilization_rate=75.0,
        )
        assert fs.military_investment == 100.0
        assert fs.local_investment == 50.0
        assert fs.utilization_rate == 75.0

    def test_to_dict(self):
        fs = self.FundStatistics(
            "infrastructure", "基础设施",
            military_investment=100.123,
            local_investment=50.456,
            planned_investment=200.789,
            total_investment=150.579,
            utilization_rate=75.123,
        )
        d = fs.to_dict()
        assert d["fund_type"] == "infrastructure"
        assert d["fund_type_label"] == "基础设施"
        assert d["military_investment"] == 100.12
        assert d["local_investment"] == 50.46
        assert d["planned_investment"] == 200.79
        assert d["total_investment"] == 150.58
        assert d["utilization_rate"] == 75.12

    def test_to_dict_zero_values(self):
        fs = self.FundStatistics("education", "教育帮扶")
        d = fs.to_dict()
        assert d["military_investment"] == 0.0
        assert d["utilization_rate"] == 0.0

# ==================== YearlyFundSummary 测试 ====================

class TestYearlyFundSummary:
    def setup_method(self):
        _, _, self.FundStatistics, self.YearlyFundSummary, _ = _import_fund_service()

    def test_create_default(self):
        summary = self.YearlyFundSummary(year=2025)
        assert summary.year == 2025
        assert summary.total_military == 0.0
        assert summary.total_local == 0.0
        assert summary.total_planned == 0.0
        assert summary.total_actual == 0.0
        assert summary.utilization_rate == 0.0
        assert summary.by_type == {}

    def test_create_with_values(self):
        by_type = {
            "transition": self.FundStatistics("transition", "过渡期经费", total_investment=100.0),
        }
        summary = self.YearlyFundSummary(
            year=2024,
            total_military=200.0,
            total_local=100.0,
            total_planned=400.0,
            total_actual=300.0,
            utilization_rate=75.0,
            by_type=by_type,
        )
        assert summary.total_military == 200.0
        assert len(summary.by_type) == 1

    def test_to_dict(self):
        by_type = {
            "transition": self.FundStatistics("transition", "过渡期经费", total_investment=100.123),
        }
        summary = self.YearlyFundSummary(
            year=2024,
            total_military=200.567,
            total_local=100.234,
            total_planned=400.789,
            total_actual=300.801,
            utilization_rate=75.123,
            by_type=by_type,
        )
        d = summary.to_dict()
        assert d["year"] == 2024
        assert d["total_military"] == 200.57
        assert d["total_local"] == 100.23
        assert d["total_planned"] == 400.79
        assert d["total_actual"] == 300.8
        assert d["utilization_rate"] == 75.12
        assert "transition" in d["by_type"]
        assert d["by_type"]["transition"]["fund_type"] == "transition"

    def test_to_dict_empty_by_type(self):
        summary = self.YearlyFundSummary(year=2023)
        d = summary.to_dict()
        assert d["by_type"] == {}

# ==================== FUND_TYPES 常量测试 ====================

class TestFundTypes:
    def setup_method(self):
        self.FUND_TYPES = _import_fund_service()[4]

    def test_all_types_present(self):
        expected = ["transition", "industry", "infrastructure", "party_building", "medical", "education"]
        for t in expected:
            assert t in self.FUND_TYPES

    def test_labels_non_empty(self):
        for key, label in self.FUND_TYPES.items():
            assert isinstance(label, str)
            assert len(label) > 0
