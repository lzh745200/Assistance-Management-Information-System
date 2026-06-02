"""
Services层最终冲刺测试
覆盖 secrets_manager, database_health_service, data_tier_service 剩余行
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from pathlib import Path

class TestSecretsManagerFinalPush:
    """最终冲刺 secrets_manager 100%"""

    def test_cleanup_expired_keys(self):
        """测试 cleanup_expired_keys"""
        from app.services.secrets_manager import SecretsManager

        manager = SecretsManager()
        # 添加一些测试密钥
        manager._secrets["old_key"] = "old_value"
        manager._key_versions = [
            {"version_id": "old_key", "created_at": time.time() - 86400 * 100, "is_active": False}
        ]

        count = manager.cleanup_expired_keys(keep_days=30)
        # 验证清理逻辑
        assert isinstance(count, int)

    def test_revoke_key(self):
        """测试 revoke_key"""
        from app.services.secrets_manager import SecretsManager

        manager = SecretsManager()
        # 先创建一个密钥
        version_id = manager.rotate_key()

        result = manager.revoke_key(version_id)
        assert result is True

    def test_create_key(self):
        """测试 create_key"""
        from app.services.secrets_manager import SecretsManager

        manager = SecretsManager()
        key_id = manager.create_key(key_type="fernet", expires_days=30)
        assert key_id is not None

class TestDataTierServiceFinalPush:
    """最终冲刺 data_tier_service"""

    def test_get_storage_summary(self):
        """测试 get_storage_summary"""
        from app.services.data_tier_service import DataTierService

        service = DataTierService()

        # 创建临时目录结构
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'stat', return_value=MagicMock(st_size=1024)):
                with patch.object(Path, 'glob', return_value=[]):
                    result = service.get_storage_summary()

        assert "generated_at" in result
        assert "tiers" in result
        assert "storage_sizes" in result

    def test_cleanup_old_archives(self):
        """测试 cleanup_old_archives"""
        from app.services.data_tier_service import DataTierService

        service = DataTierService()

        # 模拟冷存储路径
        mock_file = MagicMock()
        mock_file.stat.return_value = MagicMock(st_mtime=time.time() - 86400 * 400)
        mock_file.unlink = MagicMock()

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'glob', return_value=[mock_file]):
                count, msg = service.cleanup_old_archives(max_age_days=365)

        assert isinstance(count, int)
        assert isinstance(msg, str)

    def test_restore_from_archive(self):
        """测试 restore_from_archive"""
        from app.services.data_tier_service import DataTierService

        service = DataTierService()
        mock_db = MagicMock()

        # 模拟归档目录不存在
        with patch.object(Path, 'exists', return_value=False):
            count, msg = service.restore_from_archive(mock_db, "test_model", "warm")

        assert count == 0

class TestDatabaseHealthServiceFinalPush:
    """最终冲刺 database_health_service"""

    def test_get_database_info(self):
        """测试 get_database_info"""
        from app.services.database_health_service import DatabaseHealthService

        service = DatabaseHealthService()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("table1", "sqlite_master", 0),
        ]
        mock_cursor.fetchone.side_effect = [["ok"], [100]]

        with patch('sqlite3.connect', return_value=mock_conn):
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'stat', return_value=MagicMock(st_size=1024)):
                    result = service.get_database_info()

        assert "tables" in result or "status" in result

    def test_get_health_status(self):
        """测试 get_health_status"""
        from app.services.database_health_service import DatabaseHealthService

        service = DatabaseHealthService()

        # 设置一些健康状态
        service.health_status = {"status": "healthy"}
        service.stats = {"check_count": 10}

        result = service.get_health_status()

        assert "status" in result
        assert "stats" in result

    def test_get_stats(self):
        """测试 get_stats"""
        from app.services.database_health_service import DatabaseHealthService

        service = DatabaseHealthService()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("table1", 100, 1000),
        ]

        with patch('sqlite3.connect', return_value=mock_conn):
            with patch.object(Path, 'exists', return_value=True):
                result = service.get_stats()

        assert isinstance(result, dict)
