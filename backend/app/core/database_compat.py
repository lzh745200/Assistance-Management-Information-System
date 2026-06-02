"""Database compatibility layer.

Provides helpers that smooth over differences between SQLite and
PostgreSQL / MySQL so that the same query patterns work across all
supported backends.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def is_sqlite(url: str) -> bool:
    """Return *True* if the database URL refers to SQLite.

    Args:
        url: A SQLAlchemy-compatible database URL (e.g.
            ``"sqlite:///./data/app.db"``).
    """
    return url.startswith("sqlite")


def is_postgresql(url: str) -> bool:
    """Return *True* if the database URL refers to PostgreSQL."""
    return url.startswith("postgresql") or url.startswith("postgres")


def is_mysql(url: str) -> bool:
    """Return *True* if the database URL refers to MySQL / MariaDB."""
    return url.startswith("mysql") or url.startswith("mariadb")


def get_db_type(url: str) -> str:
    """Return a short backend identifier (``sqlite``, ``postgresql``, ``mysql``).

    Args:
        url: Database URL.
    """
    if is_sqlite(url):
        return "sqlite"
    if is_postgresql(url):
        return "postgresql"
    if is_mysql(url):
        return "mysql"
    return "unknown"


def paginate_query(
    query: Any,
    page: int = 1,
    page_size: int = 20,
    *,
    base_url: str = "",
) -> dict:
    """Apply pagination to a SQLAlchemy query.

    Args:
        query: The SQLAlchemy :class:`Query` object.
        page: 1-indexed page number.
        page_size: Number of items per page.
        base_url: Base URL used for constructing *next* / *previous* links
            (empty string returns *None* links).

    Returns:
        A dict with keys: ``items``, ``total``, ``page``, ``page_size``,
        ``pages``, ``next``, ``previous``.
    """
    import math

    total = query.count()
    pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    page = max(1, min(page, pages))

    items = query.offset((page - 1) * page_size).limit(page_size).all()

    next_url = None
    prev_url = None
    if base_url:
        sep = "&" if "?" in base_url else "?"
        if page < pages:
            next_url = f"{base_url}{sep}page={page + 1}&page_size={page_size}"
        if page > 1:
            prev_url = f"{base_url}{sep}page={page - 1}&page_size={page_size}"

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "next": next_url,
        "previous": prev_url,
    }


def like_escape(value: str) -> str:
    """Escape special characters for SQL ``LIKE`` patterns.

    Args:
        value: Raw user input to be used in a ``LIKE`` clause.

    Returns:
        Escaped string.
    """
    # The escape character is backslash; escape it first.
    for ch in ("\\", "%", "_"):
        value = value.replace(ch, f"\\{ch}")
    return value


def sqlite_regexp(expr: str, item: str) -> bool:
    """Python-side ``REGEXP`` implementation for SQLite.

    Register this function via ``engine.execute("...")`` or a
    ``@event.listens_for`` decorator to enable regular expression
    filtering in SQLite queries.

    Usage::

        from sqlalchemy import event
        @event.listens_for(engine, "connect")
        def _register_regexp(dbapi_connection, _):
            dbapi_connection.create_function("regexp", 2, sqlite_regexp)
    """
    try:
        return re.search(expr, item) is not None
    except re.error:
        return False
