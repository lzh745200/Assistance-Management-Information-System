"""Database engine and session configuration.

SQLite performance optimizations:
- WAL mode for concurrent read/write
- NORMAL synchronous (balances safety and performance)
- busy_timeout to avoid SQLITE_BUSY errors
- Increased cache_size (8MB) and mmap_size (256MB)
- Memory temp store
- WAL auto-checkpoint at 1000 pages
"""

import logging
import threading
from queue import Queue
from typing import Any, Callable

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    pool_size=getattr(settings, "DB_POOL_SIZE", 5),
    max_overflow=getattr(settings, "DB_MAX_OVERFLOW", 10),
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and performance PRAGMAs for SQLite connections."""
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_connection.cursor()
        # Journal and consistency
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        # Performance optimizations — synchronous=NORMAL is safe with WAL
        # (WAL mode already protects against corruption; FULL is redundant)
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Busy timeout: wait 5 seconds instead of immediately returning SQLITE_BUSY
        cursor.execute("PRAGMA busy_timeout=5000")
        # Increase page cache from default 2MB to 16MB (larger cache = fewer disk reads)
        cursor.execute("PRAGMA cache_size=-16000")
        # Memory-mapped I/O — up to 256MB for faster reads
        cursor.execute("PRAGMA mmap_size=268435456")
        # Store temporary tables/indexes in memory
        cursor.execute("PRAGMA temp_store=MEMORY")
        # Auto-checkpoint WAL after 1000 pages to prevent unbounded growth
        cursor.execute("PRAGMA wal_autocheckpoint=1000")
        # Enable automatic index creation for queries (SQLite 3.32+)
        cursor.execute("PRAGMA automatic_index=ON")
        # SQLCipher encryption key (only when enabled and key file exists)
        if getattr(settings, "DB_ENCRYPTION_ENABLED", False):
            try:
                from pathlib import Path as _Path
                key_file = _Path("config/db.key")
                if key_file.exists():
                    key = key_file.read_text().strip()
                    if key:
                        cursor.execute(f"PRAGMA key = '{key}'")
                        logger.info("SQLCipher encryption enabled for database")
            except Exception as _enc_err:
                logger.warning("Failed to set SQLCipher key: %s", _enc_err)
        cursor.close()
        logger.debug("SQLite PRAGMAs set: WAL, NORMAL sync, 16MB cache, 256MB mmap")


def get_db():
    """FastAPI dependency: yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# SQLite write queue — serializes writes to prevent SQLITE_BUSY under concurrency
# ---------------------------------------------------------------------------

class SQLiteWriteQueue:
    """Serializes SQLite write operations to prevent concurrent-write errors.

    SQLite supports only one writer at a time (even in WAL mode).  Under
    concurrent load (e.g. batch imports, data-sync, multiple API calls) the
    database can return ``SQLITE_BUSY``.  This queue ensures writes are
    executed sequentially, with an optional timeout.

    Usage::

        from app.core.database import write_queue

        result = write_queue.enqueue(lambda: some_db_write(db), timeout=30.0)
    """

    def __init__(self):
        self._queue: Queue = Queue()
        self._worker: threading.Thread | None = None

    def _ensure_worker(self) -> None:
        """Lazily start the writer thread on first use."""
        if self._worker is None:
            self._worker = threading.Thread(target=self._process, daemon=True, name="sqlite-writer")
            self._worker.start()

    def enqueue(self, fn: Callable[[], Any], timeout: float = 30.0) -> Any:
        """Enqueue a write operation and block until it completes.

        Args:
            fn: Zero-argument callable that performs the write.
            timeout: Maximum seconds to wait for the operation.

        Returns:
            The return value of *fn*.

        Raises:
            TimeoutError: If the operation does not complete within *timeout*.
        """
        self._ensure_worker()
        result_holder: dict = {"result": None, "error": None, "done": threading.Event()}
        self._queue.put((fn, result_holder))
        if not result_holder["done"].wait(timeout):
            raise TimeoutError(f"数据库写入操作超时（{timeout}秒）")
        if result_holder["error"]:
            raise result_holder["error"]
        return result_holder["result"]

    def _process(self) -> None:
        while True:
            fn, holder = self._queue.get()
            try:
                holder["result"] = fn()
            except Exception as e:
                holder["error"] = e
            finally:
                holder["done"].set()

    @property
    def pending(self) -> int:
        """Number of write operations waiting in the queue."""
        return self._queue.qsize()


# Global singleton — shared across all threads in the process.
write_queue = SQLiteWriteQueue()


# ---------------------------------------------------------------------------
# Database maintenance helper
#
# NOTE: For production optimize/vacuum operations, prefer the canonical
# implementation in ``app/utils/db_performance.py`` which integrates with
# the connection pool and existing monitoring infrastructure.
# ---------------------------------------------------------------------------
