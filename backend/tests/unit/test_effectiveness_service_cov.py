"""app.services.effectiveness_service 静态方法覆盖率测试

覆盖新增的 3 个 API 静态方法（修复前不存在导致端点必 500）：
- evaluate_village：村不存在 error / 无评估 error / 有评估返回
- get_evaluation_report：无记录 None / 有记录 dict
- compare_evaluations：缺 year1 / 缺 year2 / 成功 delta（含 None 分数回退）
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.effectiveness_service import EffectivenessService


def _ev(**kw):
    defaults = dict(
        village_id=1, year=2026, economic_score=80.0, social_score=85.0,
        ecological_score=75.0, total_score=80.0, rank=1, grade="B",
        indicators={"income": 80}, evaluated_at=datetime(2026, 7, 1, 12, 0, 0),
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _db(village=None, eval_first=None):
    """db.query 返回带 filter/order_by/first 的 mock；village 与评估共用 first 调用序"""
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    db.query.return_value = q
    # evaluate_village 先查村再查评估：first 调两次
    q.first.side_effect = [village, eval_first] if eval_first is not ... else [village]
    return db, q


class TestEvaluateVillage:
    def test_village_not_found(self):
        db, q = _db(village=None)
        q.first.side_effect = [None]
        result = EffectivenessService.evaluate_village(db, 999, 2026, user_id=1)
        assert "不存在" in result["error"]

    def test_no_evaluation(self):
        db, q = _db()
        q.first.side_effect = [SimpleNamespace(id=1, name="幸福村"), None]
        result = EffectivenessService.evaluate_village(db, 1, 2026, user_id=1)
        assert "暂无评估数据" in result["error"]

    def test_success_with_village_name(self):
        db, q = _db()
        q.first.side_effect = [SimpleNamespace(id=1, name="幸福村"), _ev()]
        result = EffectivenessService.evaluate_village(db, 1, 2026, user_id=1)
        assert result["total_score"] == 80.0
        assert result["village_name"] == "幸福村"
        assert result["grade"] == "B"
        assert result["evaluated_at"] == "2026-07-01T12:00:00"

    def test_evaluated_at_none(self):
        db, q = _db()
        q.first.side_effect = [SimpleNamespace(id=1, name="幸福村"), _ev(evaluated_at=None)]
        result = EffectivenessService.evaluate_village(db, 1, 2026, user_id=1)
        assert result["evaluated_at"] is None


class TestGetEvaluationReport:
    def test_none_when_missing(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        assert EffectivenessService.get_evaluation_report(db, 1, 2026) is None

    def test_dict_when_found(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = _ev()
        db.query.return_value = q
        result = EffectivenessService.get_evaluation_report(db, 1, 2026)
        assert result["indicators"] == {"income": 80}
        assert result["rank"] == 1


class TestCompareEvaluations:
    def _db2(self, ev1, ev2):
        """compare 内部两次 _find_evaluation（各 filter→order_by→first）"""
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.side_effect = [ev1, ev2]
        db.query.return_value = q
        return db

    def test_missing_year1(self):
        result = EffectivenessService.compare_evaluations(self._db2(None, _ev()), 1, 2025, 2026)
        assert "2025" in result["error"]

    def test_missing_year2(self):
        result = EffectivenessService.compare_evaluations(self._db2(_ev(), None), 1, 2025, 2026)
        assert "2026" in result["error"]

    def test_success_delta(self):
        ev1 = _ev(year=2025, total_score=70.0, economic_score=70.0)
        ev2 = _ev(year=2026, total_score=85.5, economic_score=80.0)
        result = EffectivenessService.compare_evaluations(self._db2(ev1, ev2), 1, 2025, 2026)
        assert result["delta"]["total_score"] == 15.5
        assert result["delta"]["economic_score"] == 10.0
        assert result["year1_data"]["total_score"] == 70.0
        assert result["year2_data"]["total_score"] == 85.5

    def test_none_scores_fallback(self):
        ev1 = _ev(year=2025, total_score=None, economic_score=None, social_score=None, ecological_score=None)
        ev2 = _ev(year=2026, total_score=None, economic_score=None, social_score=None, ecological_score=None)
        result = EffectivenessService.compare_evaluations(self._db2(ev1, ev2), 1, 2025, 2026)
        assert result["delta"]["total_score"] == 0


def test_compare_effectiveness_periods_two_periods():
    """compare_effectiveness_periods 两时期分支（line 247）"""
    svc = EffectivenessService()
    result = svc.compare_effectiveness_periods(1, "2025-01", "2025-12")
    assert result["period1"] == "2025-01"
    assert result["period2"] == "2025-12"
    assert "improvement" in result
