"""
测试 - app.services.database_health_service
覆盖率目标: 100%
"""
import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

class TestDatabaseHealthService:
    """测试 DatabaseHealthService"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        from app.services.database_health_service import DatabaseHealthService
        return DatabaseHealthService()

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        # 创建一些表和索引
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("CREATE INDEX idx_test ON test_table(name)")
        conn.commit()
        conn.close()

        yield db_path

        # 清理
        import os
        try:
            os.unlink(db_path)
        except:
            pass

    def test_service_creation(self, service):
        """测试服务创建"""
        assert service is not None
        assert service.monitoring is False
        assert service.stats is not None
        assert service.health_status is not None

    def test_get_db_path(self, service):
        """测试获取数据库路径"""
        path = service._get_db_path()
        assert isinstance(path, Path)

    def test_check_integrity_no_db(self, service):
        """测试完整性检查 - 数据库不存在"""
        with patch.object(service, 'db_path', Path('/nonexistent/db.db')):
            result = service.check_integrity()
            assert result["status"] == "error"
            assert "不存在" in result["message"]

    def test_check_integrity_with_db(self, service, temp_db):
        """测试完整性检查 - 正常数据库"""
        with patch.object(service, 'db_path', Path(temp_db)):
            result = service.check_integrity()
            assert result["status"] == "healthy"

    def test_check_integrity_exception(self, service):
        """测试完整性检查异常处理"""
        with patch.object(service, 'db_path', MagicMock(exists=MagicMock(return_value=True))):
            with patch('sqlite3.connect', side_effect=Exception("DB Error")):
                result = service.check_integrity()
                assert result["status"] == "error"
                assert service.stats["integrity_errors"] > 0

    def test_quick_check_no_db(self, service):
        """测试快速检查 - 数据库不存在"""
        with patch.object(service, 'db_path', Path('/nonexistent/db.db')):
            result = service.quick_check()
            assert result["status"] == "error"

    def test_quick_check_with_db(self, service, temp_db):
        """测试快速检查 - 正常数据库"""
        with patch.object(service, 'db_path', Path(temp_db)):
            result = service.quick_check()
            assert result["status"] == "ok"
            assert "db_size" in result
            assert "table_count" in result

    def test_quick_check_exception(self, service):
        """测试快速检查异常处理"""
        with patch.object(service, 'db_path', MagicMock(exists=MagicMock(return_value=True))):
            with patch('sqlite3.connect', side_effect=Exception("DB Error")):
                result = service.quick_check()
                assert result["status"] == "error"

    def test_vacuum_database_no_db(self, service):
        """测试 VACUUM - 数据库不存在"""
        with patch.object(service, 'db_path', Path('/nonexistent/db.db')):
            result = service.vacuum_database()
            assert result["status"] == "error"

    def test_vacuum_database_with_db(self, service, temp_db):
        """测试 VACUUM - 正常数据库"""
        with patch.object(service, 'db_path', Path(temp_db)):
            result = service.vacuum_database()
            assert result["status"] == "ok"
            assert "size_before" in result
            assert "size_after" in result

    def test_vacuum_database_exception(self, service):
        """测试 VACUUM 异常处理"""
        with patch.object(service, 'db_path', MagicMock(exists=MagicMock(return_value=True))):
            with patch('sqlite3.connect', side_effect=Exception("DB Error")):
                result = service.vacuum_database()
                assert result["status"] == "error"

    def test_check_indexes_no_db(self, service):
        """测试检查索引 - 数据库不存在"""
        with patch.object(service, 'db_path', Path('/nonexistent/db.db')):
            result = service.check_indexes()
            assert result["status"] == "error"

    def test_check_indexes_with_db(self, service, temp_db):
        """测试检查索引 - 正常数据库"""
        with patch.object(service, 'db_path', Path(temp_db)):
            result = service.check_indexes()
            assert result["status"] == "ok"
            assert result["index_count"] == 1

    def test_check_indexes_exception(self, service):
        """测试检查索引异常处理"""
        with patch.object(service, 'db_path', MagicMock(exists=MagicMock(return_value=True))):
            with patch('sqlite3.connect', side_effect=Exception("DB Error")):
                result = service.check_indexes()
                assert result["status"] == "error"

    def test_analyze_database_no_db(self, service):
        """测试分析数据库 - 数据库不存在"""
        with patch.object(service, 'db_path', Path('/nonexistent/db.db')):
            result = service.analyze_database()
            assert result["status"] == "error"

    def test_analyze_database_with_db(self, service, temp_db):
        """测试分析数据库 - 正常数据库"""
        with patch.object(service, 'db_path', Path(temp_db)):
            result = service.analyze_database()
            assert result["status"] == "ok"

    def test_analyze_database_exception(self, service):
        """测试分析数据库异常处理"""
        with patch.object(service, 'db_path', MagicMock(exists=MagicMock(return_value=True))):
            with patch('sqlite3.connect', side_effect=Exception("DB Error")):
                result = service.analyze_database()
                assert result["status"] == "error"

    def test_get_database_info_no_db(self, service):
        """测试获取数据库信息 - 数据库不存在"""
        with patch.object(service, 'db_path', Path('/nonexistent/db.db')):
            result = service.get_database_info()
            assert result["status"] == "error"

    def test_get_database_info_with_db(self, service, temp_db):
        """测试获取数据库信息 - 正常数据库"""
        with patch.object(service, 'db_path', Path(temp_db)):
            result = service.get_database_info()
            assert result["status"] == "ok"
            assert "db_size" in result
            assert "table_count" in result
            assert "index_count" in result

    def test_get_database_info_exception(self, service):
        """测试获取数据库信息异常处理"""
        with patch.object(service, 'db_path', MagicMock(exists=MagicMock(return_value=True))):
            with patch('sqlite3.connect', side_effect=Exception("DB Error")):
                result = service.get_database_info()
                assert result["status"] == "error"

    def test_get_health_status(self, service):
        """测试获取健康状态"""
        result = service.get_health_status()
        assert "status" in result
        assert "stats" in result
        assert "monitoring" in result

    def test_get_stats(self, service):
        """测试获取统计信息"""
        result = service.get_stats()
        assert isinstance(result, dict)
        assert "integrity_errors" in result

    def test_start_stop_monitoring(self, service):
        """测试启动和停止监控"""
        import threading

        # Mock _monitor_loop 避免实际运行
        service._monitor_loop = MagicMock()

        # 启动监控
        service.start_monitoring()
        assert service.monitoring is True

        # 再次启动应该返回警告但不报错
        service.start_monitoring()

        # 停止监控
        service.stop_monitoring()
        assert service.monitoring is False

class TestGlobalInstance:
    """测试全局实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        from app.services.database_health_service import database_health_service
        assert database_health_service is not None

    def test_global_instance_is_service(self):
        """测试全局实例是服务类型"""
        from app.services.database_health_service import database_health_service, DatabaseHealthService
        assert isinstance(database_health_service, DatabaseHealthService)
