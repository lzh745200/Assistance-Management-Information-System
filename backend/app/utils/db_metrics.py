"""
数据库监控指标

提供数据库连接池和查询性能监控

prometheus_client 是可选依赖，完全延迟导入，确保在 PyInstaller
打包环境中缺失 prometheus_client 时模块仍可正常加载。
"""

import logging
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# prometheus_client 延迟加载（不在模块顶层导入，避免 PyInstaller 打包缺失时报错）
_PROMETHEUS_AVAILABLE = False
_Counter: Any = None
_Gauge: Any = None
_Histogram: Any = None

# 数据库连接池指标（延迟初始化）
db_connections_total: Any = None
db_connections_active: Any = None
db_connections_idle: Any = None

# 数据库查询指标（延迟初始化）
db_queries_total: Any = None
db_query_duration_seconds: Any = None
db_query_errors_total: Any = None
db_slow_queries_total: Any = None


def _ensure_prometheus():
    """延迟初始化 prometheus_client 指标（仅在首次调用时检测并初始化）"""
    global _PROMETHEUS_AVAILABLE, _Counter, _Gauge, _Histogram
    global db_connections_total, db_connections_active, db_connections_idle
    global db_queries_total, db_query_duration_seconds, db_query_errors_total
    global db_slow_queries_total

    if _PROMETHEUS_AVAILABLE:
        return True

    try:
        from prometheus_client import Counter, Gauge, Histogram
        _Counter = Counter
        _Gauge = Gauge
        _Histogram = Histogram

        db_connections_total = Gauge("db_connections_total", "Total database connections in pool")
        db_connections_active = Gauge("db_connections_active", "Active database connections")
        db_connections_idle = Gauge("db_connections_idle", "Idle database connections")

        db_queries_total = Counter("db_queries_total", "Total database queries", ["operation", "table"])
        db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation", "table"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        )
        db_query_errors_total = Counter(
            "db_query_errors_total",
            "Total database query errors",
            ["operation", "table", "error_type"],
        )
        db_slow_queries_total = Counter(
            "db_slow_queries_total",
            "Total slow database queries (>1s)",
            ["operation", "table"],
        )

        _PROMETHEUS_AVAILABLE = True
        return True
    except ImportError:
        _PROMETHEUS_AVAILABLE = False
        return False


class DatabaseMetrics:
    """数据库指标收集器"""

    def __init__(self, slow_query_threshold: float = 1.0):
        """
        初始化数据库指标收集器

        Args:
            slow_query_threshold: 慢查询阈值（秒），默认1秒
        """
        self.slow_query_threshold = slow_query_threshold
        _ensure_prometheus()  # 初始化 prometheus 指标

    @contextmanager
    def track_query(self, operation: str, table: str = "unknown"):
        """
        追踪数据库查询

        Args:
            operation: 操作类型 (SELECT, INSERT, UPDATE, DELETE)
            table: 表名

        Usage:
            with db_metrics.track_query("SELECT", "projects"):
                result = db.query(Project).all()
        """
        if not _PROMETHEUS_AVAILABLE:
            yield
            return

        start_time = time.time()
        error_occurred = False
        error_type = None

        try:
            yield
        except Exception as e:
            error_occurred = True
            error_type = type(e).__name__
            db_query_errors_total.labels(operation=operation, table=table, error_type=error_type).inc()
            raise
        finally:
            duration = time.time() - start_time

            # 记录查询计数
            if not error_occurred:
                db_queries_total.labels(operation=operation, table=table).inc()

            # 记录查询延迟
            db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)

            # 记录慢查询
            if duration > self.slow_query_threshold:
                db_slow_queries_total.labels(operation=operation, table=table).inc()
                logger.warning(f"Slow query detected: {operation} on {table} took {duration:.3f}s")

    def update_connection_pool_metrics(self, total: int, active: int, idle: int):
        """
        更新连接池指标

        Args:
            total: 总连接数
            active: 活跃连接数
            idle: 空闲连接数
        """
        if not _PROMETHEUS_AVAILABLE:
            return
        db_connections_total.set(total)
        db_connections_active.set(active)
        db_connections_idle.set(idle)


# 全局数据库指标实例
_db_metrics: Optional[DatabaseMetrics] = None


def get_db_metrics() -> DatabaseMetrics:
    """获取数据库指标实例（单例）"""
    global _db_metrics
    if _db_metrics is None:
        _db_metrics = DatabaseMetrics()
    return _db_metrics


# ==================== DBMetrics 类（兼容测试）====================


@dataclass
class QueryMetric:
    """查询指标"""

    query_type: str
    sql: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)
    rows_affected: int = 0


@dataclass
class TableMetric:
    """表指标"""

    table_name: str
    row_count: int = 0
    size_bytes: int = 0
    index_count: int = 0
    last_analyze: Optional[datetime] = None


class DBMetrics:
    """数据库指标收集器（测试兼容版本）"""

    def __init__(self):
        self.query_times: deque[QueryMetric] = deque(maxlen=1000)
        self.table_metrics: Dict[str, TableMetric] = {}
        self.query_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "total_time": 0.0, "avg_time": 0.0, "max_time": 0.0}
        )

    def record_query_time(self, query_type: str, duration: float, sql: str = "", rows_affected: int = 0):
        """
        记录查询时间

        Args:
            query_type: 查询类型 (SELECT/INSERT/UPDATE/DELETE)
            duration: 执行时间(秒)
            sql: SQL语句
            rows_affected: 影响的行数
        """
        metric = QueryMetric(
            query_type=query_type.upper(), sql=sql[:200], duration=duration, rows_affected=rows_affected  # 限制长度
        )
        self.query_times.append(metric)

        # 更新统计
        stats = self.query_stats[query_type.upper()]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["max_time"] = max(stats["max_time"], duration)

    def get_query_stats(self, query_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取查询统计

        Args:
            query_type: 查询类型，None表示所有类型

        Returns:
            统计信息字典
        """
        if query_type:
            return dict(self.query_stats.get(query_type.upper(), {}))

        return dict(self.query_stats)

    def get_slow_queries(self, threshold: float = 1.0) -> List[QueryMetric]:
        """
        获取慢查询

        Args:
            threshold: 慢查询阈值(秒)

        Returns:
            慢查询列表
        """
        return [q for q in self.query_times if q.duration >= threshold]

    def record_table_metric(self, table_name: str, row_count: int = 0, size_bytes: int = 0, index_count: int = 0):
        """记录表指标"""
        self.table_metrics[table_name] = TableMetric(
            table_name=table_name,
            row_count=row_count,
            size_bytes=size_bytes,
            index_count=index_count,
            last_analyze=datetime.now(),
        )

    def get_table_metrics(self, table_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取表指标"""
        if table_name:
            metric = self.table_metrics.get(table_name)
            if metric:
                return {
                    "table_name": metric.table_name,
                    "row_count": metric.row_count,
                    "size_bytes": metric.size_bytes,
                    "size_mb": round(metric.size_bytes / (1024 * 1024), 2),
                    "index_count": metric.index_count,
                    "last_analyze": metric.last_analyze.isoformat() if metric.last_analyze else None,
                }
            return None

        return {
            name: {
                "table_name": m.table_name,
                "row_count": m.row_count,
                "size_bytes": m.size_bytes,
                "size_mb": round(m.size_bytes / (1024 * 1024), 2),
                "index_count": m.index_count,
                "last_analyze": m.last_analyze.isoformat() if m.last_analyze else None,
            }
            for name, m in self.table_metrics.items()
        }

    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        total_queries = sum(s["count"] for s in self.query_stats.values())
        total_time = sum(s["total_time"] for s in self.query_stats.values())

        return {
            "total_queries": total_queries,
            "total_query_time": round(total_time, 3),
            "avg_query_time": round(total_time / total_queries, 3) if total_queries > 0 else 0,
            "query_stats": dict(self.query_stats),
            "table_count": len(self.table_metrics),
            "slow_query_count": len(self.get_slow_queries()),
        }

    def reset(self):
        """重置所有指标"""
        self.query_times.clear()
        self.table_metrics.clear()
        self.query_stats.clear()
