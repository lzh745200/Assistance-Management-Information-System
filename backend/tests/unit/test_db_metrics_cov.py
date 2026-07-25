"""app.utils.db_metrics 覆盖率攻坚测试

覆盖缺口：
- _ensure_prometheus 的 ImportError 降级分支（78-80）
- DatabaseMetrics.track_query 在 prometheus 不可用时的直通分支（110-111）
- DatabaseMetrics.update_connection_pool_metrics 不可用时的提前返回（149）
- DBMetrics（测试兼容版本）全部公开方法（196-306 的缺口段）

prometheus 相关全局状态的切换均用 patch/patch.dict 上下文管理器，自动还原，
不污染模块全局状态。
"""

import sys
from unittest.mock import patch

import app.utils.db_metrics as m
from app.utils.db_metrics import DBMetrics, DatabaseMetrics


class TestEnsurePrometheusImportError:
    def test_import_error_returns_false(self):
        # prometheus_client 不可导入时优雅降级（78-80）
        with patch.object(m, "_PROMETHEUS_AVAILABLE", False):
            with patch.dict(sys.modules, {"prometheus_client": None}):
                assert m._ensure_prometheus() is False
        # 上下文退出后模块恢复正常（prometheus_client 已安装，可正常初始化）
        assert m._ensure_prometheus() is True


class TestPrometheusUnavailablePaths:
    def test_track_query_passthrough_when_unavailable(self):
        metrics = DatabaseMetrics()
        with patch.object(m, "_PROMETHEUS_AVAILABLE", False):
            with metrics.track_query("SELECT", "projects"):
                pass  # 110-111：不可用时直接 yield，不记录任何指标
        # 恢复后同一实例可正常追踪（验证无状态污染）
        with metrics.track_query("SELECT", "projects"):
            pass

    def test_update_pool_metrics_noop_when_unavailable(self):
        metrics = DatabaseMetrics()
        with patch.object(m, "_PROMETHEUS_AVAILABLE", False):
            # 149：不可用时提前返回，不触碰 gauge
            assert metrics.update_connection_pool_metrics(10, 5, 5) is None
        # 恢复后正常更新
        assert metrics.update_connection_pool_metrics(10, 5, 5) is None


class TestDBMetricsCompat:
    def test_record_query_time_and_stats(self):
        d = DBMetrics()  # 196-198
        d.record_query_time("select", 0.25, sql="SELECT " + "x" * 300, rows_affected=5)  # 212-222
        d.record_query_time("SELECT", 0.75)
        assert len(d.query_times) == 2
        # query_type 统一大写、sql 截断到 200 字符
        assert d.query_times[0].query_type == "SELECT"
        assert len(d.query_times[0].sql) == 200
        assert d.query_times[0].rows_affected == 5
        stats = d.query_stats["SELECT"]
        assert stats["count"] == 2
        assert stats["total_time"] == 1.0
        assert stats["avg_time"] == 0.5
        assert stats["max_time"] == 0.75

    def test_get_query_stats(self):
        d = DBMetrics()
        d.record_query_time("insert", 0.1)
        one = d.get_query_stats("INSERT")  # 234-235
        assert one["count"] == 1
        # 未记录过的类型返回空 dict
        assert d.get_query_stats("DELETE") == {}
        all_stats = d.get_query_stats()  # 237
        assert "INSERT" in all_stats

    def test_get_slow_queries(self):
        d = DBMetrics()
        d.record_query_time("SELECT", 0.5)
        d.record_query_time("SELECT", 2.0)
        slow = d.get_slow_queries(threshold=1.0)  # 249
        assert len(slow) == 1
        assert slow[0].duration == 2.0

    def test_table_metrics(self):
        d = DBMetrics()
        d.record_table_metric("projects", row_count=10, size_bytes=2 * 1024 * 1024, index_count=3)  # 253
        one = d.get_table_metrics("projects")  # 263-273
        assert one["table_name"] == "projects"
        assert one["row_count"] == 10
        assert one["size_bytes"] == 2 * 1024 * 1024
        assert one["size_mb"] == 2.0
        assert one["index_count"] == 3
        assert one["last_analyze"] is not None
        # 不存在的表返回 None（274）
        assert d.get_table_metrics("ghost") is None
        # 不传表名返回全部（276-286）
        d.record_table_metric("villages", row_count=5, size_bytes=1024, index_count=1)
        all_tm = d.get_table_metrics()
        assert set(all_tm.keys()) == {"projects", "villages"}
        assert all_tm["villages"]["size_mb"] == 0.0

    def test_get_summary_and_reset(self):
        d = DBMetrics()
        d.record_query_time("SELECT", 0.5)
        d.record_query_time("UPDATE", 1.5)
        d.record_table_metric("t", row_count=1)
        summary = d.get_summary()  # 290-293
        assert summary["total_queries"] == 2
        assert summary["total_query_time"] == 2.0
        assert summary["avg_query_time"] == 1.0
        assert summary["table_count"] == 1
        # 默认慢查询阈值 1.0：只有 1.5s 的那条
        assert summary["slow_query_count"] == 1
        d.reset()  # 304-306
        empty = d.get_summary()
        assert empty["total_queries"] == 0
        # total_queries=0 时 avg 为 0（296 的 else 分支）
        assert empty["avg_query_time"] == 0
        assert empty["table_count"] == 0
        assert d.get_table_metrics() == {}
