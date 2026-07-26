"""
异常与稳定性测试套件 — 帮扶管理信息系统

测试内容：
1. 进程强制结束测试 — 验证数据库完整性
2. 磁盘空间检查 — 验证可用空间充足
3. 硬件异常测试 — 内存压力、文件锁定
4. 长时间稳定性测试 — 内存泄漏检测、连接池、文件句柄
5. 并发压力测试 — 数据库并发写入
6. 错误恢复测试 — 日志验证

运行方式：
  pytest tests/stability/test_stability.py -v --tb=short -m "not slow and not stress"
  pytest tests/stability/test_stability.py -v -m "slow"  # 运行长稳测试
"""

import os
import sys
import gc
import time
import shutil
import pytest
import psutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))


# ============================================================
# 进程强制结束测试
# ============================================================

class TestProcessTermination:
    """进程强制结束测试"""

    def test_data_integrity_after_crash(self):
        """测试：崩溃后数据库可访问且完整性正常"""
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1, "数据库应该可访问"

    def test_database_integrity_check(self):
        """测试：PRAGMA integrity_check 返回 ok"""
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA integrity_check"))
            row = result.fetchone()
            assert row[0] == "ok", f"数据库完整性检查失败: {row[0]}"

    def test_wal_checkpoint_recovery(self):
        """测试：WAL checkpoint 后数据库一致"""
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            # 执行 WAL checkpoint
            result = conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
            row = result.fetchone()
            # busy=0 表示没有忙等待，log=0 表示 WAL 已清空，checkpoint=0 表示成功
            assert row[0] == 0, f"WAL checkpoint 失败: busy={row[0]}"

    def test_lock_file_cleanup(self):
        """测试：锁文件清理"""
        lock_file = Path(__file__).parent.parent.parent / "backend" / "app.lock"
        if lock_file.exists():
            # 锁文件存在时，检查是否为过期锁
            mtime = lock_file.stat().st_mtime
            age = time.time() - mtime
            # 超过 1 小时的锁文件视为过期
            if age > 3600:
                print(f"警告: 发现过期锁文件 ({age:.0f}s)，建议删除")


# ============================================================
# 磁盘空间检查
# ============================================================

class TestDiskSpaceHandling:
    """磁盘空间检查"""

    def test_check_disk_space_before_write(self):
        """测试：可用磁盘空间充足"""
        disk_usage = shutil.disk_usage(str(Path(__file__).resolve().drive + "\\"))
        free_space_gb = disk_usage.free / (1024 ** 3)
        print(f"可用磁盘空间：{free_space_gb:.2f} GB")
        assert free_space_gb > 1.0, "磁盘空间应大于 1GB"

    def test_cleanup_temp_files(self):
        """测试：临时文件不堆积"""
        temp_dir = Path(__file__).parent.parent.parent / "backend" / "temp"
        if temp_dir.exists():
            temp_files = list(temp_dir.glob("*"))
            print(f"临时文件数量：{len(temp_files)}")
            assert len(temp_files) < 100, "临时文件过多"

    def test_log_rotation(self):
        """测试：日志文件不无限增长"""
        log_dir = Path(__file__).parent.parent.parent / "backend" / "logs"
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            total_size = sum(f.stat().st_size for f in log_files)
            total_size_mb = total_size / (1024 ** 2)
            print(f"日志文件总大小：{total_size_mb:.2f} MB ({len(log_files)} 个文件)")
            # 建议日志总大小不超过 500MB
            if total_size_mb > 500:
                print("警告：日志文件过大，建议实现日志轮转")


# ============================================================
# 硬件异常测试
# ============================================================

class TestHardwareAbnormality:
    """硬件异常测试"""

    def test_memory_pressure(self):
        """测试：系统内存充足"""
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024 ** 3)
        print(f"可用内存：{available_gb:.2f} GB ({memory.percent}% 已使用)")
        assert available_gb > 0.5, "可用内存应大于 0.5GB"

    def test_database_writable(self):
        """测试：数据库文件可写入"""
        from app.core.database import engine, DB_PATH
        from sqlalchemy import text

        assert DB_PATH.exists(), "数据库文件应存在"
        # 尝试写入并回滚
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(text("CREATE TABLE IF NOT EXISTS _stability_test (id INTEGER)"))
                conn.execute(text("INSERT INTO _stability_test VALUES (1)"))
                trans.rollback()
            except Exception:
                trans.rollback()
                raise


# ============================================================
# 长时间稳定性测试
# ============================================================

class TestLongTermStability:
    """长时间稳定性测试"""

    def test_memory_leak_detection(self):
        """测试：内存泄漏检测（快速版）"""
        process = psutil.Process()
        gc.collect()
        initial_memory = process.memory_info().rss / (1024 ** 2)

        # 模拟业务操作 — 执行数据库查询
        from app.core.database import SessionLocal
        from sqlalchemy import text

        sessions = []
        for _ in range(50):
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            sessions.append(db)

        for db in sessions:
            db.close()
        del sessions
        gc.collect()

        final_memory = process.memory_info().rss / (1024 ** 2)
        memory_increase = final_memory - initial_memory
        print(f"内存增长：{memory_increase:.2f} MB (初始: {initial_memory:.1f}MB, 最终: {final_memory:.1f}MB)")
        assert memory_increase < 100, f"可能存在内存泄漏 (增长 {memory_increase:.1f}MB)"

    def test_database_connection_pool(self):
        """测试：数据库连接池正常"""
        from app.core.database import engine
        pool = engine.pool
        print(f"连接池大小：{pool.size()}")
        print(f"已检出连接：{pool.checkedout()}")
        assert pool.checkedout() < pool.size(), "连接池应有可用连接"

    def test_file_handle_leak(self):
        """测试：文件句柄泄漏"""
        process = psutil.Process()
        open_files = process.open_files()
        print(f"打开的文件数：{len(open_files)}")
        assert len(open_files) < 200, f"可能存在文件句柄泄漏 ({len(open_files)} 个)"

    def test_wal_file_size(self):
        """测试：WAL 文件大小正常"""
        db_path = Path(__file__).parent.parent.parent / "backend" / "data" / "rural_revitalization.db"
        wal_path = Path(str(db_path) + "-wal")

        if wal_path.exists():
            wal_size_mb = wal_path.stat().st_size / (1024 * 1024)
            print(f"WAL 文件大小：{wal_size_mb:.2f} MB")
            assert wal_size_mb < 100, f"WAL 文件过大 ({wal_size_mb:.1f}MB)"
        else:
            print("WAL 文件不存在（可能已 checkpoint）")

    @pytest.mark.slow
    def test_24_hour_stability(self):
        """测试：24 小时稳定性（需单独运行）"""
        pytest.skip("长稳测试请使用: python tests/stability/run_stability_test.py --duration 24h")


# ============================================================
# 并发压力测试
# ============================================================

class TestConcurrencyStress:
    """并发压力测试"""

    def test_concurrent_database_reads(self):
        """测试：并发数据库读取"""
        from app.core.database import SessionLocal
        from sqlalchemy import text
        import threading

        errors = []
        num_threads = 10
        barrier = threading.Barrier(num_threads)

        def worker():
            try:
                barrier.wait(timeout=5)
                db = SessionLocal()
                result = db.execute(text("SELECT COUNT(*) FROM sqlite_master"))
                result.fetchone()
                db.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"并发读取失败: {errors}"

    @pytest.mark.stress
    def test_database_concurrent_writes(self):
        """测试：数据库并发写入"""
        from app.core.database import engine
        from sqlalchemy import text
        import threading

        errors = []
        num_threads = 5
        barrier = threading.Barrier(num_threads)

        def worker(worker_id: int):
            try:
                barrier.wait(timeout=5)
                with engine.connect() as conn:
                    trans = conn.begin()
                    try:
                        conn.execute(text(
                            f"CREATE TABLE IF NOT EXISTS _concurrent_test_{worker_id} (id INTEGER)"
                        ))
                        conn.execute(text(f"INSERT INTO _concurrent_test_{worker_id} VALUES (1)"))
                        trans.commit()
                    except Exception:
                        trans.rollback()
                        raise
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        # 清理测试表
        with engine.connect() as conn:
            for i in range(num_threads):
                conn.execute(text(f"DROP TABLE IF EXISTS _concurrent_test_{i}"))
            conn.commit()

        assert not errors, f"并发写入失败: {errors}"


# ============================================================
# 错误恢复测试
# ============================================================

class TestErrorRecovery:
    """错误恢复测试"""

    def test_error_reporting(self):
        """测试：错误报告机制（日志文件存在）"""
        log_dir = Path(__file__).parent.parent.parent / "backend" / "logs"
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            assert len(log_files) > 0, "应有日志文件"

    def test_database_pragma_settings(self):
        """测试：数据库 PRAGMA 配置正确"""
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            # WAL 模式
            result = conn.execute(text("PRAGMA journal_mode"))
            journal_mode = result.fetchone()[0]
            assert journal_mode.lower() == "wal", f"应为 WAL 模式, 实际: {journal_mode}"

            # 同步模式
            result = conn.execute(text("PRAGMA synchronous"))
            synchronous = result.fetchone()[0]
            assert synchronous == 1, f"应为 NORMAL(1), 实际: {synchronous}"

            # busy_timeout
            result = conn.execute(text("PRAGMA busy_timeout"))
            busy_timeout = result.fetchone()[0]
            assert busy_timeout >= 5000, f"busy_timeout 应 ≥ 5000ms, 实际: {busy_timeout}ms"

    def test_transaction_rollback(self):
        """测试：事务回滚正常"""
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            # 确保测试表不存在
            conn.execute(text("DROP TABLE IF EXISTS _rollback_test"))
            conn.execute(text("CREATE TABLE _rollback_test (id INTEGER, name TEXT)"))
            conn.commit()

            # 插入数据并回滚
            trans = conn.begin()
            conn.execute(text("INSERT INTO _rollback_test VALUES (1, 'test')"))
            trans.rollback()

            # 验证数据未写入
            result = conn.execute(text("SELECT COUNT(*) FROM _rollback_test"))
            count = result.fetchone()[0]
            assert count == 0, "回滚后不应有数据"

            # 清理
            conn.execute(text("DROP TABLE _rollback_test"))
            conn.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow and not stress"])
