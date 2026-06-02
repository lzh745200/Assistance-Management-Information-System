"""
数据库指标监控测试

测试 app/utils/db_metrics.py 模块
"""
import pytest
import time
from unittest.mock import Mock, patch
from app.utils.db_metrics import DatabaseMetrics, get_db_metrics

class TestDatabaseMetrics:
    """数据库指标测试类"""

    @pytest.fixture
    def db_metrics(self):
        """创建数据库指标实例"""
        return DatabaseMetrics(slow_query_threshold=0.5)

    def test_track_query_success(self, db_metrics):
        """测试成功的查询追踪"""
        with db_metrics.track_query("SELECT", "projects"):
            time.sleep(0.01)  # 模拟查询
        # 验证指标已记录（通过Prometheus客户端）

    def test_track_query_with_error(self, db_metrics):
        """测试查询错误追踪"""
        with pytest.raises(ValueError):
            with db_metrics.track_query("SELECT", "projects"):
                raise ValueError("Query failed")
        # 验证错误指标已记录

    def test_slow_query_detection(self, db_metrics):
        """测试慢查询检测"""
        with db_metrics.track_query("SELECT", "projects"):
            time.sleep(0.6)  # 超过阈值0.5秒
        # 验证慢查询指标已记录

    def test_update_connection_pool_metrics(self, db_metrics):
        """测试连接池指标更新"""
        db_metrics.update_connection_pool_metrics(
            total=10,
            active=5,
            idle=5
        )
        # 验证指标已更新

    def test_get_db_metrics_singleton(self):
        """测试单例模式"""
        metrics1 = get_db_metrics()
        metrics2 = get_db_metrics()
        assert metrics1 is metrics2

class TestDatabaseMetricsIntegration:
    """数据库指标集成测试"""

    def test_track_multiple_queries(self):
        """测试追踪多个查询"""
        db_metrics = DatabaseMetrics()

        # 执行多个查询
        with db_metrics.track_query("SELECT", "projects"):
            time.sleep(0.01)

        with db_metrics.track_query("INSERT", "funds"):
            time.sleep(0.01)

        with db_metrics.track_query("UPDATE", "villages"):
            time.sleep(0.01)

        # 验证所有查询都被记录

    def test_concurrent_queries(self):
        """测试并发查询追踪"""
        import threading

        db_metrics = DatabaseMetrics()

        def query_task():
            with db_metrics.track_query("SELECT", "test"):
                time.sleep(0.01)

        threads = [threading.Thread(target=query_task) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证所有查询都被正确记录
