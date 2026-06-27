"""数据库维护单元测试 — 100% line/branch coverage"""
from unittest.mock import MagicMock, patch


class TestDoMaintenance:
    """覆盖 _do_maintenance 所有分支"""

    def test_success(self):
        """正常执行 WAL checkpoint + VACUUM + optimize"""
        import app.services.db_maintenance as dm

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_obj = MagicMock()
        mock_conn_obj.connection = mock_conn
        mock_db = MagicMock()
        mock_db.connection.return_value = mock_conn_obj

        with patch("app.core.database.SessionLocal", return_value=mock_db):
            dm._do_maintenance()

        # PRAGMA 调用顺序
        calls = [c[0][0] for c in mock_cursor.execute.call_args_list]
        assert "PRAGMA wal_checkpoint(TRUNCATE)" in calls
        assert "VACUUM" in calls
        assert "PRAGMA optimize" in calls
        mock_cursor.close.assert_called_once()
        mock_db.close.assert_called_once()

    def test_exception_in_maintenance(self):
        """cursor.execute 抛出异常 → 捕获并记录警告，finally 关闭 db"""
        import app.services.db_maintenance as dm

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

        args, _ = mock_log.warning.call_args
        assert args[0] == "SQLite 维护操作失败: %s"
        assert isinstance(args[1], Exception)
        assert str(args[1]) == "disk full"
        mock_db.close.assert_called_once()

    def test_exception_in_connection(self):
        """db.connection() 抛出异常 → 在 finally 中 db.close"""
        import app.services.db_maintenance as dm

        mock_db = MagicMock()
        mock_db.connection.side_effect = Exception("no connection")

        with patch("app.core.database.SessionLocal", return_value=mock_db):
            with patch.object(dm, "logger") as mock_log:
                dm._do_maintenance()

        mock_log.warning.assert_called_once()
        mock_db.close.assert_called_once()


class TestRunMaintenance:
    """覆盖 _run_maintenance 所有分支"""

    def test_one_iteration_then_exit(self):
        """循环一次后 _stop_event 被置位 → 退出"""
        import app.services.db_maintenance as dm

        with patch.object(dm, "_stop_event") as mock_event:
            mock_event.is_set.side_effect = [False, True]
            # Event.wait() 默认返回 truthy → 会在 INITIAL_DELAY 处提前退出
            mock_event.wait.return_value = False

            with patch.object(dm, "_do_maintenance") as mock_do:
                dm._run_maintenance()

        mock_do.assert_called_once()
        assert mock_event.is_set.call_count >= 2

    def test_do_maintenance_raises(self):
        """_do_maintenance 抛出异常 → 捕获并记录警告，循环继续"""
        import app.services.db_maintenance as dm

        with patch.object(dm, "_stop_event") as mock_event:
            mock_event.is_set.side_effect = [False, True]
            mock_event.wait.return_value = False

            with patch.object(dm, "_do_maintenance", side_effect=Exception("err")):
                with patch.object(dm, "logger") as mock_log:
                    dm._run_maintenance()

        mock_log.warning.assert_called_once_with(
            "数据库维护失败", exc_info=True
        )


class TestStartDbMaintenance:
    """覆盖 start_db_maintenance 所有分支"""

    def test_start_first_time(self):
        """_maintenance_thread 为 None → 创建并启动线程"""
        import app.services.db_maintenance as dm

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
        """_maintenance_thread 不为 None → 直接返回"""
        import app.services.db_maintenance as dm

        mock_existing = MagicMock()
        with patch.object(dm, "_maintenance_thread", mock_existing):
            with patch("threading.Thread") as mock_thread_cls:
                dm.start_db_maintenance()
                mock_thread_cls.assert_not_called()


class TestStopDbMaintenance:
    """覆盖 stop_db_maintenance 所有分支"""

    def test_stop_with_thread(self):
        """_maintenance_thread 存在 → set event + join"""
        import app.services.db_maintenance as dm

        mock_thread = MagicMock()
        with patch.object(dm, "_maintenance_thread", mock_thread):
            with patch.object(dm, "_stop_event") as mock_event:
                with patch.object(dm, "logger"):
                    dm.stop_db_maintenance()

        mock_event.set.assert_called_once()
        mock_thread.join.assert_called_once_with(timeout=1)

    def test_stop_without_thread(self):
        """_maintenance_thread 为 None → set event，不 join"""
        import app.services.db_maintenance as dm

        with patch.object(dm, "_maintenance_thread", None):
            with patch.object(dm, "_stop_event") as mock_event:
                with patch.object(dm, "logger"):
                    dm.stop_db_maintenance()

        mock_event.set.assert_called_once()
        # join 不应被调用
