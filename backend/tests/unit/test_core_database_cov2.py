# -*- coding: utf-8 -*-
"""core.database 覆盖率补测：连接关闭 optimize 钩子 + 磁盘空间检查"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import app.core.database as mod


# ---------- _on_connection_close（128-136） ----------

def test_on_connection_close_executes_optimize():
    conn = MagicMock()
    with patch.object(mod, "IS_SQLITE", True):
        mod._on_connection_close(conn, MagicMock())
    conn.cursor.assert_called_once()
    conn.cursor.return_value.execute.assert_called_once_with("PRAGMA optimize")
    conn.cursor.return_value.close.assert_called_once()


def test_on_connection_close_exception_swallowed():
    conn = MagicMock()
    conn.cursor.side_effect = RuntimeError("closed")
    with patch.object(mod, "IS_SQLITE", True):
        mod._on_connection_close(conn, MagicMock())  # 不抛异常


def test_on_connection_close_non_sqlite_returns_early():
    conn = MagicMock()
    with patch.object(mod, "IS_SQLITE", False):
        mod._on_connection_close(conn, MagicMock())
    conn.cursor.assert_not_called()


# ---------- check_disk_space（272-289） ----------

def test_check_disk_space_sufficient():
    usage = SimpleNamespace(free=500 * 1024 * 1024, total=1024 * 1024 * 1024)
    with patch("shutil.disk_usage", return_value=usage):
        r = mod.check_disk_space(min_mb=100)
    assert r["sufficient"] is True
    assert r["free_mb"] == 500
    assert r["total_mb"] == 1024
    assert "error" not in r


def test_check_disk_space_insufficient():
    usage = SimpleNamespace(free=10 * 1024 * 1024, total=1024 * 1024 * 1024)
    with patch("shutil.disk_usage", return_value=usage):
        r = mod.check_disk_space(min_mb=100)
    assert r["sufficient"] is False


def test_check_disk_space_exception():
    with patch("shutil.disk_usage", side_effect=OSError("no disk")):
        r = mod.check_disk_space()
    assert r["sufficient"] is False
    assert r["free_mb"] == -1
    assert r["error"] == "no disk"
