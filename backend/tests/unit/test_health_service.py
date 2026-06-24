"""
系统健康检查服务单元测试
覆盖: app/services/health_service.py
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def health_service():
    from app.services.health_service import HealthService
    return HealthService()


class TestHealthServiceInit:
    def test_init_without_db(self):
        from app.services.health_service import HealthService
        svc = HealthService()
        assert svc.db is None

    def test_init_with_db(self):
        from app.services.health_service import HealthService
        mock_db = MagicMock()
        svc = HealthService(db=mock_db)
        assert svc.db is mock_db


class TestCheckDatabase:
    def test_check_database_calls_service(self, health_service):
        # 修复后 check_database 调用 get_health_status() + check_integrity() + quick_check()
        # （原 check() 方法不存在，旧测试用 mock 掩盖了 AttributeError）
        with patch("app.services.database_health_service.DatabaseHealthService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.get_health_status.return_value = {"status": "healthy", "size_mb": 50}
            mock_svc.check_integrity.return_value = {}
            mock_svc.quick_check.return_value = {}
            mock_svc_cls.return_value = mock_svc

            result = health_service.check_database()
            assert result["status"] == "healthy"
            assert result["size_mb"] == 50
            # DatabaseHealthService.__init__ 不收参数（从 settings 读取路径）
            mock_svc_cls.assert_called_once_with()
            mock_svc.get_health_status.assert_called_once()
            mock_svc.check_integrity.assert_called_once()
            mock_svc.quick_check.assert_called_once()

    def test_check_database_with_db(self):
        # DatabaseHealthService 自管路径，不接受 db 参数；HealthService.db 仅用于
        # 其它子检查，不再透传给 DatabaseHealthService（原透传会 TypeError）
        from app.services.health_service import HealthService
        mock_db = MagicMock()
        svc = HealthService(db=mock_db)

        with patch("app.services.database_health_service.DatabaseHealthService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.get_health_status.return_value = {"status": "healthy"}
            mock_svc.check_integrity.return_value = {}
            mock_svc.quick_check.return_value = {}
            mock_svc_cls.return_value = mock_svc

            svc.check_database()
            mock_svc_cls.assert_called_once_with()

    def test_check_database_handles_check_exception(self, health_service):
        # check_integrity 抛错时不应让 check_database 崩，应把异常转为 issues
        with patch("app.services.database_health_service.DatabaseHealthService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.get_health_status.return_value = {"status": "unknown", "issues": []}
            mock_svc.check_integrity.side_effect = RuntimeError("boom")
            mock_svc.quick_check.return_value = {}
            mock_svc_cls.return_value = mock_svc

            result = health_service.check_database()
            assert "boom" in result.get("issues", [])


class TestCheckFunds:
    def test_check_funds_calls_service(self, health_service):
        with patch("app.services.fund_health_service.FundHealthService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.check_funds.return_value = {"status": "healthy", "anomalies": 0}
            mock_svc_cls.return_value = mock_svc

            result = health_service.check_funds()
            assert result["status"] == "healthy"
            assert result["anomalies"] == 0


class TestCheckAll:
    def test_check_all_aggregates(self, health_service):
        with patch.object(health_service, "check_database",
                          return_value={"status": "healthy"}), \
             patch.object(health_service, "check_funds",
                          return_value={"status": "healthy"}):
            result = health_service.check_all()
            assert result["database"]["status"] == "healthy"
            assert result["funds"]["status"] == "healthy"
            assert result["status"] == "healthy"

    def test_check_all_with_degraded_database(self, health_service):
        with patch.object(health_service, "check_database",
                          return_value={"status": "degraded", "error": "disk full"}), \
             patch.object(health_service, "check_funds",
                          return_value={"status": "healthy"}):
            result = health_service.check_all()
            assert result["database"]["status"] == "degraded"
            assert result["status"] == "healthy"  # overall status stays healthy


class TestCheckFilesystem:
    def test_check_filesystem_backward_compat(self, health_service):
        result = health_service.check_filesystem()
        assert result["status"] == "healthy"
        assert "uploads_dir" in result
        assert "db_dir" in result

    def test_check_filesystem_attached_to_class(self, health_service):
        from app.services.health_service import HealthService
        # Verify it's attached as a bound method
        assert hasattr(HealthService, "check_filesystem")
        assert callable(health_service.check_filesystem)
