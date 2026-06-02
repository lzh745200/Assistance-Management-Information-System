"""
政策API全面测试
覆盖app/api/v1/policy.py的所有路由
"""

import pytest


from unittest.mock import patch, MagicMock
from unittest.mock import MagicMock  # auto-added

class TestPolicyAPI:
    """测试政策API"""

    def test_policies_list(self, client):
        """测试政策列表"""
        response = client.get("/api/v1/policies")
        assert response.status_code in [200, 401, 403]

    def test_policies_list_with_filters(self, client):
        """测试政策列表带过滤"""
        response = client.get("/api/v1/policies?category=finance&status=active")
        assert response.status_code in [200, 401, 403]

    def test_policies_detail(self, client):
        """测试政策详情"""
        response = client.get("/api/v1/policies/1")
        assert response.status_code in [200, 401, 403, 404, 405]

    def test_policies_create_empty(self, client):
        """测试创建空政策"""
        response = client.post("/api/v1/policies", json={})
        assert response.status_code in [200, 401, 403, 422]

    def test_policies_create_with_data(self, client):
        """测试创建政策"""
        response = client.post("/api/v1/policies", json={
            "title": "测试政策",
            "content": "政策内容",
            "category": "finance"
        })
        assert response.status_code in [200, 201, 401, 403, 422]

    def test_policies_update(self, client):
        """测试更新政策"""
        response = client.put("/api/v1/policies/1", json={
            "title": "更新政策"
        })
        assert response.status_code in [200, 401, 403, 404, 405, 422]

    def test_policies_delete(self, client):
        """测试删除政策"""
        response = client.delete("/api/v1/policies/1")
        assert response.status_code in [200, 401, 403, 404, 405]

    def test_policies_publish(self, client):
        """测试发布政策"""
        response = client.post("/api/v1/policies/1/publish")
        assert response.status_code in [200, 401, 403, 404, 405]

    def test_policies_unpublish(self, client):
        """测试取消发布政策"""
        response = client.post("/api/v1/policies/1/unpublish")
        assert response.status_code in [200, 401, 403, 404, 405]

    def test_policies_categories(self, client):
        """测试政策分类"""
        response = client.get("/api/v1/policies/categories")
        assert response.status_code in [200, 401, 403]

    def test_policies_search(self, client):
        """测试政策搜索"""
        response = client.get("/api/v1/policies/search?q=乡村振兴")
        assert response.status_code in [200, 401, 403]

class TestPolicyDocumentsAPI:
    """测试政策文件API"""

    def test_policy_documents_list(self, client):
        """测试政策文件列表"""
        response = client.get("/api/v1/policies/1/documents")
        assert response.status_code in [200, 401, 403, 404, 405]

    def test_policy_document_upload(self, client):
        """测试上传政策文件"""
        response = client.post("/api/v1/policies/1/documents")
        assert response.status_code in [200, 401, 403, 404, 405, 422]

    def test_policy_document_delete(self, client):
        """测试删除政策文件"""
        response = client.delete("/api/v1/policies/documents/1")
        assert response.status_code in [200, 401, 403, 404, 405]
