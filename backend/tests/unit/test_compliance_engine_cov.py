"""app.services.compliance_engine 覆盖率攻坚测试

覆盖 run_compliance_check 全部分支：
- 项目不存在 → violations
- 无经费记录 → 零预算通过
- 偏差率 >15% → 否决线 violations
- 10%<偏差率<=15% → 预警线 warnings
- 偏差率<=10% → 无告警
- budget=0 → 跳过偏差检测
- 基金 code/name 为空 → '未命名' 回退
- 查询异常 → 降级 violations
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.compliance_engine import run_compliance_check


def _db(project=None, funds=None, raise_on=None):
    db = MagicMock()

    def _query(model):
        if raise_on is not None:
            raise raise_on
        q = MagicMock()
        q.filter.return_value = q
        if model.__name__ == "Project":
            q.first.return_value = project
        else:
            q.all.return_value = funds or []
        return q

    db.query.side_effect = _query
    return db


def _fund(**kw):
    defaults = dict(
        approved_amount=100.0, planned_amount=None, amount=None,
        used_amount=100.0, code="F001", name="经费1",
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


class TestComplianceCheck:
    def test_project_not_found(self):
        result = run_compliance_check(_db(project=None), 999)
        assert result["passed"] is False
        assert "项目 999 不存在" in result["violations"]
        assert result["summary"] == {}

    def test_no_funds_zero_budget(self):
        project = SimpleNamespace(id=1, name="项目A")
        result = run_compliance_check(_db(project=project, funds=[]), 1)
        assert result["passed"] is True
        assert result["summary"]["usage_rate"] == 0
        assert result["summary"]["fund_count"] == 0

    def test_within_warning_line(self):
        project = SimpleNamespace(id=1, name="项目A")
        # 偏差 5% < 10% 预警线
        fund = _fund(approved_amount=100.0, used_amount=105.0)
        result = run_compliance_check(_db(project=project, funds=[fund]), 1)
        assert result["passed"] is True
        assert result["warnings"] == []
        assert result["violations"] == []
        assert result["summary"]["total_budget"] == 100.0
        assert result["summary"]["total_used"] == 105.0

    def test_warning_line_exceeded(self):
        project = SimpleNamespace(id=1, name="项目A")
        # 偏差 12% > 10% 预警线，<=15% 否决线
        fund = _fund(approved_amount=100.0, used_amount=112.0)
        result = run_compliance_check(_db(project=project, funds=[fund]), 1)
        assert result["passed"] is True
        assert len(result["warnings"]) == 1
        assert "12.0%" in result["warnings"][0]
        assert "预警线" in result["warnings"][0]

    def test_rejection_line_exceeded(self):
        project = SimpleNamespace(id=1, name="项目A")
        # 偏差 20% > 15% 否决线
        fund = _fund(approved_amount=100.0, used_amount=120.0)
        result = run_compliance_check(_db(project=project, funds=[fund]), 1)
        assert result["passed"] is False
        assert len(result["violations"]) == 1
        assert "否决线" in result["violations"][0]

    def test_zero_budget_skipped(self):
        project = SimpleNamespace(id=1, name="项目A")
        # approved/planned/amount 全空 → budget=0 → 跳过偏差检测
        fund = _fund(approved_amount=None, planned_amount=None, amount=None, used_amount=50.0)
        result = run_compliance_check(_db(project=project, funds=[fund]), 1)
        assert result["passed"] is True
        assert result["warnings"] == []
        assert result["summary"]["total_budget"] == 0.0
        assert result["summary"]["total_used"] == 50.0

    def test_budget_fallback_chain(self):
        project = SimpleNamespace(id=1, name="项目A")
        # approved 空 → 用 planned；planned 也空 → 用 amount
        f1 = _fund(approved_amount=None, planned_amount=200.0, used_amount=200.0)
        f2 = _fund(approved_amount=None, planned_amount=None, amount=300.0, used_amount=300.0)
        result = run_compliance_check(_db(project=project, funds=[f1, f2]), 1)
        assert result["summary"]["total_budget"] == 500.0

    def test_unnamed_fund_fallback(self):
        project = SimpleNamespace(id=1, name="项目A")
        fund = _fund(approved_amount=100.0, used_amount=120.0, code=None, name=None)
        result = run_compliance_check(_db(project=project, funds=[fund]), 1)
        assert "未命名" in result["violations"][0]

    def test_usage_rate_calculation(self):
        project = SimpleNamespace(id=1, name="项目A")
        fund = _fund(approved_amount=200.0, used_amount=150.0)
        result = run_compliance_check(_db(project=project, funds=[fund]), 1)
        assert result["summary"]["usage_rate"] == 75.0

    def test_exception_degrades(self):
        result = run_compliance_check(_db(raise_on=Exception("db gone")), 1)
        assert result["passed"] is False
        assert "校验过程出错" in result["violations"][0]
        assert result["summary"] == {}
