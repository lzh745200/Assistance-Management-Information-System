"""Tests for app/core/prophet_status.py — 目标 100% 覆盖。"""
import importlib
import os
from unittest.mock import patch

import pytest


class TestProphetStatusForceDisable:
    def test_force_disabled_via_env(self):
        with patch.dict(os.environ, {"PROPHET_UNAVAILABLE": "true"}, clear=False):
            from app.core import prophet_status as ps
            importlib.reload(ps)
            assert ps.FORCE_DISABLE is True
            assert ps.PROPHET_AVAILABLE is False
            assert ps.is_prophet_available() is False


class TestProphetStatusUnavailable:
    def test_normal_state(self):
        """Prophet 未安装时默认不可用。"""
        from app.core.prophet_status import is_prophet_available, PROPHET_AVAILABLE
        assert is_prophet_available() is PROPHET_AVAILABLE

    def test_repeated_call(self):
        from app.core.prophet_status import is_prophet_available
        assert is_prophet_available() == is_prophet_available()

    @pytest.mark.parametrize("env_val", ["false", "False", "", "0"])
    def test_not_forced_when_env_is_falsey(self, env_val):
        with patch.dict(os.environ, {"PROPHET_UNAVAILABLE": env_val}, clear=False):
            from app.core import prophet_status as ps
            importlib.reload(ps)
            assert ps.FORCE_DISABLE is False
