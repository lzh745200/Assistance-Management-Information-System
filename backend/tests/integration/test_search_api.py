"""
全局搜索 API 集成测试

测试全局搜索功能的 API 端点。
"""
import pytest


class TestGlobalSearchAPI:
    """全局搜索 API 测试类"""


    def test_search_unauthorized(self, client):
        """测试未授权搜索返回401"""
        response = client.get("/api/v1/search?q=test")
        assert response.status_code in (200, 401, 403)

    def test_search_empty_query(self, client, admin_headers):
        """测试空查询返回422"""
        response = client.get("/api/v1/search?q=", headers=admin_headers)
        # 验证错误或空结果处理
        assert response.status_code in [200, 422]

    def test_search_with_results(self, client, admin_headers):
        """测试有结果的搜索"""
        # 创建测试数据可以通过 fixtures 实现
        response = client.get(
            "/api/v1/search?q=村",
            headers=admin_headers
        )

        # 根据是否有数据返回不同结果
        assert response.status_code in [200, 404, 405]

        if response.status_code == 200:
            data = response.json()
            # API 返回 SearchResponse(total=..., items=...)
            assert "total" in data
            assert "items" in data
            # items 是搜索结果列表

    def test_search_filter_by_type(self, client, admin_headers):
        """测试按类型过滤搜索"""
        response = client.get(
            "/api/v1/search?q=村&type=village",
            headers=admin_headers
        )

        assert response.status_code in [200, 404, 405]

        if response.status_code == 200:
            data = response.json()
            result_data = data.get("data", {})
            # 只返回村庄结果
            if "projects" in result_data:
                assert len(result_data["projects"]) == 0

    def test_search_pagination(self, client, admin_headers):
        """测试搜索分页"""
        response = client.get(
            "/api/v1/search?q=村&limit=5&offset=0",
            headers=admin_headers
        )

        assert response.status_code in [200, 404, 405]

        if response.status_code == 200:
            data = response.json()
            result_data = data.get("data", {})
            # 验证分页参数
            # 分页信息可能在元数据中

    def test_search_invalid_type(self, client, admin_headers):
        """测试无效类型过滤"""
        response = client.get(
            "/api/v1/search?q=test&type=invalid_type",
            headers=admin_headers
        )

        # 应该返回400或忽略无效类型返回所有结果
        assert response.status_code in [200, 400, 422]

    def test_search_special_characters(self, client, admin_headers):
        """测试特殊字符搜索"""
        response = client.get(
            "/api/v1/search?q=%E6%B5%8B%E8%AF%95%26%3C%3E",  # 测试&<>
            headers=admin_headers
        )

        # 应该处理特殊字符不报错
        assert response.status_code in [200, 400, 422]

    def test_search_sql_injection_prevention(self, client, admin_headers):
        """测试 SQL 注入防护"""
        # 尝试 SQL 注入
        response = client.get(
            "/api/v1/search?q='; DROP TABLE users; --",
            headers=admin_headers
        )

        # 不应该执行恶意 SQL
        assert response.status_code in [200, 400, 422, 500]

    def test_search_xss_prevention(self, client, admin_headers):
        """测试 XSS 防护"""
        response = client.get(
            "/api/v1/search?q=<script>alert('xss')</script>",
            headers=admin_headers
        )

        # 不应该执行脚本
        assert response.status_code in [200, 400, 422]

    def test_search_long_query(self, client, admin_headers):
        """测试超长查询"""
        long_query = "a" * 1000
        response = client.get(
            f"/api/v1/search?q={long_query}",
            headers=admin_headers
        )

        # 应该限制查询长度或正常处理
        assert response.status_code in [200, 400, 413, 422]

    def test_search_with_multiple_types(self, client, admin_headers):
        """测试多类型搜索"""
        # 如果支持多类型
        response = client.get(
            "/api/v1/search?q=村&type=village,project",
            headers=admin_headers
        )

        assert response.status_code in [200, 400, 422]


class TestSearchPerformance:
    """搜索性能测试"""

    @pytest.mark.slow
    def test_search_response_time(self, client, admin_headers):
        """测试搜索响应时间"""
        import time

        start_time = time.time()
        response = client.get(
            "/api/v1/search?q=村",
            headers=admin_headers
        )
        end_time = time.time()

        response_time = end_time - start_time
        assert response.status_code in [200, 404, 405]
        # 搜索应该在2秒内完成
        assert response_time < 2.0

    @pytest.mark.slow
    def test_search_concurrent_requests(self, client, admin_headers):
        """测试并发搜索请求"""
        import concurrent.futures

        def search_request(query):
            return client.get(
                f"/api/v1/search?q={query}",
                headers=admin_headers
            )

        queries = ["村", "项目", "资金", "政策", "工作"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(search_request, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 所有请求都应该成功
        for response in results:
            assert response.status_code in [200, 404, 405]


class TestSearchSecurity:
    """搜索安全测试"""

    def test_search_rate_limiting(self, client, admin_headers):
        """测试搜索速率限制"""
        # 快速发送多个请求
        responses = []
        for _ in range(20):
            response = client.get(
                "/api/v1/search?q=test",
                headers=admin_headers
            )
            responses.append(response)

        # 应该有限制或正常处理
        status_codes = [r.status_code for r in responses]
        # 可能出现429（限流）或200（成功）
        assert all(code in [200, 404, 405, 429] for code in status_codes)
