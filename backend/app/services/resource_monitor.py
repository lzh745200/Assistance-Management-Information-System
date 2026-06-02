"""
资源监控服务模块
提供系统CPU、内存、磁盘等资源的实时监控和历史趋势
"""

import logging
import os
import platform
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
    logger.warning("psutil 未安装，资源监控将使用有限的 fallback 方案")


@dataclass
class ResourceSnapshot:
    """资源快照"""

    timestamp: float = 0.0
    cpu_percent: float = 0.0
    memory_total: int = 0
    memory_used: int = 0
    memory_percent: float = 0.0
    disk_total: int = 0
    disk_used: int = 0
    disk_percent: float = 0.0
    process_count: int = 0
    python_memory_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "cpu": {
                "percent": self.cpu_percent,
            },
            "memory": {
                "total_mb": round(self.memory_total / 1024 / 1024, 1),
                "used_mb": round(self.memory_used / 1024 / 1024, 1),
                "percent": self.memory_percent,
            },
            "disk": {
                "total_gb": round(self.disk_total / 1024 / 1024 / 1024, 2),
                "used_gb": round(self.disk_used / 1024 / 1024 / 1024, 2),
                "percent": self.disk_percent,
            },
            "process_count": self.process_count,
            "python_memory_mb": self.python_memory_mb,
        }


class ResourceMonitor:
    """
    系统资源监控服务

    功能:
    - 实时获取系统资源使用情况
    - 保存历史趋势数据（内存存储，最多保留 max_history 条）
    - 提供系统概况信息
    """

    def __init__(self, max_history: int = 360):
        """
        Args:
            max_history: 最大历史记录数（默认360条，每分钟1条=6小时）
        """
        self._history: deque = deque(maxlen=max_history)
        self._last_collect_time: float = 0
        self._collect_interval: float = 60.0  # 最小采集间隔（秒）

    def get_current(self) -> ResourceSnapshot:
        """获取当前系统资源快照"""
        snapshot = ResourceSnapshot(timestamp=time.time())

        if PSUTIL_AVAILABLE:
            self._collect_with_psutil(snapshot)
        else:
            self._collect_fallback(snapshot)

        # 自动记录历史
        now = time.time()
        if now - self._last_collect_time >= self._collect_interval:
            self._history.append(snapshot)
            self._last_collect_time = now

        return snapshot

    def get_history(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """
        获取历史资源数据

        Args:
            minutes: 获取最近多少分钟的数据

        Returns:
            历史快照列表
        """
        cutoff = time.time() - (minutes * 60)
        return [s.to_dict() for s in self._history if s.timestamp >= cutoff]

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统基本信息"""
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "processor": platform.processor() or "unknown",
        }

        if PSUTIL_AVAILABLE:
            info["cpu_count_logical"] = psutil.cpu_count(logical=True)
            info["cpu_count_physical"] = psutil.cpu_count(logical=False)
            mem = psutil.virtual_memory()
            info["total_memory_gb"] = round(mem.total / 1024 / 1024 / 1024, 2)
            info["boot_time"] = datetime.fromtimestamp(psutil.boot_time()).isoformat()

        return info

    def check_health(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            包含 status（healthy/warning/critical）和详细信息
        """
        snapshot = self.get_current()
        warnings = []

        if snapshot.cpu_percent > 95:
            warnings.append(f"CPU使用率过高: {snapshot.cpu_percent}%")
        if snapshot.memory_percent > 95:
            warnings.append(f"内存使用率过高: {snapshot.memory_percent}%")
        if snapshot.disk_percent > 95:
            warnings.append(f"磁盘使用率过高: {snapshot.disk_percent}%")

        if any("过高" in w for w in warnings):
            status = "critical" if snapshot.memory_percent > 95 or snapshot.disk_percent > 95 else "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "warnings": warnings,
            "snapshot": snapshot.to_dict(),
        }

    def _collect_with_psutil(self, snapshot: ResourceSnapshot) -> None:
        """使用 psutil 采集资源数据"""
        try:
            # CPU（非阻塞方式，使用上次采集的值）
            snapshot.cpu_percent = psutil.cpu_percent(interval=0)

            # 内存
            mem = psutil.virtual_memory()
            snapshot.memory_total = mem.total
            snapshot.memory_used = mem.used
            snapshot.memory_percent = mem.percent

            # 磁盘（使用当前工作目录所在的分区）
            try:
                disk = psutil.disk_usage(os.getcwd())
                snapshot.disk_total = disk.total
                snapshot.disk_used = disk.used
                snapshot.disk_percent = disk.percent
            except Exception:
                disk = psutil.disk_usage(os.environ.get("SystemDrive", "C:\\"))
                snapshot.disk_total = disk.total
                snapshot.disk_used = disk.used
                snapshot.disk_percent = disk.percent

            # 进程数
            snapshot.process_count = len(psutil.pids())

            # 当前 Python 进程内存
            proc = psutil.Process(os.getpid())
            snapshot.python_memory_mb = round(proc.memory_info().rss / 1024 / 1024, 2)
        except Exception as e:
            logger.error(f"psutil 采集资源失败: {e}")

    def _collect_fallback(self, snapshot: ResourceSnapshot) -> None:
        """Fallback: 使用 os/shutil 采集有限的资源数据"""
        import shutil

        try:
            usage = shutil.disk_usage(os.getcwd())
            snapshot.disk_total = usage.total
            snapshot.disk_used = usage.used
            snapshot.disk_percent = round(usage.used / usage.total * 100, 1) if usage.total > 0 else 0
        except Exception as e:
            logger.error(f"fallback 磁盘信息获取失败: {e}")


# 全局资源监控实例
resource_monitor = ResourceMonitor()
