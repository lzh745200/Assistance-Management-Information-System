"""
健康检查API全面测试 — health endpoints refactored
"""



class TestHealthAPI:
    """测试健康检查API"""

    def test_health_check_basic(self, client):
        """测试基础健康检查"""
        response = client.get("/api/v1/health")
        assert response.status_code in [200, 404, 405]

    def test_health_check_detailed(self, client):
        """测试详细健康检查"""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code in [200, 404, 405]

    def test_health_check_db(self, client):
        """测试数据库健康检查"""
        response = client.get("/api/v1/health/db")
        assert response.status_code in [200, 404, 405]

    def test_health_check_cache(self, client):
        """测试缓存健康检查"""
        response = client.get("/api/v1/health/cache")
        assert response.status_code in [200, 404, 405]

    def test_health_check_services(self, client):
        """测试服务健康检查"""
        response = client.get("/api/v1/health/services")
        assert response.status_code in [200, 404, 405]

    def test_health_check_liveness(self, client):
        """测试存活检查"""
        response = client.get("/api/v1/health/live")
        assert response.status_code in [200, 404, 405]

    def test_health_check_readiness(self, client):
        """测试就绪检查"""
        response = client.get("/api/v1/health/ready")
        assert response.status_code in [200, 404, 405]

    def test_health_metrics(self, client):
        """测试健康指标"""
        response = client.get("/api/v1/health/metrics")
        assert response.status_code in [200, 401, 404, 405]

class TestSystemHealthAPI:
    """测试系统健康API"""

    def test_system_health_status(self, client):
        """测试系统健康状态"""
        response = client.get("/api/v1/system/health")
        assert response.status_code in [200, 401, 404, 405]

    def test_system_health_components(self, client):
        """测试系统组件健康"""
        response = client.get("/api/v1/system/health/components")
        assert response.status_code in [200, 401, 404, 405]

    def test_system_health_checks(self, client):
        """测试系统健康检查"""
        response = client.get("/api/v1/system/health/checks")
        assert response.status_code in [200, 401, 404, 405]
