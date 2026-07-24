"""app.utils.date_type_handler 覆盖率攻坚测试

Date 类型安全防护：_coerce_to_date 全类型分支、_get_date_columns、
监听器工厂与注册流程（含幂等与 ImportError 降级）。
"""

import sys
from datetime import date, datetime
from unittest.mock import patch

from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.orm import declarative_base

import app.utils.date_type_handler as dth
from app.utils.date_type_handler import (
    _coerce_to_date,
    _get_date_columns,
    _make_before_listener,
    register_date_type_handlers,
)


# ==================== _coerce_to_date ====================


class TestCoerceToDate:
    def test_none(self):
        assert _coerce_to_date(None) is None

    def test_plain_date_returned_as_is(self):
        d = date(2026, 7, 25)
        assert _coerce_to_date(d) is d

    def test_datetime_truncated(self):
        assert _coerce_to_date(datetime(2026, 7, 25, 10, 30)) == date(2026, 7, 25)

    def test_iso_string(self):
        assert _coerce_to_date("2026-07-25") == date(2026, 7, 25)

    def test_iso_string_with_whitespace(self):
        assert _coerce_to_date("  2026-07-25  ") == date(2026, 7, 25)

    def test_iso_datetime_string(self):
        assert _coerce_to_date("2026-07-25T10:30:00") == date(2026, 7, 25)

    def test_empty_string_returns_none(self):
        assert _coerce_to_date("   ") is None

    def test_strptime_fallback(self):
        """fromisoformat 拒绝但前10字符是合法日期 → strptime 兜底"""
        assert _coerce_to_date("2026-07-25 附加文本") == date(2026, 7, 25)

    def test_unparseable_string_returned_as_is(self):
        assert _coerce_to_date("not-a-date") == "not-a-date"

    def test_other_types_returned_as_is(self):
        assert _coerce_to_date(12345) == 12345


# ==================== _get_date_columns ====================


class TestGetDateColumns:
    def test_model_without_table(self):
        class NoTable:
            pass

        assert _get_date_columns(NoTable) == []

    def test_model_with_date_columns(self):
        Base = declarative_base()

        class M(Base):
            __tablename__ = "t_date_cols"
            id = Column(Integer, primary_key=True)
            d = Column(Date)
            s = Column(String(10))

        assert _get_date_columns(M) == ["d"]


# ==================== _make_before_listener ====================


class TestBeforeListener:
    def test_coerces_datetime_and_keeps_date(self):
        listener = _make_before_listener(["d1", "d2", "d3"])

        class Target:
            d1 = datetime(2026, 7, 25, 8, 0)
            d2 = date(2026, 7, 24)
            d3 = None

        t = Target()
        original_d2 = t.d2
        listener(None, None, t)
        assert t.d1 == date(2026, 7, 25)
        assert t.d2 is original_d2  # 幂等：date 不重复赋值
        assert t.d3 is None


# ==================== register_date_type_handlers ====================


class TestRegisterDateTypeHandlers:
    def test_registers_and_idempotent(self, monkeypatch):
        Base = declarative_base()

        class WithDate(Base):
            __tablename__ = "t_reg_with_date"
            id = Column(Integer, primary_key=True)
            d = Column(Date)

        class WithoutDate(Base):
            __tablename__ = "t_reg_without_date"
            id = Column(Integer, primary_key=True)
            s = Column(String(10))

        monkeypatch.setattr(dth, "_registered_models", set())
        assert register_date_type_handlers(Base) == 1
        key = f"{WithDate.__module__}.{WithDate.__name__}"
        assert key in dth._registered_models
        # 幂等：再次注册为 0
        assert register_date_type_handlers(Base) == 0

    def test_models_import_failure_degrades(self, monkeypatch):
        Base = declarative_base()

        class M(Base):
            __tablename__ = "t_reg_import_fail"
            id = Column(Integer, primary_key=True)
            d = Column(Date)

        monkeypatch.setattr(dth, "_registered_models", set())
        with patch.dict(sys.modules, {"app.models": None}):
            # import app.models 触发 ImportError → 告警后继续注册
            assert register_date_type_handlers(Base) == 1

    def test_mappers_missing_table_attrs_skipped(self, monkeypatch):
        """mapper.class_ 缺 __table__ / __tablename__ 时跳过（108、110 行）"""
        from types import SimpleNamespace

        no_table_cls = type("NoTable", (), {})
        has_table_no_name_cls = type("HasTable", (), {"__table__": object()})
        fake_base = SimpleNamespace(
            registry=SimpleNamespace(
                mappers=[
                    SimpleNamespace(class_=no_table_cls),
                    SimpleNamespace(class_=has_table_no_name_cls),
                ]
            )
        )
        monkeypatch.setattr(dth, "_registered_models", set())
        assert register_date_type_handlers(fake_base) == 0
