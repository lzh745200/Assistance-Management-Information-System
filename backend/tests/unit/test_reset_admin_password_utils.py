"""Tests for app.utils.reset_admin_password — 100% coverage target.

覆盖: validate_password_strength / _default_db_path / _resolve_env /
reset_admin_password / main。
"""

import os
import sqlite3
import sys
from unittest.mock import patch

import pytest

from app.utils.reset_admin_password import (
    PasswordTooWeakError,
    _default_db_path,
    _resolve_env,
    main,
    reset_admin_password,
    validate_password_strength,
)


class TestValidatePasswordStrength:
    def test_strong_password_passes(self):
        validate_password_strength("StrongPass1!")

    def test_too_short_raises(self):
        with pytest.raises(PasswordTooWeakError):
            validate_password_strength("Short1!")

    def test_missing_uppercase_raises(self):
        with pytest.raises(PasswordTooWeakError):
            validate_password_strength("lowercase1!")

    def test_missing_lowercase_raises(self):
        with pytest.raises(PasswordTooWeakError):
            validate_password_strength("UPPERCASE1!")

    def test_missing_digit_raises(self):
        with pytest.raises(PasswordTooWeakError):
            validate_password_strength("NoDigits!")

    def test_missing_special_raises(self):
        with pytest.raises(PasswordTooWeakError):
            validate_password_strength("NoSpecial1")


class TestPathHelpers:
    def test_default_db_path(self):
        path = _default_db_path()
        assert path.endswith("data\\rural_revitalization.db") or path.endswith("data/rural_revitalization.db")

    def test_resolve_env_expands_vars(self):
        os.environ["_TEST_RESET_ADMIN_DIR"] = "C:/tmp"
        try:
            assert _resolve_env("%_TEST_RESET_ADMIN_DIR%/x") == "C:/tmp/x"
        finally:
            del os.environ["_TEST_RESET_ADMIN_DIR"]

    def test_resolve_env_expands_user(self):
        resolved = _resolve_env("~")
        assert not resolved.startswith("~")


class TestResetAdminPassword:
    def test_weak_password_raises(self, tmp_path):
        db_path = tmp_path / "t.db"
        _create_users_table(str(db_path), [("admin", "old", 1)])
        with pytest.raises(PasswordTooWeakError):
            reset_admin_password(str(db_path), "weak")

    def test_missing_db_file_returns_false(self, tmp_path, capsys):
        result = reset_admin_password(str(tmp_path / "nope.db"), "StrongPass1!")
        assert result is False
        assert "数据库文件不存在" in capsys.readouterr().out

    def test_admin_not_found_lists_users(self, tmp_path, capsys):
        db_path = tmp_path / "t.db"
        _create_users_table(str(db_path), [("zhangsan", "old", 1)])
        result = reset_admin_password(str(db_path), "StrongPass1!")
        assert result is False
        out = capsys.readouterr().out
        assert "未找到 admin 用户" in out
        assert "zhangsan" in out

    def test_success_clear_flag(self, tmp_path):
        db_path = tmp_path / "t.db"
        _create_users_table(str(db_path), [("admin", "old-hash", 1)])
        result = reset_admin_password(str(db_path), "StrongPass1!")
        assert result is True
        row = sqlite3.connect(str(db_path)).execute(
            "SELECT hashed_password, must_change_password FROM users WHERE username='admin'"
        ).fetchone()
        assert row[0] != "old-hash"
        assert row[1] == 0

    def test_success_keep_flag(self, tmp_path):
        db_path = tmp_path / "t.db"
        _create_users_table(str(db_path), [("admin", "old-hash", 1)])
        result = reset_admin_password(str(db_path), "StrongPass1!", clear_flag=False)
        assert result is True
        row = sqlite3.connect(str(db_path)).execute(
            "SELECT must_change_password FROM users WHERE username='admin'"
        ).fetchone()
        assert row[0] == 1

    def test_database_error_returns_false(self, tmp_path, capsys):
        db_path = tmp_path / "t.db"
        db_path.write_bytes(b"not-a-sqlite-db")
        result = reset_admin_password(str(db_path), "StrongPass1!")
        assert result is False
        assert "重置失败" in capsys.readouterr().out


class TestMain:
    def test_weak_password_exits_2(self, tmp_path, capsys):
        with patch.object(sys, "argv", ["reset_admin_password", "--password", "weak"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 2
        assert "密码不符合复杂度要求" in capsys.readouterr().out

    def test_missing_db_exits_1(self, tmp_path, capsys):
        with patch.object(sys, "argv", ["reset_admin_password", "--password", "StrongPass1!",
                                        "--db", str(tmp_path / "nope.db")]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1

    def test_success_exits_0(self, tmp_path, capsys):
        db_path = tmp_path / "t.db"
        _create_users_table(str(db_path), [("admin", "old-hash", 1)])
        with patch.object(sys, "argv", ["reset_admin_password", "--password", "StrongPass1!",
                                        "--db", str(db_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 0
        assert "已重置" in capsys.readouterr().out


def _create_users_table(db_path: str, rows):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, "
        "hashed_password TEXT, must_change_password INTEGER, role TEXT)"
    )
    for username, hashed, flag in rows:
        conn.execute(
            "INSERT INTO users (username, hashed_password, must_change_password, role) "
            "VALUES (?, ?, ?, 'admin')",
            (username, hashed, flag),
        )
    conn.commit()
    conn.close()
