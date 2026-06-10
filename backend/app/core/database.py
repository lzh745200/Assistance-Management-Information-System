"""
Database engine and session configuration.

军用级离线桌面管理系统 - 数据库核心配置
针对 SQLite 进行了深度调优，确保在单机/多机物理协同环境下的数据一致性与极致性能。

SQLite 性能优化策略：
1. WAL (Write-Ahead Logging) 模式：实现并发读写，读写互不阻塞。
2. NORMAL 同步模式：在 WAL 下兼顾数据安全与写入性能。
3. 动态 PRAGMA 调优：根据现代硬件自动调整 cache_size (64MB) 和 mmap_size (512MB)。
4. 长事务独占锁机制：解决大批量数据导入 (.rrs) 时的 SQLITE_BUSY 问题。
"""

import logging
import threading
from contextlib import contextmanager
from pathlib import Path
from queue import Queue
from typing import Any, Callable, Generator, Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# SQLite 必须禁用线程检查，以支持 FastAPI 的多线程/协程环境
connect_args = {"check_same_thread": False} if IS_SQLITE else {}

# 引擎配置
# 对于 SQLite，使用 QueuePool 并限制连接数，避免过多连接导致文件锁竞争
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool if IS_SQLITE else None,
    pool_size=getattr(settings, "DB_POOL_SIZE", 10),
    max_overflow=getattr(settings, "DB_MAX_OVERFLOW", 20),
    pool_pre_ping=True,  # 连接池健康检查，剔除断开的连接
    pool_recycle=3600,   # 每小时回收连接，防止长时间运行导致的连接僵死
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """
    每次建立新连接时，自动执行 SQLite PRAGMA 性能调优。
    仅在 SQLite 数据库下生效。
    """
    if not IS_SQLITE:
        return

    cursor = dbapi_connection.cursor()
    
    # 1. 核心日志与一致性
    cursor.execute("PRAGMA journal_mode=WAL")         # 启用 WAL 模式，支持并发读写
    cursor.execute("PRAGMA foreign_keys=ON")          # 强制外键约束
    
    # 2. 性能与安全性平衡
    # WAL 模式下 NORMAL 已经足够安全，无需 FULL（FULL 会严重拖慢写入）
    cursor.execute("PRAGMA synchronous=NORMAL")
    
    # 3. 锁等待与超时 (军用环境硬件可能较慢或存在大事务，放宽至 10 秒)
    cursor.execute("PRAGMA busy_timeout=10000")       
    
    # 4. 内存与缓存调优 (针对现代 PC/工控机，适当放大)
    cursor.execute("PRAGMA cache_size=-64000")        # 64MB 页面缓存 (负数表示 KB)
    cursor.execute("PRAGMA mmap_size=536870912")      # 512MB 内存映射 I/O，加速全表扫描/统计
    cursor.execute("PRAGMA temp_store=MEMORY")        # 临时表/索引存储在内存中
    
    # 5. WAL 维护
    cursor.execute("PRAGMA wal_autocheckpoint=1000")  # 每 1000 页自动 checkpoint
    
    # 6. 查询优化器
    cursor.execute("PRAGMA automatic_index=ON")       # 允许自动创建临时索引
    
    # 7. SQLCipher 加密支持 (零信任安全要求)
    if getattr(settings, "DB_ENCRYPTION_ENABLED", False):
        try:
            # 兼容 PyInstaller 打包后的绝对路径
            base_dir = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent.parent))
            key_file = base_dir / "config" / "db.key"
            
            if key_file.exists():
                key = key_file.read_text(encoding="utf-8").strip()
                if key:
                    cursor.execute(f"PRAGMA key = '{key}'")
                    logger.info("SQLCipher 数据库加密已启用")
            else:
                logger.warning("未找到数据库加密密钥文件: %s", key_file)
        except Exception as _enc_err:
            logger.error("设置 SQLCipher 密钥失败: %s", _enc_err)
            
    cursor.close()
    logger.debug("SQLite PRAGMAs 初始化完成: WAL, 64MB Cache, 512MB MMAP, 10s Timeout")


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：提供数据库 Session，并在请求结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 数据库写入协调器 (SQLite Write Coordinator)
# 
# 设计原则：
# 1. 短事务 (常规 CRUD)：依赖 WAL + busy_timeout=10000 自动重试，无需加锁，性能最高。
# 2. 长事务 (.rrs 导入、大批量更新)：使用 exclusive_write() 获取独占锁，防止
#    长事务被 busy_timeout 截断，同时避免阻塞其他短事务的读取。
# ---------------------------------------------------------------------------

class SQLiteWriteCoordinator:
    """
    SQLite 写入协调器。
    解决高并发或长事务下的 SQLITE_BUSY 问题。
    """

    def __init__(self):
        # 使用 threading.Lock 实现进程内的互斥锁
        self._lock = threading.Lock()
        # 保留 Queue 以兼容旧版 enqueue 调用（不推荐在新代码中使用）
        self._queue: Queue = Queue()
        self._worker: threading.Thread | None = None

    @contextmanager
    def exclusive_write(self, timeout: float = 60.0) -> Iterator[None]:
        """
        长事务独占写上下文管理器。
        
        用法：
            with db_coordinator.exclusive_write():
                with SessionLocal() as session:
                    session.bulk_insert_mappings(...)
                    session.commit()
        """
        if not IS_SQLITE:
            # 非 SQLite 数据库（如测试时用的内存库或未来的 PG/MySQL）无需此锁
            yield
            return

        acquired = self._lock.acquire(timeout=timeout)
        if not acquired:
            raise TimeoutError(
                f"获取数据库独占写锁超时（{timeout}秒）。"
                "可能有其他大型数据导入任务正在执行，请稍后重试。"
            )
        try:
            yield
        finally:
            self._lock.release()

    def _ensure_worker(self) -> None:
        """懒加载启动后台写入线程（仅用于兼容旧的 enqueue 方法）。"""
        if self._worker is None:
            self._worker = threading.Thread(
                target=self._process_queue, 
                daemon=True, 
                name="sqlite-write-worker"
            )
            self._worker.start()

    def enqueue(self, fn: Callable[[], Any], timeout: float = 30.0) -> Any:
        """
        [向后兼容] 将写操作放入队列串行执行。
        ⚠️ 警告：在 FastAPI 同步路由中调用此方法会阻塞工作线程。
        建议新代码使用 `exclusive_write()` 上下文管理器，并将长任务放入 BackgroundTasks。
        """
        self._ensure_worker()
        result_holder: dict = {"result": None, "error": None, "done": threading.Event()}
        self._queue.put((fn, result_holder))
        
        if not result_holder["done"].wait(timeout):
            raise TimeoutError(f"数据库写入队列操作超时（{timeout}秒）")
        if result_holder["error"]:
            raise result_holder["error"]
        return result_holder["result"]

    def _process_queue(self) -> None:
        """后台线程：持续消费队列中的写操作。"""
        while True:
            fn, holder = self._queue.get()
            try:
                # 在队列消费时，也加上独占锁，确保绝对串行
                with self.exclusive_write(timeout=60.0):
                    holder["result"] = fn()
            except Exception as e:
                holder["error"] = e
            finally:
                holder["done"].set()
                self._queue.task_done()

    @property
    def pending(self) -> int:
        """队列中等待的写操作数量。"""
        return self._queue.qsize()


# 全局单例：在整个应用生命周期内共享
db_coordinator = SQLiteWriteCoordinator()

# 向后兼容别名
write_queue = db_coordinator
SQLiteWriteQueue = SQLiteWriteCoordinator  # 旧类名别名
