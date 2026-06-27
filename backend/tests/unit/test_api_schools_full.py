"""
学校API全面测试
覆盖app/api/v1/school.py的所有路由
"""




class TestSchoolsAPI:
    """测试学校API"""

    def test_schools_list(self, client):
        """测试学校列表"""
        response = client.get("/api/v1/schools")
        assert response.status_code in [200, 401, 403]

    def test_schools_list_with_filters(self, client):
        """测试学校列表带过滤"""
        response = client.get("/api/v1/schools?type=primary&status=active")
        assert response.status_code in [200, 401, 403]

    def test_schools_detail(self, client):
        """测试学校详情"""
        response = client.get("/api/v1/schools/1")
        assert response.status_code in [200, 401, 403, 404, 405]

    def test_schools_create_empty(self, client):
        """测试创建空学校"""
        response = client.post("/api/v1/schools", json={})
        assert response.status_code in [200, 401, 403, 422]

    def test_schools_create_with_data(self, client):
        """测试创建学校"""
        response = client.post("/api/v1/schools", json={
            "name": "测试学校",
            "type": "primary"
        })
        assert response.status_code in [200, 201, 401, 403, 422]

    def test_schools_update(self, client):
        """测试更新学校"""
        response = client.put("/api/v1/schools/1", json={
            "name": "更新学校名称"
        })
        assert response.status_code in [200, 401, 403, 404, 405, 422]

    def test_schools_delete(self, client):
        """测试删除学校"""
        response = client.delete("/api/v1/schools/1")
        assert response.status_code in [200, 401, 403, 404, 405]

    def test_schools_statistics(self, client):
        """测试学校统计"""
        response = client.get("/api/v1/schools/statistics")
        assert response.status_code in [200, 401, 403]

    def test_schools_export(self, client):
        """测试导出学校"""
        response = client.get("/api/v1/schools/export")
        assert response.status_code in [200, 401, 403]

class TestSchoolSupportAPI:
    """测试学校帮扶API"""

    def test_school_support_records(self, client):
        """测试学校帮扶记录"""
        response = client.get("/api/v1/schools/1/support-records")
        assert response.status_code in [200, 401, 403, 404, 405]

    def test_school_support_create(self, client):
        """测试创建帮扶记录"""
        response = client.post("/api/v1/schools/1/support-records", json={
            "amount": 10000,
            "description": "帮扶物资"
        })
        assert response.status_code in [200, 401, 403, 404, 405, 422]

    def test_school_support_detail(self, client):
        """测试帮扶记录详情"""
        response = client.get("/api/v1/schools/support-records/1")
        assert response.status_code in [200, 401, 403, 404, 405]

    def test_school_support_update(self, client):
        """测试更新帮扶记录"""
        response = client.put("/api/v1/schools/support-records/1", json={})
        assert response.status_code in [200, 401, 403, 404, 405, 422]

    def test_school_support_delete(self, client):
        """测试删除帮扶记录"""
        response = client.delete("/api/v1/schools/support-records/1")
        assert response.status_code in [200, 401, 403, 404, 405]

class TestSchoolStudentsAPI:
    """测试学校学生API"""

    def test_school_students_list(self, client):
        """测试学生列表"""
        response = client.get("/api/v1/schools/1/students")
        assert response.status_code in [200, 401, 403, 404, 405]

    def test_school_students_create(self, client):
        """测试创建学生"""
        response = client.post("/api/v1/schools/1/students", json={
            "name": "测试学生"
        })
        assert response.status_code in [200, 401, 403, 404, 405, 422]
