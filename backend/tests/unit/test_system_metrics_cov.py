"""app.utils.system_metrics 覆盖率攻坚测试

覆盖缺口：
- _ensure_prometheus 的 ImportError 降级分支（68-70）
- collect_all 子采集器抛错时的吞异常分支（93-94）
- 各 collect_* 在 prometheus 不可用时的提前返回（99/114/137/156）
- collect_memory_metrics 异常分支（126-127）
- collect_disk_metrics 单路径失败 warning（148-149）与外层异常（150-151）
- collect_process_metrics num_fds 不支持分支（162-164）与外层异常（169-170）
"""

import sys
from unittest.mock import MagicMock, patch

import app.utils.system_metrics as m
from app.utils.system_metrics import SystemMetrics


def _make_metrics(process=None):
    return SystemMetrics(process=process if process is not None else MagicMock())


class TestEnsurePrometheusImportError:
    def test_import_error_returns_false(self):
        with patch.object(m, "_PROMETHEUS_AVAILABLE", False):
            with patch.dict(sys.modules, {"prometheus_client": None}):
                assert m._ensure_prometheus() is False  # 68-70
        # 上下文退出后模块恢复正常（prometheus_client 已安装）
        assert m._ensure_prometheus() is True


class TestCollectAllException:
    def test_subcollector_failure_swallowed(self):
        sm = _make_metrics()
        with patch.object(sm, "collect_cpu_metrics", side_effect=RuntimeError("boom")):
            sm.collect_all()  # 93-94：记录日志，不向外抛


class TestUnavailableEarlyReturns:
    def test_all_collectors_noop_when_unavailable(self):
        proc = MagicMock()
        sm = _make_metrics(process=proc)
        with patch.object(m, "_PROMETHEUS_AVAILABLE", False):
            sm.collect_cpu_metrics()  # 99
            sm.collect_memory_metrics()  # 114
            sm.collect_disk_metrics()  # 137
            sm.collect_process_metrics()  # 156
        # 不可用时完全不触碰 psutil / process
        proc.cpu_percent.assert_not_called()
        proc.memory_info.assert_not_called()
        proc.num_threads.assert_not_called()


class TestMemoryMetricsException:
    def test_virtual_memory_failure_logged(self):
        sm = _make_metrics()
        with patch("psutil.virtual_memory", side_effect=RuntimeError("mem err")):
            sm.collect_memory_metrics()  # 126-127：吞异常不向外抛


class TestDiskMetricsExceptions:
    def test_per_path_failure_warns_and_continues(self):
        sm = _make_metrics()
        usage = MagicMock(total=100, used=50, percent=50.0)
        with patch("psutil.disk_usage", side_effect=[OSError("bad path"), usage]) as mock_du:
            sm.collect_disk_metrics(paths=["/bad", "/good"])  # 148-149，随后 /good 正常
        assert mock_du.call_count == 2

    def test_outer_exception_logged(self):
        sm = _make_metrics()
        # paths 不可迭代 → for 循环抛 TypeError → 外层 except（150-151）
        sm.collect_disk_metrics(paths=123)


class TestProcessMetricsEdgeCases:
    def test_num_fds_not_supported(self):
        proc = MagicMock()
        proc.num_fds.side_effect = AttributeError("no num_fds on Windows")
        proc.num_threads.return_value = 7
        _make_metrics(process=proc).collect_process_metrics()  # 162-164
        proc.num_threads.assert_called_once()

    def test_outer_exception_logged(self):
        proc = MagicMock()
        proc.num_fds.return_value = 3
        proc.num_threads.side_effect = RuntimeError("threads err")
        _make_metrics(process=proc).collect_process_metrics()  # 169-170
