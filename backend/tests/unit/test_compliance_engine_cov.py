# -*- coding: utf-8 -*-
"""compliance_engine 合规校验引擎覆盖率测试（0% → 100%）"""

from unittest.mock import MagicMock

from app.services.compliance_engine import run_compliance_check


def _db(project, funds=None, raises=False):
    db = MagicMock()
    if raises:
        db.query.side_effect = RuntimeError("db down")
        return db
    q_proj = MagicMock()
    q_proj.filter.return_value = q_proj
    q_proj.first.return_value = project
    q_fund = MagicMock()
    q_fund.filter.return_value = q_fund
    q_fund.all.return_value = funds or []
    db.query.side_effect = [q_proj, q_fund]
    return db


def _fund(budget, used, code=None, name=None):
    f = MagicMock()
    f.approved_amount = budget
    f.planned_amount = None
    f.amount = None
    f.used_amount = used
    f.code = code
    f.name = name
    return f


def test_project_not_found():
    r = run_compliance_check(_db(None), 999)
    assert r["passed"] is False
    assert r["violations"] == ["项目 999 不存在"]
    assert r["summary"] == {}


def test_violation_over_rejection_line():
    proj = MagicMock()
    proj.name = "产业项目"
    funds = [_fund(100, 120, code="F001")]  # 偏差20% > 15%
    r = run_compliance_check(_db(proj, funds), 1)
    assert r["passed"] is False
    assert len(r["violations"]) == 1
    assert "F001" in r["violations"][0]
    assert "否决线" in r["violations"][0]
    assert r["summary"]["usage_rate"] == 120.0


def test_warning_over_warning_line():
    proj = MagicMock()
    proj.name = "基建项目"
    funds = [_fund(100, 112, name="修路款")]  # 偏差12% ∈ (10%,15%]
    r = run_compliance_check(_db(proj, funds), 2)
    assert r["passed"] is True
    assert len(r["warnings"]) == 1
    assert "修路款" in r["warnings"][0]
    assert "预警线" in r["warnings"][0]


def test_zero_budget_and_unnamed_fund():
    proj = MagicMock()
    proj.name = "p"
    funds = [_fund(0, 5), _fund(None, 0)]  # budget=0 跳过偏差检测
    r = run_compliance_check(_db(proj, funds), 3)
    assert r["passed"] is True
    assert r["warnings"] == []
    assert r["summary"]["usage_rate"] == 0
    assert r["summary"]["fund_count"] == 2


def test_unnamed_fund_in_violation_message():
    proj = MagicMock()
    proj.name = "p"
    funds = [_fund(100, 200)]  # 无 code/name → 未命名
    r = run_compliance_check(_db(proj, funds), 4)
    assert "未命名" in r["violations"][0]


def test_exception_returns_error_dict():
    r = run_compliance_check(_db(None, raises=True), 5)
    assert r["passed"] is False
    assert "校验过程出错" in r["violations"][0]
    assert "db down" in r["violations"][0]
