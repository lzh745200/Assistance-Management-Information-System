"""app.core.logging_config 覆盖率攻坚测试（补充 test_core_logging.py 未覆盖分支）

覆盖点：
- SafeTimedRotatingFileHandler.doRollover：关流/重试/最终失败stderr/重开流
- SafeRotatingFileHandler.rotate：重试成功/最终失败stderr
- SensitiveDataFilter.filter：脱敏覆盖分支、异常降级
- _redact：空文本
- ColoredFormatter.format：ANSI 着色
- configure_logging：旧handler关闭异常、TTY着色分支、时间/大小轮转、text格式
- init_logging：异常回退
"""

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from unittest.mock import MagicMock, patch

import pytest

import app.core.logging_config as lc


@pytest.fixture
def restore_root_handlers():
    root = logging.getLogger()
    saved = list(root.handlers)
    yield
    for h in list(root.handlers):
        root.removeHandler(h)
    for h in saved:
        root.addHandler(h)


class TestSafeTimedRotatingHandler:
    def test_rollover_retry_then_success(self, tmp_path):
        h = lc.SafeTimedRotatingFileHandler(str(tmp_path / "a.log"), when="midnight")
        with patch.object(
            TimedRotatingFileHandler, "doRollover",
            side_effect=[PermissionError(), PermissionError(), None],
        ):
            h.doRollover()
        h.close()

    def test_rollover_persistent_failure_reopens_stream(self, tmp_path, capsys):
        h = lc.SafeTimedRotatingFileHandler(str(tmp_path / "b.log"), when="midnight")
        with (
            patch.object(TimedRotatingFileHandler, "doRollover", side_effect=PermissionError()),
            patch.object(lc.time, "sleep"),
        ):
            h.doRollover()
        assert "轮转失败" in capsys.readouterr().err
        assert h.stream is not None
        h.close()


class TestSafeRotatingHandler:
    def test_rotate_retry_then_success(self, tmp_path):
        h = lc.SafeRotatingFileHandler(str(tmp_path / "c.log"), maxBytes=1024)
        with patch.object(
            RotatingFileHandler, "rotate", side_effect=[PermissionError(), None]
        ):
            h.rotate("a", "b")
        h.close()

    def test_rotate_persistent_failure(self, tmp_path, capsys):
        h = lc.SafeRotatingFileHandler(str(tmp_path / "d.log"), maxBytes=1024)
        with (
            patch.object(RotatingFileHandler, "rotate", side_effect=PermissionError()),
            patch.object(lc.time, "sleep"),
        ):
            h.rotate("a", "b")
        assert "轮转失败" in capsys.readouterr().err
        h.close()


class TestSensitiveDataFilter:
    def test_redacts_and_overwrites_record(self):
        f = lc.SensitiveDataFilter()
        record = logging.LogRecord("n", logging.INFO, __file__, 1, "手机 13812345678", None, None)
        assert f.filter(record) is True
        assert "13812345678" not in record.msg
        assert record.args is None

    def test_get_message_exception_degrades(self):
        f = lc.SensitiveDataFilter()
        record = logging.LogRecord("n", logging.INFO, __file__, 1, "%s %s", ("only-one",), None)
        assert f.filter(record) is True  # getMessage 抛 TypeError → 吞掉

    def test_redact_empty(self):
        assert lc.SensitiveDataFilter._redact("") == ""
        assert lc.SensitiveDataFilter._redact(None) is None


class TestColoredFormatter:
    def test_format_adds_ansi(self):
        fmt = lc.ColoredFormatter("%(levelname)s %(message)s")
        record = logging.LogRecord("n", logging.ERROR, __file__, 1, "msg", None, None)
        out = fmt.format(record)
        assert "\033[31m" in out


class TestConfigureLogging:
    def test_handler_close_exception_prints(self, restore_root_handlers, capsys):
        root = logging.getLogger()
        bad = MagicMock()
        bad.close.side_effect = RuntimeError("close boom")
        root.addHandler(bad)
        lc.configure_logging(level="INFO", log_format="json", log_file=None)
        assert "handler close failed" in capsys.readouterr().err

    def test_tty_uses_colored_formatter(self, restore_root_handlers):
        with (
            patch.object(lc.os, "name", "posix"),
            patch.object(lc.sys.stdout, "isatty", return_value=True),
        ):
            lc.configure_logging(level="DEBUG", log_format="json", log_file=None)
        console = logging.getLogger().handlers[0]
        assert isinstance(console.formatter, lc.ColoredFormatter)

    def test_timed_rotation_and_text_format(self, restore_root_handlers, tmp_path):
        lc.configure_logging(
            level="INFO", log_format="text",
            log_file=str(tmp_path / "timed.log"), log_rotation="midnight",
        )
        handlers = logging.getLogger().handlers
        assert any(isinstance(h, lc.SafeTimedRotatingFileHandler) for h in handlers)
        file_handler = [h for h in handlers if isinstance(h, lc.SafeTimedRotatingFileHandler)][0]
        assert not isinstance(file_handler.formatter, lc.JsonFormatter)

    def test_size_rotation_json(self, restore_root_handlers, tmp_path):
        lc.configure_logging(
            level="INFO", log_format="json", log_file=str(tmp_path / "size.log"),
        )
        handlers = logging.getLogger().handlers
        assert any(isinstance(h, lc.SafeRotatingFileHandler) for h in handlers)


class TestInitLogging:
    def test_exception_falls_back(self, restore_root_handlers):
        with patch.object(lc, "configure_logging", side_effect=[RuntimeError("boom"), None]) as m:
            lc.init_logging()
        assert m.call_count == 2
        assert m.call_args_list[1].kwargs == {"level": "INFO", "log_format": "text"}
