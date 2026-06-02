"""Database root configuration.

Provides a lazy database-session factory that other modules can import
without causing circular dependency issues with the :mod:`app.core.database`
module.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_db_session_factory = None
_db_url: Optional[str] = None


def init_database() -> None:
    """Initialise the database engine and session factory.

    Must be called once during application startup.  Repeated calls are
    harmless (no-op).
    """
    global _db_session_factory, _db_url
    if _db_session_factory is not None:
        return

    try:
        from app.core.database import SessionLocal, DATABASE_URL  # type: ignore[import-untyped]

        _db_session_factory = SessionLocal
        _db_url = DATABASE_URL
        logger.info("数据库会话工厂已初始化 (type=%s)", "sqlite" if "sqlite" in (DATABASE_URL or "") else "other")
    except Exception:
        logger.exception("数据库初始化失败")


def get_session() -> Session:
    """Create and return a new database session.

    The caller is responsible for closing the session.

    Raises:
        RuntimeError: If :func:`init_database` has not been called.
    """
    if _db_session_factory is None:
        init_database()
    if _db_session_factory is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    return _db_session_factory()


def get_db_url() -> str:
    """Return the active database URL.

    Returns an empty string if the database has not been initialised.
    """
    if _db_url is None:
        try:
            from app.core.database import DATABASE_URL  # type: ignore[import-untyped]

            return DATABASE_URL
        except Exception:
            return ""
    return _db_url
