"""单机即时备份(T1.5): trigger_immediate_backup 幂等/后台执行/备份创建"""
import threading
from unittest.mock import MagicMock, patch

import pytest


class _FakeLock:
    def __init__(self, acquire_ok):
        self._acquire_ok = acquire_ok
        self.released = False
        self.acquire_count = 0

    def acquire(self, blocking=False):
        self.acquire_count += 1
        return self._acquire_ok

    def release(self):
        self.released = True


def _get_ib():
    import app.services.immediate_backup as ib
    return ib


def test_trigger_immediate_backup_queues_thread():
    from app.services.immediate_backup import trigger_immediate_backup

    captured = {}

    class FakeThread:
        def __init__(self, *a, **kw):
            captured["target"] = kw.get("target")
            captured["daemon"] = kw.get("daemon")
            captured["name"] = kw.get("name")

        def start(self):
            captured["started"] = True

    with patch.object(_get_ib(), "_triggered_once", _FakeLock(True)):
        with patch("app.services.immediate_backup.threading.Thread", FakeThread):
            ok = trigger_immediate_backup("测试备份", delay=0)
    assert ok is True
    assert captured["started"] is True
    assert captured["daemon"] is True
    assert captured["name"] == "immediate-backup"
    assert callable(captured["target"])


def test_trigger_immediate_backup_skip_when_busy():
    from app.services.immediate_backup import trigger_immediate_backup

    with patch.object(_get_ib(), "_triggered_once", _FakeLock(False)):
        with patch("app.services.immediate_backup.threading.Thread") as mk:
            ok = trigger_immediate_backup("测试")
    assert ok is False
    mk.assert_not_called()


def test_thread_target_creates_backup_and_releases_lock():
    """线程 target 执行: 创建备份 + 释放锁"""
    from app.services.immediate_backup import trigger_immediate_backup

    captured = {}

    class FakeThread:
        def __init__(self, *a, **kw):
            captured["target"] = kw["target"]

        def start(self):
            pass

    with patch.object(_get_ib(), "_triggered_once", _FakeLock(True)):
        with patch("app.services.immediate_backup.threading.Thread", FakeThread):
            trigger_immediate_backup("线程测试", delay=0)

    svc = MagicMock()
    record = MagicMock()
    record.file_name = "bk.zip"
    svc.create_backup.return_value = record
    mock_db = MagicMock()

    ctx = MagicMock()
    ctx.__enter__.return_value = mock_db

    with patch("app.core.transaction.get_db_context", return_value=ctx):
        with patch("app.services.backup_service.BackupService", return_value=svc) as mk_svc:
            with patch("app.services.system_config_service.get_config", return_value=""):
                fake_lock = _FakeLock(True)
                with patch.object(_get_ib(), "_triggered_once", fake_lock):
                    captured["target"]()
                    svc.create_backup.assert_called_once()
                    assert fake_lock.released is True
                    # 无 target_dir 时使用默认 BackupService(db)
                    assert mk_svc.call_args.args[0] is mock_db


def test_thread_target_uses_target_dir():
    from app.services.immediate_backup import trigger_immediate_backup

    captured = {}

    class FakeThread:
        def __init__(self, *a, **kw):
            captured["target"] = kw["target"]

        def start(self):
            pass

    with patch.object(_get_ib(), "_triggered_once", _FakeLock(True)):
        with patch("app.services.immediate_backup.threading.Thread", FakeThread):
            trigger_immediate_backup("目标目录", delay=0)

    svc = MagicMock()
    mock_db = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = mock_db

    with patch("app.core.transaction.get_db_context", return_value=ctx):
        with patch("app.services.backup_service.BackupService", return_value=svc) as mk_svc:
            with patch("app.services.system_config_service.get_config", return_value="E:\\bk"):
                fake_lock = _FakeLock(True)
                with patch.object(_get_ib(), "_triggered_once", fake_lock):
                    captured["target"]()
                    _, kwargs = mk_svc.call_args
                    assert kwargs["backup_dir"] == "E:\\bk"
                    assert fake_lock.released is True


def test_thread_target_error_releases_lock():
    from app.services.immediate_backup import trigger_immediate_backup

    captured = {}

    class FakeThread:
        def __init__(self, *a, **kw):
            captured["target"] = kw["target"]

        def start(self):
            pass

    with patch.object(_get_ib(), "_triggered_once", _FakeLock(True)):
        with patch("app.services.immediate_backup.threading.Thread", FakeThread):
            trigger_immediate_backup("异常", delay=0)

    ctx = MagicMock()
    ctx.__enter__.side_effect = RuntimeError("db down")

    with patch("app.core.transaction.get_db_context", return_value=ctx):
        fake_lock = _FakeLock(True)
        with patch.object(_get_ib(), "_triggered_once", fake_lock):
            captured["target"]()  # 不应抛异常
            assert fake_lock.released is True
