"""Logging configuration.

Sets up structured (JSON) and plain-text log formatters, configures
rotating file handlers, and provides a helper to initialise logging
for the entire application.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


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
) -> None:
    """Configure the Python logging subsystem for the application.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
        log_format: "json" or "text".
        log_file: Path to the log file. If None/empty, file logging is disabled.
        max_bytes: Maximum size of a log file before rotation.
        backup_count: Number of backup log files to retain.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

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
    root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
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
        )
    except Exception:
        configure_logging(level="INFO", log_format="text")
