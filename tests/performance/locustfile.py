"""
性能和压力测试脚本

使用 locust 进行性能测试和压力测试

安装依赖：
pip install locust

运行测试：
locust -f tests/performance/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random
import json


class AdminUser(HttpUser):
    """管理员用户行为模拟"""

    wait_time = between(1, 3)  # 用户操作间隔 1-3 秒

    def on_start(self):
        """用户启动时执行：登录"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(3)
    def view_dashboard(self):
        """查看工作台（高频操作）"""
        self.client.get("/api/v1/dashboard/stats", headers=self.headers)

    @task(2)
    def list_villages(self):
        """查看帮扶村列表"""
        self.client.get("/api/v1/villages?skip=0&limit=20", headers=self.headers)

    @task(2)
    def list_projects(self):
        """查看项目列表"""
        self.client.get("/api/v1/projects?skip=0&limit=20", headers=self.headers)

    @task(1)
    def view_village_detail(self):
        """查看帮扶村详情"""
        village_id = random.randint(1, 10)
        self.client.get(f"/api/v1/villages/{village_id}", headers=self.headers)

    @task(1)
    def view_project_detail(self):
        """查看项目详情"""
        project_id = random.randint(1, 10)
        self.client.get(f"/api/v1/projects/{project_id}", headers=self.headers)

    @task(1)
    def search_villages(self):
        """搜索帮扶村"""
        keywords = ["测试", "示例", "村", "乡"]
        keyword = random.choice(keywords)
        self.client.get(f"/api/v1/villages?search={keyword}", headers=self.headers)


class NormalUser(HttpUser):
    """普通用户行为模拟"""

    wait_time = between(2, 5)  # 用户操作间隔 2-5 秒

    def on_start(self):
        """用户启动时执行：登录"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "user",
            "password": "user123456"
        })

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(5)
    def view_dashboard(self):
        """查看工作台"""
        self.client.get("/api/v1/dashboard/stats", headers=self.headers)

    @task(3)
    def list_villages(self):
        """查看帮扶村列表"""
        self.client.get("/api/v1/villages?skip=0&limit=20", headers=self.headers)

    @task(2)
    def list_projects(self):
        """查看项目列表"""
        self.client.get("/api/v1/projects?skip=0&limit=20", headers=self.headers)

    @task(1)
    def view_profile(self):
        """查看个人信息"""
        self.client.get("/api/v1/auth/me", headers=self.headers)


class StressTestUser(HttpUser):
    """压力测试用户（高并发场景）"""

    wait_time = between(0.1, 0.5)  # 快速操作，模拟高并发

    def on_start(self):
        """用户启动时执行：登录"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task
    def rapid_requests(self):
        """快速请求（压力测试）"""
        endpoints = [
            "/api/v1/dashboard/stats",
            "/api/v1/villages?skip=0&limit=10",
            "/api/v1/projects?skip=0&limit=10",
            "/api/v1/auth/me",
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, headers=self.headers)


# 性能测试场景配置
class PerformanceTest(HttpUser):
    """性能测试场景"""

    tasks = [AdminUser, NormalUser]
    wait_time = between(1, 3)

    # 用户权重：70% 普通用户，30% 管理员
    weight = 7  # NormalUser
    # weight = 3  # AdminUser


# 压力测试场景配置
class StressTest(HttpUser):
    """压力测试场景"""

    tasks = [StressTestUser]
    wait_time = between(0.1, 0.5)
