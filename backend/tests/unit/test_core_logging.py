"""Tests for app/core/logging.py — 目标 100% 覆盖。"""
import logging
from unittest.mock import patch

from app.core.logging import init_logging, logger


class TestLogging:
    def test_logger_is_logger_instance(self):
        assert isinstance(logger, logging.Logger)
        assert logger.name == "assistance_management"

    def test_init_logging_delegates(self):
        with patch("app.core.logging_config.init_logging") as mock_init:
            init_logging()
            mock_init.assert_called_once()

    def test_module_all(self):
        from app.core.logging import __all__
        assert "logger" in __all__
        assert "init_logging" in __all__
