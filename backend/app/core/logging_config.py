"""Logging configuration.

Sets up structured (JSON) and plain-text log formatters, configures
rotating file handlers, and provides a helper to initialise logging
for the entire application.

P2-1: 统一日志入口——本模块为唯一日志实现入口（logging.py 的 SafeLogger 已移除）。
额外6: SensitiveDataFilter 在日志层对身份证/手机号/邮箱脱敏，注册到所有 handler。
"""

import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """日志层敏感信息脱敏过滤器。

    对每条日志消息执行正则替换，将身份证号、手机号、邮箱替换为 ``***``，
    防止敏感数据通过 SQL echo / 异常栈 / 请求体落入日志文件。
    """

    # 身份证号：18 位，末位可为 X/x
    _ID_CARD = re.compile(r"\d{17}[\dXx]")
    # 手机号：1 开头 + [3-9] + 9 位数字
    _MOBILE = re.compile(r"1[3-9]\d{9}")
    # 邮箱
    _EMAIL = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            redacted = self._redact(msg)
            if redacted != msg:
                # 用脱敏后的内容覆盖 record.args/msg，确保 format() 输出脱敏结果
                record.msg = redacted
                record.args = None
        except Exception:
            # 脱敏失败不应阻断日志输出
            pass
        return True

    @classmethod
    def _redact(cls, text: str) -> str:
        if not text:
            return text
        text = cls._ID_CARD.sub("***", text)
        text = cls._MOBILE.sub("***", text)
        text = cls._EMAIL.sub("***", text)
        return text


class JsonFormatter(logging.Formatter):
    """JSON line formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        import json as _json
        from datetime import datetime, timezone

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return _json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Console formatter with ANSI colour codes."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def configure_logging(
    level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    *,
    max_bytes: int = 50 * 1024 * 1024,
    backup_count: int = 5,
    log_rotation: Optional[str] = None,
) -> None:
    """Configure the Python logging subsystem for the application.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
        log_format: "json" or "text".
        log_file: Path to the log file. If None/empty, file logging is disabled.
        max_bytes: Maximum size of a log file before rotation (size-based).
        backup_count: Number of backup log files to retain.
        log_rotation: 时间轮转策略。若提供且非空（如 settings.LOG_ROTATION），
            使用 TimedRotatingFileHandler(when='midnight', backupCount=backup_count)
            按天轮转；否则按大小使用 RotatingFileHandler。接通 config.LOG_ROTATION 死配置。
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 敏感信息脱敏过滤器（注册到 root，所有 handler 继承）
    sensitive_filter = SensitiveDataFilter()

    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if level.upper() == "DEBUG" else logging.INFO)

    if os.name == "nt" or not sys.stdout.isatty():
        console_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        console_fmt = ColoredFormatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    console_handler.setFormatter(console_fmt)
    console_handler.addFilter(sensitive_filter)
    root_logger.addHandler(console_handler)

    # File handler — 根据 log_rotation 选择按时间或按大小轮转
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if log_rotation:
            # 按天轮转（接通 config.LOG_ROTATION）
            file_handler = TimedRotatingFileHandler(
                str(log_path),
                when="midnight",
                backupCount=backup_count,
                encoding="utf-8",
                utc=False,
            )
        else:
            file_handler = RotatingFileHandler(
                str(log_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
        file_handler.setLevel(logging.DEBUG)
        if log_format == "json":
            file_handler.setFormatter(JsonFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(name)s %(module)s:%(lineno)d: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info("日志系统已初始化 level=%s", level.upper())


def init_logging() -> None:
    """Initialise logging from the application settings.

    Safe to call multiple times.
    """
    try:
        from app.core.config import settings  # type: ignore[import-untyped]

        configure_logging(
            level=getattr(settings, "LOG_LEVEL", "INFO"),
            log_format=getattr(settings, "LOG_FORMAT", "json"),
            log_file=getattr(settings, "LOG_FILE", None),
            max_bytes=getattr(settings, "LOG_MAX_SIZE_MB", 50) * 1024 * 1024,
            backup_count=getattr(settings, "LOG_BACKUP_COUNT", 5),
            log_rotation=getattr(settings, "LOG_ROTATION", None) or None,
        )
    except Exception:
        configure_logging(level="INFO", log_format="text")
