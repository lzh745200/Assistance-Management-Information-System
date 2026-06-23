"""Tests for app/services/db_maintenance.py — 目标 100% 覆盖。

覆盖要点：
- _run_maintenance:
  * 初始 wait 返回 True → 立即退出
  * 循环一次后 is_set → 退出
  * _do_maintenance 抛异常 → 捕获 + 警告
- _do_maintenance: 成功 / 异常 / 连接异常
- start_db_maintenance: 首次启动 / 已在运行
- stop_db_maintenance: 有线程 / 无线程
- _seconds_until_next_3am: 3 点前 / 3 点后 / now=None
- _run_wal_checkpoint:
  * 初始 wait 返回 True → 退出
  * 循环一次 + 二次 wait True → 退出
  * _do_wal_checkpoint 抛异常 → 捕获
- _do_wal_checkpoint: 成功 / 异常 / finally close
- start_wal_checkpoint_scheduler: 首次 / 已在运行
- stop_wal_checkpoint_scheduler: 有线程 / 无线程
"""
import datetime
from unittest.mock import MagicMock, patch

import pytest

import app.services.db_maintenance as dm


# ---------------------------------------------------------------------------
# _run_maintenance
# ---------------------------------------------------------------------------


class TestRunMaintenance:
    def test_initial_wait_returns_true_exits_immediately(self):
        """初始 _stop_event.wait 返回 True → 立即 return（不进入循环）。"""
        with patch.object(dm, "_stop_event") as mock_event:
            mock_event.wait.return_value = True  # 初始等待被中断
            with patch.object(dm, "_do_maintenance") as mock_do:
                dm._run_maintenance()
            # _do_maintenance 不应被调用
            mock_do.assert_not_called()
            # 初始 wait 只调用一次
            assert mock_event.wait.call_count == 1

    def test_one_iteration_then_exit(self):
        """循环一次后 _stop_event 被置位 → 退出。"""
        with patch.object(dm, "_stop_event") as mock_event:
            mock_event.wait.return_value = False  # 初始等待 + 间隔等待都返回 False
            mock_event.is_set.side_effect = [False, True]  # 第一次进循环，第二次退出
            with patch.object(dm, "_do_maintenance") as mock_do:
                dm._run_maintenance()
            mock_do.assert_called_once()

    def test_do_maintenance_raises_logs_warning(self):
        """_do_maintenance 抛异常 → 捕获并记录警告，循环继续。"""
        with patch.object(dm, "_stop_event") as mock_event:
            mock_event.wait.return_value = False
            mock_event.is_set.side_effect = [False, True]
            with patch.object(dm, "_do_maintenance", side_effect=RuntimeError("boom")):
                with patch.object(dm, "logger") as mock_log:
                    dm._run_maintenance()
            mock_log.warning.assert_called_once_with("数据库维护失败", exc_info=True)


# ---------------------------------------------------------------------------
# _do_maintenance
# ---------------------------------------------------------------------------


class TestDoMaintenance:
    def test_success(self):
        """正常执行 WAL checkpoint + VACUUM + optimize。"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_obj = MagicMock()
        mock_conn_obj.connection = mock_conn
        mock_db = MagicMock()
        mock_db.connection.return_value = mock_conn_obj

        with patch("app.core.database.SessionLocal", return_value=mock_db):
            dm._do_maintenance()

        calls = [c[0][0] for c in mock_cursor.execute.call_args_list]
        assert "PRAGMA wal_checkpoint(TRUNCATE)" in calls
        assert "VACUUM" in calls
        assert "PRAGMA optimize" in calls
        mock_cursor.close.assert_called_once()
        mock_db.close.assert_called_once()

    def test_exception_logs_warning(self):
        """cursor.execute 抛异常 → 捕获 + 警告 + finally close。"""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("disk full")
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_obj = MagicMock()
        mock_conn_obj.connection = mock_conn
        mock_db = MagicMock()
        mock_db.connection.return_value = mock_conn_obj

        with patch("app.core.database.SessionLocal", return_value=mock_db):
            with patch.object(dm, "logger") as mock_log:
                dm._do_maintenance()

        mock_log.warning.assert_called_once()
        mock_db.close.assert_called_once()

    def test_connection_failure(self):
        """db.connection() 抛异常 → finally close。"""
        mock_db = MagicMock()
        mock_db.connection.side_effect = Exception("no conn")

        with patch("app.core.database.SessionLocal", return_value=mock_db):
            with patch.object(dm, "logger"):
                dm._do_maintenance()

        mock_db.close.assert_called_once()


# ---------------------------------------------------------------------------
# start_db_maintenance / stop_db_maintenance
# ---------------------------------------------------------------------------


class TestStartStopDbMaintenance:
    def test_start_first_time(self):
        with patch.object(dm, "_maintenance_thread", None):
            with patch.object(dm, "_stop_event") as mock_event:
                with patch("threading.Thread") as mock_thread_cls:
                    mock_thread = MagicMock()
                    mock_thread_cls.return_value = mock_thread
                    dm.start_db_maintenance()
                    mock_event.clear.assert_called_once()
                    mock_thread_cls.assert_called_once_with(
                        target=dm._run_maintenance, daemon=True, name="db-maintenance"
                    )
                    mock_thread.start.assert_called_once()

    def test_start_already_running(self):
        mock_existing = MagicMock()
        with patch.object(dm, "_maintenance_thread", mock_existing):
            with patch("threading.Thread") as mock_thread_cls:
                dm.start_db_maintenance()
                mock_thread_cls.assert_not_called()

    def test_stop_with_thread(self):
        mock_thread = MagicMock()
        with patch.object(dm, "_maintenance_thread", mock_thread):
            with patch.object(dm, "_stop_event") as mock_event:
                with patch.object(dm, "logger"):
                    dm.stop_db_maintenance()
                mock_event.set.assert_called_once()
                mock_thread.join.assert_called_once_with(timeout=1)

    def test_stop_without_thread(self):
        with patch.object(dm, "_maintenance_thread", None):
            with patch.object(dm, "_stop_event") as mock_event:
                with patch.object(dm, "logger"):
                    dm.stop_db_maintenance()
                mock_event.set.assert_called_once()


# ---------------------------------------------------------------------------
# _seconds_until_next_3am
# ---------------------------------------------------------------------------


class TestSecondsUntilNext3am:
    def test_before_3am_same_day(self):
        """2:00 → 距今天 3:00 还有 1 小时。"""
        now = datetime.datetime(2026, 6, 23, 2, 0, 0)
        seconds = dm._seconds_until_next_3am(now)
        assert seconds == 3600

    def test_after_3am_next_day(self):
        """4:00 → 距明天 3:00 还有 23 小时。"""
        now = datetime.datetime(2026, 6, 23, 4, 0, 0)
        seconds = dm._seconds_until_next_3am(now)
        assert seconds == 23 * 3600

    def test_exactly_3am_next_day(self):
        """正好 3:00:00 → next_run <= now → 加 1 天 → 24 小时。"""
        now = datetime.datetime(2026, 6, 23, 3, 0, 0)
        seconds = dm._seconds_until_next_3am(now)
        assert seconds == 24 * 3600

    def test_now_none_uses_current_time(self):
        """now=None → 使用 datetime.datetime.now()，返回正整数。"""
        seconds = dm._seconds_until_next_3am(None)
        assert isinstance(seconds, int)
        assert seconds >= 1


# ---------------------------------------------------------------------------
# _run_wal_checkpoint
# ---------------------------------------------------------------------------


class TestRunWalCheckpoint:
    def test_initial_wait_returns_true_exits(self):
        """初始 _wal_stop_event.wait 返回 True → 立即退出。"""
        with patch.object(dm, "_wal_stop_event") as mock_event:
            mock_event.wait.return_value = True
            with patch.object(dm, "_do_wal_checkpoint") as mock_do:
                dm._run_wal_checkpoint()
            mock_do.assert_not_called()
            assert mock_event.wait.call_count == 1

    def test_one_iteration_then_exit_on_second_wait(self):
        """循环一次后二次 wait 返回 True → 退出。"""
        with patch.object(dm, "_wal_stop_event") as mock_event:
            # 第一次 wait (初始) → False；第二次 wait (循环内) → True
            mock_event.wait.side_effect = [False, True]
            mock_event.is_set.side_effect = [False]  # 进入循环一次
            with patch.object(dm, "_do_wal_checkpoint") as mock_do:
                dm._run_wal_checkpoint()
            mock_do.assert_called_once()

    def test_do_wal_checkpoint_raises_logs_warning(self):
        """_do_wal_checkpoint 抛异常 → 捕获 + 警告，循环继续到二次 wait 退出。"""
        with patch.object(dm, "_wal_stop_event") as mock_event:
            mock_event.wait.side_effect = [False, True]
            mock_event.is_set.side_effect = [False]
            with patch.object(dm, "_do_wal_checkpoint", side_effect=RuntimeError("err")):
                with patch.object(dm, "logger") as mock_log:
                    dm._run_wal_checkpoint()
            mock_log.warning.assert_called_once_with(
                "WAL checkpoint 调度执行失败", exc_info=True
            )


# ---------------------------------------------------------------------------
# _do_wal_checkpoint
# ---------------------------------------------------------------------------


class TestDoWalCheckpoint:
    def test_success(self):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0, 0, 0)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_obj = MagicMock()
        mock_conn_obj.connection = mock_conn
        mock_db = MagicMock()
        mock_db.connection.return_value = mock_conn_obj

        with patch("app.core.database.SessionLocal", return_value=mock_db):
            with patch.object(dm, "logger") as mock_log:
                dm._do_wal_checkpoint()

        mock_cursor.execute.assert_called_once_with("PRAGMA wal_checkpoint(TRUNCATE)")
        mock_cursor.fetchone.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_db.close.assert_called_once()
        mock_log.info.assert_called_once()

    def test_exception_logs_warning(self):
        """cursor.execute 抛异常 → 捕获 + 警告 + finally close。"""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("locked")
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_obj = MagicMock()
        mock_conn_obj.connection = mock_conn
        mock_db = MagicMock()
        mock_db.connection.return_value = mock_conn_obj

        with patch("app.core.database.SessionLocal", return_value=mock_db):
            with patch.object(dm, "logger") as mock_log:
                dm._do_wal_checkpoint()

        mock_log.warning.assert_called_once()
        mock_db.close.assert_called_once()

    def test_connection_failure(self):
        """db.connection() 抛异常 → finally close。"""
        mock_db = MagicMock()
        mock_db.connection.side_effect = Exception("no conn")

        with patch("app.core.database.SessionLocal", return_value=mock_db):
            with patch.object(dm, "logger"):
                dm._do_wal_checkpoint()

        mock_db.close.assert_called_once()


# ---------------------------------------------------------------------------
# start_wal_checkpoint_scheduler / stop_wal_checkpoint_scheduler
# ---------------------------------------------------------------------------


class TestStartStopWalScheduler:
    def test_start_first_time(self):
        with patch.object(dm, "_wal_thread", None):
            with patch.object(dm, "_wal_stop_event") as mock_event:
                with patch("threading.Thread") as mock_thread_cls:
                    mock_thread = MagicMock()
                    mock_thread_cls.return_value = mock_thread
                    dm.start_wal_checkpoint_scheduler()
                    mock_event.clear.assert_called_once()
                    mock_thread_cls.assert_called_once_with(
                        target=dm._run_wal_checkpoint, daemon=True, name="db-wal-checkpoint"
                    )
                    mock_thread.start.assert_called_once()

    def test_start_already_running(self):
        mock_existing = MagicMock()
        with patch.object(dm, "_wal_thread", mock_existing):
            with patch("threading.Thread") as mock_thread_cls:
                dm.start_wal_checkpoint_scheduler()
                mock_thread_cls.assert_not_called()

    def test_stop_with_thread(self):
        mock_thread = MagicMock()
        with patch.object(dm, "_wal_thread", mock_thread):
            with patch.object(dm, "_wal_stop_event") as mock_event:
                with patch.object(dm, "logger"):
                    dm.stop_wal_checkpoint_scheduler()
                mock_event.set.assert_called_once()
                mock_thread.join.assert_called_once_with(timeout=1)

    def test_stop_without_thread(self):
        with patch.object(dm, "_wal_thread", None):
            with patch.object(dm, "_wal_stop_event") as mock_event:
                with patch.object(dm, "logger"):
                    dm.stop_wal_checkpoint_scheduler()
                mock_event.set.assert_called_once()
