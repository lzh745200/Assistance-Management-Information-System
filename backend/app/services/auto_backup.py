"""自动定时备份 — 间隔调度 + 完整性校验 + 过期清理."""
import hashlib
import logging
import os
import shutil
import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_MINUTES = 120  # 默认 2 小时
DEFAULT_RETENTION_DAYS = 30    # 保留 30 天
DEFAULT_KEEP_MIN = 5           # 最少保留 5 个备份


class BackupScheduler:
    """定时备份调度器."""

    def __init__(
        self,
        interval_minutes: int = DEFAULT_INTERVAL_MINUTES,
        backup_dir: str = "./backups",
        source_db_path: str = "./data/rural_revitalization.db",
    ):
        self.interval = interval_minutes
        self.backup_dir = backup_dir
        self.source_db_path = source_db_path
        self._last_backup: float = 0.0
        os.makedirs(backup_dir, exist_ok=True)

    def should_backup(self) -> bool:
        """检查是否到达备份间隔."""
        if self._last_backup == 0.0:
            return True
        elapsed = time.time() - self._last_backup
        return elapsed >= self.interval * 60

    def run_backup(self) -> Optional[str]:
        """执行一次备份，返回备份文件路径."""
        if not os.path.exists(self.source_db_path):
            logger.warning("源数据库不存在: %s", self.source_db_path)
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.db"
        dest = os.path.join(self.backup_dir, filename)

        try:
            shutil.copy2(self.source_db_path, dest)
            self._last_backup = time.time()
            logger.info("备份完成: %s", dest)

            # 清理过期备份
            cleanup_old_backups(
                self.backup_dir,
                max_age_days=DEFAULT_RETENTION_DAYS,
                keep_min=DEFAULT_KEEP_MIN,
            )
            return dest
        except Exception as e:
            logger.error("备份失败: %s", e)
            return None

    def verify_last_backup(self) -> bool:
        """校验最近备份的完整性."""
        backups = sorted(
            [f for f in os.listdir(self.backup_dir) if f.startswith("backup_")],
            reverse=True,
        )
        if not backups:
            return False
        latest = os.path.join(self.backup_dir, backups[0])
        source_hash = compute_file_checksum(self.source_db_path)
        backup_hash = compute_file_checksum(latest)
        return source_hash == backup_hash


def compute_file_checksum(filepath: str, chunk_size: int = 8192) -> str:
    """计算文件的 SHA-256 校验和."""
    sha = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha.update(chunk)
    except FileNotFoundError:
        return ""
    return sha.hexdigest()


def cleanup_old_backups(
    backup_dir: str,
    max_age_days: int = DEFAULT_RETENTION_DAYS,
    keep_min: int = DEFAULT_KEEP_MIN,
) -> int:
    """清理过期备份文件，最少保留 keep_min 个."""
    cutoff = time.time() - max_age_days * 86400
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith("backup_")],
    )
    removed = 0
    for f in backups:
        if len(backups) - removed <= keep_min:
            break
        filepath = os.path.join(backup_dir, f)
        if os.path.getmtime(filepath) < cutoff:
            os.remove(filepath)
            removed += 1
            logger.info("清理过期备份: %s", f)
    return removed
