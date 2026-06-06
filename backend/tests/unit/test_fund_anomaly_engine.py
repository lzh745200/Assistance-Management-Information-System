"""TDD: fund_anomaly_engine — 组合异常检测引擎."""
import pytest


class TestAnomalyResult:
    def test_default_risk_score_is_zero(self):
        from app.services.fund_anomaly_engine import AnomalyResult
        r = AnomalyResult(fund_id=1, fund_name="测试经费", anomalies=[], risk_score=0, risk_level="normal")
        assert r.risk_score == 0 and r.risk_level == "normal"

    def test_danger_level_sets_high_risk(self):
        from app.services.fund_anomaly_engine import AnomalyResult
        r = AnomalyResult(fund_id=2, fund_name="超标", anomalies=[{"type": "overspend", "severity": "danger"}], risk_score=75, risk_level="high")
        assert r.risk_level == "high" and r.risk_score == 75


class TestStatisticalVariance:
    def test_normal_no_anomaly(self):
        from app.services.fund_anomaly_engine import _check_statistical_variance
        r = _check_statistical_variance([100.0, 105.0, 98.0, 102.0, 99.0], threshold_std=2.0)
        assert len(r) == 0

    def test_empty_returns_empty(self):
        from app.services.fund_anomaly_engine import _check_statistical_variance
        assert len(_check_statistical_variance([], threshold_std=2.0)) == 0


class TestRiskScore:
    def test_no_anomalies_zero(self):
        from app.services.fund_anomaly_engine import _calculate_risk_score
        assert _calculate_risk_score([], 0, 100) == 0

    def test_capped_at_100(self):
        from app.services.fund_anomaly_engine import _calculate_risk_score
        assert _calculate_risk_score([{"severity": "danger"}] * 5, 1, 0) <= 100


class TestEscalationTrigger:
    def test_high_risk_escalates(self):
        from app.services.fund_anomaly_engine import should_escalate_approval
        assert should_escalate_approval(55, 100000) is True

    def test_low_risk_no_escalation(self):
        from app.services.fund_anomaly_engine import should_escalate_approval
        assert should_escalate_approval(10, 100000) is False
