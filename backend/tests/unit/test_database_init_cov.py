# -*- coding: utf-8 -*-
"""database_init 覆盖率补测：init_default_users 组织关联异常 + main() 全分支"""

import sys
from unittest.mock import MagicMock, patch

import pytest

import app.utils.database_init as mod


# ---------- init_default_users（226-227 及既有用户早退） ----------

def test_init_default_users_skip_when_exists():
    db = MagicMock()
    db.query.return_value.count.return_value = 3
    mod.init_default_users(db)
    db.add_all.assert_not_called()


def test_init_default_users_org_association_failure_warns():
    db = MagicMock()
    q_user = MagicMock()
    q_user.count.return_value = 0
    db.query.side_effect = [q_user, RuntimeError("org table missing")]
    mod.init_default_users(db)  # 组织关联失败仅 warning，流程继续
    db.add_all.assert_called_once()
    db.commit.assert_called_once()


# ---------- main()（307-349） ----------


def _run_main(argv):
    with patch.object(sys, "argv", argv), patch.object(
        mod.settings, "DATABASE_URL", "sqlite:///x.db"
    ), patch.object(mod, "reset_database") as rd, patch.object(
        mod, "get_database_info"
    ) as gdi, patch.object(
        mod, "check_database_connection", return_value=True
    ) as cdc, patch.object(
        mod, "create_database_if_not_exists"
    ) as cdin, patch.object(
        mod, "init_database_tables"
    ) as idt, patch.object(
        mod, "SessionLocal"
    ) as sl, patch.object(
        mod, "init_default_roles"
    ) as idr, patch.object(
        mod, "init_default_users"
    ) as idu:
        mod.main()
    return SimpleNamespaceMocks(rd, gdi, cdc, cdin, idt, sl, idr, idu)


class SimpleNamespaceMocks:
    def __init__(self, rd, gdi, cdc, cdin, idt, sl, idr, idu):
        self.reset_database = rd
        self.get_database_info = gdi
        self.check_database_connection = cdc
        self.create_database_if_not_exists = cdin
        self.init_database_tables = idt
        self.SessionLocal = sl
        self.init_default_roles = idr
        self.init_default_users = idu


def test_main_info_mode_returns_early():
    m = _run_main(["prog", "--info"])
    m.get_database_info.assert_called_once()
    m.init_database_tables.assert_not_called()


def test_main_reset_and_full_init():
    m = _run_main(["prog", "--reset"])
    m.reset_database.assert_called_once_with("sqlite:///x.db")
    m.create_database_if_not_exists.assert_called_once()
    m.init_database_tables.assert_called_once()
    m.init_default_roles.assert_called_once()
    m.init_default_users.assert_called_once()
    m.SessionLocal.return_value.close.assert_called_once()


def test_main_init_only_skips_default_data():
    m = _run_main(["prog", "--init-only"])
    m.init_default_roles.assert_not_called()
    m.init_default_users.assert_not_called()


def test_main_connection_failure_exits_early():
    with patch.object(sys, "argv", ["prog"]), patch.object(
        mod.settings, "DATABASE_URL", "sqlite:///x.db"
    ), patch.object(mod, "reset_database"), patch.object(
        mod, "get_database_info"
    ), patch.object(
        mod, "check_database_connection", return_value=False
    ), patch.object(
        mod, "create_database_if_not_exists"
    ) as cdin:
        mod.main()
    cdin.assert_not_called()


def test_main_exception_calls_sys_exit():
    with patch.object(sys, "argv", ["prog"]), patch.object(
        mod.settings, "DATABASE_URL", "sqlite:///x.db"
    ), patch.object(mod, "reset_database"), patch.object(
        mod, "get_database_info"
    ), patch.object(
        mod, "check_database_connection", side_effect=RuntimeError("boom")
    ):
        with pytest.raises(SystemExit) as exc:
            mod.main()
    assert exc.value.code == 1
