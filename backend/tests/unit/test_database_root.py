"""Tests for app.core.database_root - zero coverage → 100%"""

import pytest
import sys
from unittest.mock import MagicMock, patch
import app.core.database_root as db_root


class TestInitDatabase:
    def setup_method(self):
        db_root._db_session_factory = None
        db_root._db_url = None

    def teardown_method(self):
        db_root._db_session_factory = None
        db_root._db_url = None

    def test_first_call_imports_and_sets_factory(self):
        mock_session = MagicMock(name="SessionLocal")
        with patch(
            "app.core.database.SessionLocal", mock_session
        ), patch(
            "app.core.database.DATABASE_URL", "sqlite:///test.db"
        ):
            db_root.init_database()
            assert db_root._db_session_factory is mock_session
            assert db_root._db_url == "sqlite:///test.db"

    def test_repeated_call_is_noop(self):
        mock_factory = MagicMock(name="ExistingFactory")
        db_root._db_session_factory = mock_factory
        db_root._db_url = "postgresql://existing"

        db_root.init_database()
        assert db_root._db_session_factory is mock_factory
        assert db_root._db_url == "postgresql://existing"

    def test_import_error_is_caught(self, monkeypatch):
        db_root._db_session_factory = None
        db_root._db_url = None
        import builtins
        real_import = builtins.__import__

        def block_import(name, *args, **kwargs):
            if name == "app.core.database":
                raise ImportError("simulated")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", block_import)
        db_root.init_database()
        assert db_root._db_session_factory is None
        assert db_root._db_url is None


class TestGetSession:
    def setup_method(self):
        db_root._db_session_factory = None
        db_root._db_url = None

    def teardown_method(self):
        db_root._db_session_factory = None
        db_root._db_url = None

    def test_auto_inits_when_not_initialized(self):
        mock_factory = MagicMock(return_value=MagicMock(name="session"))
        with patch(
            "app.core.database.SessionLocal", mock_factory
        ), patch(
            "app.core.database.DATABASE_URL", "sqlite:///auto.db"
        ):
            session = db_root.get_session()
            mock_factory.assert_called_once()
            assert session is mock_factory.return_value

    def test_returns_session_when_initialized(self):
        mock_factory = MagicMock(return_value=MagicMock(name="session"))
        db_root._db_session_factory = mock_factory
        db_root._db_url = "sqlite:///ready.db"

        session = db_root.get_session()
        mock_factory.assert_called_once()
        assert session is mock_factory.return_value

    def test_raises_runtime_error_when_init_fails(self):
        db_root._db_session_factory = None
        db_root._db_url = None
        with patch.object(db_root, "init_database", return_value=None):
            with pytest.raises(RuntimeError, match="数据库未初始化"):
                db_root.get_session()


class TestGetDbUrl:
    def setup_method(self):
        db_root._db_session_factory = None
        db_root._db_url = None

    def teardown_method(self):
        db_root._db_session_factory = None
        db_root._db_url = None

    def test_returns_stored_url(self):
        db_root._db_url = "postgresql://stored"
        assert db_root.get_db_url() == "postgresql://stored"

    def test_falls_back_to_import_when_not_set(self):
        db_root._db_url = None
        with patch(
            "app.core.database.DATABASE_URL", "postgresql://imported"
        ):
            assert db_root.get_db_url() == "postgresql://imported"

    def test_import_failure_returns_empty(self, monkeypatch):
        db_root._db_url = None
        import builtins
        real_import = builtins.__import__

        def block_import(name, *args, **kwargs):
            if name == "app.core.database":
                raise ImportError("simulated")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", block_import)
        assert db_root.get_db_url() == ""
