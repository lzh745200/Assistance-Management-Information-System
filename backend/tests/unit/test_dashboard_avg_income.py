"""dashboard.py _avg_per_capita_income 覆盖率测试（私有函数直接调用）。"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


class _Scope:
    org_ids = []

    @staticmethod
    def filter_by_org_ids(q, *args, **kwargs):
        return q

    def has_full_access(self):
        return True


class _Col:
    def __init__(self, name):
        self.name = name


class _Table:
    def __init__(self, names):
        self.columns = [_Col(n) for n in names]


class TestAvgPerCapitaIncome:
    def test_no_income_columns_returns_zero(self):
        from app.api.v1.data.data.dashboard import _avg_per_capita_income

        fake_model = SimpleNamespace()
        fake_model.__table__ = _Table([])
        with patch("app.models.annual_income.AnnualIncome", fake_model):
            assert _avg_per_capita_income(db=MagicMock(), data_scope=_Scope()) == 0.0

    def test_specific_year_unknown_column(self):
        from app.api.v1.data.data.dashboard import _avg_per_capita_income

        fake_model = SimpleNamespace()
        fake_model.__table__ = _Table(["per_capita_income_2024"])
        with patch("app.models.annual_income.AnnualIncome", fake_model):
            assert _avg_per_capita_income(db=MagicMock(), data_scope=_Scope(), year=2023) == 0.0

    def test_max_year_path(self):
        from app.api.v1.data.data.dashboard import _avg_per_capita_income

        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = 1234.5
        db = MagicMock()
        db.query.return_value = q

        fake_model = SimpleNamespace()
        fake_model.__table__ = _Table(["per_capita_income_2023", "per_capita_income_2024"])
        fake_model.per_capita_income_2024 = MagicMock(name="col-2024")
        with patch("app.models.annual_income.AnnualIncome", fake_model):
            result = _avg_per_capita_income(db=db, data_scope=_Scope())
        assert result == 1234.5

    def test_supported_village_filter_skipped(self):
        from app.api.v1.data.data.dashboard import _avg_per_capita_income

        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = 500.0
        db = MagicMock()
        db.query.return_value = q

        fake_model = SimpleNamespace()
        fake_model.__table__ = _Table(["per_capita_income_2024"])
        fake_model.per_capita_income_2024 = MagicMock(name="col-2024")
        with patch("app.models.annual_income.AnnualIncome", fake_model):
            result = _avg_per_capita_income(db=db, data_scope=_Scope(), year=2024)
        assert result == 500.0
        # hasattr(AnnualIncome, "supported_village_id") False → 不调用 filter 链
        db.query.assert_called()

    def test_exception_returns_zero(self):
        from app.api.v1.data.data.dashboard import _avg_per_capita_income

        fake_model = SimpleNamespace()
        fake_model.__table__ = _Table([])
        with patch("app.models.annual_income.AnnualIncome", fake_model):
            assert _avg_per_capita_income(db=MagicMock(), data_scope=_Scope()) == 0.0

    def test_scalar_none_returns_zero(self):
        from app.api.v1.data.data.dashboard import _avg_per_capita_income

        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = None
        db = MagicMock()
        db.query.return_value = q

        fake_model = SimpleNamespace()
        fake_model.__table__ = _Table(["per_capita_income_2024"])
        fake_model.per_capita_income_2024 = MagicMock(name="col-2024")
        with patch("app.models.annual_income.AnnualIncome", fake_model):
            assert _avg_per_capita_income(db=db, data_scope=_Scope(), year=2024) == 0.0

    def test_with_supported_village_filter(self):
        """hasattr(AnnualIncome, 'supported_village_id') 为 True 时走 filter 链（510-514）。"""
        from app.api.v1.data.data.dashboard import _avg_per_capita_income

        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = 888.0

        inner_q = MagicMock()
        inner_q.filter.return_value = inner_q
        inner_q.scalar.return_value = 1

        db = MagicMock()
        db.query.side_effect = [q, inner_q]

        fake_model = SimpleNamespace()
        fake_model.__table__ = _Table(["per_capita_income_2024"])
        fake_model.per_capita_income_2024 = MagicMock(name="col-2024")
        fake_model.supported_village_id = MagicMock()
        with patch("app.models.annual_income.AnnualIncome", fake_model):
            result = _avg_per_capita_income(db=db, data_scope=_Scope(), year=2024)
        assert result == 888.0
        q.filter.assert_called()

    def test_exception_path(self):
        """AnnualIncome.__table__ 访问抛错 → except 分支（517-518）。"""
        from app.api.v1.data.data.dashboard import _avg_per_capita_income

        fake_model = SimpleNamespace()
        fake_model.__table__ = MagicMock()
        fake_model.__table__.columns = None  # 迭代抛 TypeError
        with patch("app.models.annual_income.AnnualIncome", fake_model):
            assert _avg_per_capita_income(db=MagicMock(), data_scope=_Scope()) == 0.0
