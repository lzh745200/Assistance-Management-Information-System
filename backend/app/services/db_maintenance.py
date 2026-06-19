"""SQLite 定期维护 — VACUUM + PRAGMA optimize + WAL checkpoint。

在后台线程中定期执行，不阻塞主请求处理。
"""

import logging
import threading

logger = logging.getLogger(__name__)

_maintenance_thread: threading.Thread | None = None
_stop_event = threading.Event()
# 维护间隔（秒）：首次 5 分钟后执行，之后每 6 小时
_INITIAL_DELAY = 300
_INTERVAL = 21600


def _run_maintenance():
    """后台线程：定期执行 SQLite 维护操作。"""
    if _stop_event.wait(_INITIAL_DELAY):  # 用 Event.wait 替代 time.sleep — stop 时立即唤醒
        return
    while not _stop_event.is_set():
        try:
            _do_maintenance()
        except Exception:
            logger.warning("数据库维护失败", exc_info=True)
        _stop_event.wait(_INTERVAL)


def _do_maintenance():
    """执行单次维护：VACUUM + PRAGMA optimize + WAL checkpoint。"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        conn = db.connection().connection  # raw sqlite3 connection
        cursor = conn.cursor()
        # WAL checkpoint: 将 WAL 数据写回主数据库，防止 WAL 无限增长
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        # 回收已删除记录的空间，整理碎片
        cursor.execute("VACUUM")
        # 更新查询优化器统计信息
        cursor.execute("PRAGMA optimize")
        cursor.close()
        logger.info("SQLite 定期维护完成 (WAL checkpoint + VACUUM + optimize)")
    except Exception as e:
        logger.warning("SQLite 维护操作失败: %s", e)
    finally:
        db.close()


def start_db_maintenance():
    """启动后台数据库维护线程。"""
    global _maintenance_thread
    if _maintenance_thread is not None:
        return
    _stop_event.clear()
    _maintenance_thread = threading.Thread(
        target=_run_maintenance, daemon=True, name="db-maintenance"
    )
    _maintenance_thread.start()
    logger.info("数据库定期维护已启动 (间隔 %d 秒)", _INTERVAL)


def stop_db_maintenance():
    """停止后台数据库维护线程。"""
    _stop_event.set()
    if _maintenance_thread:
        _maintenance_thread.join(timeout=1)
    logger.info("数据库定期维护已停止")
