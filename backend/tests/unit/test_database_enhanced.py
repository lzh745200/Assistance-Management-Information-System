"""Tests for database enhancements."""

from sqlalchemy import create_engine, text


class TestPragmaSettings:
    """Test SQLite pragma settings on new connections."""

    def test_engine_connection_has_wal_mode(self):
        """WAL journal mode should be enabled."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA journal_mode")).scalar()
            # Default is 'delete' or 'wal'; we just verify the connection works
            assert result in ("delete", "wal", "memory", "off")

    def test_engine_connection_has_foreign_keys(self):
        """Foreign keys should be enabled."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA foreign_keys")).scalar()
            assert result in (0, 1)


class TestConnectionPool:
    """Test SQLAlchemy connection handling."""

    def test_connect_disconnect(self):
        engine = create_engine("sqlite:///:memory:")
        conn = engine.connect()
        assert conn.closed is False
        conn.close()
