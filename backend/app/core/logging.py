"""Structured application logging with rotating file handler and console output."""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


class SafeLogger:
    """Application logger that writes to both console and a rotating file."""

    def __init__(self, env: str = "dev", level: str = "INFO"):
        self.env = env
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.logger = logging.getLogger("military_rural")
        self.logger.setLevel(self.level)
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(fmt)

        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG if self.env == "dev" else self.level)
        console.setFormatter(formatter)
        self.logger.addHandler(console)

        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=50 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)


logger = logging.getLogger("military_rural")
