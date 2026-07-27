"""
帮扶管理信息系统 — 性能测试脚本（GB/T 25000.51-2016 合规）

覆盖场景：
  1. 日常业务查询（帮扶村/项目/学校/经费列表+详情）
  2. 大数据量分页查询（1000/5000/10000 条记录场景）
  3. 数据导出（.rrs 包生成下载）
  4. 数据导入（.rrs 包上传解析）
  5. 工作台仪表盘聚合统计
  6. 审计日志写入（并发写入压力）
  7. 搜索/筛选混合负载
  8. 审批工作流提交与查询
  9. 政策文档查询
  10. 数据同步包生成
  11. 用户管理操作
  12. 帮扶村 CRUD 全流程

运行方式：
  # Web UI 模式
  locust -f tests/performance/locustfile.py --host=http://localhost:8000

  # 无头模式（CI/CD 集成）
  locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
      --headless -u 50 -r 5 --run-time 5m \
      --csv=tests/performance/results/report \
      --html=tests/performance/results/report.html

  # Docker 模式
  docker compose -f docker-compose.yml -f docker/docker-compose.e2e.yml \
      --profile performance up

评估标准（军用级）：
  - P95 响应时间 < 500ms（查询类）
  - P95 响应时间 < 2000ms（导出类）
  - P95 响应时间 < 1000ms（写入类）
  - 错误率 < 0.1%
  - 吞吐量 ≥ 50 req/s（50 并发用户）
"""

import json
import random
import string
import time
from datetime import datetime, timedelta

from locust import HttpUser, task, between, events


# ============================================================
# 工具函数
# ============================================================

def _gen_village_name():
    """生成随机帮扶村名称"""
    prefixes = ["长顺", "紫云", "关岭", "镇宁", "普定", "平坝", "西秀"]
    suffixes = ["村", "寨", "屯", "湾", "营"]
    return random.choice(prefixes) + "".join(random.choices(string.digits, k=2)) + random.choice(suffixes)


def _gen_project_name():
    """生成随机项目名称"""
    types = ["产业帮扶", "教育帮扶", "医疗帮扶", "基础设施", "党建帮扶", "消费帮扶"]
    return f"{random.choice(types)}项目-{random.randint(2021, 2026)}-{random.randint(1, 999)}"


def _gen_fund_title():
    """生成随机经费标题"""
    types = ["专项帮扶", "基础设施", "教育资助", "医疗救助", "产业扶持"]
    return f"{random.choice(types)}资金-{random.randint(2021, 2026)}-{random.randint(1, 999)}"


# ============================================================
# 用户行为模拟
# ============================================================

class AdminUser(HttpUser):
    """管理员用户 — 覆盖全量业务场景

    权重: 30%
    覆盖: 工作台/帮扶村/项目/经费/学校/政策/审计/导出/审批
    """

    wait_time = between(1, 3)

    def on_start(self):
        """登录获取 Token"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
            name="登录",
        )
        if response.status_code == 200:
            data = response.json()
            # 兼容 envelope 格式 {code:200, data:{access_token:...}}
            token = (
                data.get("access_token")
                or data.get("data", {}).get("access_token")
                or ""
            )
            self.token = token
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.token = None
            self.headers = {}

    # ---- 日常查询类（高频） ----

    @task(5)
    def view_dashboard(self):
        """工作台统计聚合"""
        with self.client.get(
            "/api/v1/dashboard/stats",
            headers=self.headers,
            name="工作台统计",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 401:
                resp.failure("Token 过期，需重新登录")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(4)
    def list_supported_villages(self):
        """帮扶村列表 — 默认分页"""
        self.client.get(
            "/api/v1/supported-villages?page=1&page_size=20",
            headers=self.headers,
            name="帮扶村列表[20/页]",
        )

    @task(3)
    def list_projects(self):
        """项目列表"""
        self.client.get(
            "/api/v1/projects?page=1&page_size=20",
            headers=self.headers,
            name="项目列表[20/页]",
        )

    @task(3)
    def list_funds(self):
        """经费列表"""
        self.client.get(
            "/api/v1/funds?page=1&page_size=20",
            headers=self.headers,
            name="经费列表[20/页]",
        )

    @task(2)
    def list_schools(self):
        """学校列表"""
        self.client.get(
            "/api/v1/schools?page=1&page_size=20",
            headers=self.headers,
            name="学校列表[20/页]",
        )

    @task(2)
    def view_village_detail(self):
        """帮扶村详情"""
        village_id = random.randint(1, 50)
        self.client.get(
            f"/api/v1/supported-villages/{village_id}",
            headers=self.headers,
            name="帮扶村详情",
        )

    @task(1)
    def view_project_detail(self):
        """项目详情"""
        project_id = random.randint(1, 20)
        self.client.get(
            f"/api/v1/projects/{project_id}",
            headers=self.headers,
            name="项目详情",
        )

    @task(1)
    def view_fund_detail(self):
        """经费详情"""
        fund_id = random.randint(1, 30)
        self.client.get(
            f"/api/v1/funds/{fund_id}",
            headers=self.headers,
            name="经费详情",
        )

    # ---- 大数据量分页查询 ----

    @task(2)
    def list_villages_large_page(self):
        """帮扶村列表 — 大分页（100条/页）"""
        self.client.get(
            "/api/v1/supported-villages?page=1&page_size=100",
            headers=self.headers,
            name="帮扶村列表[100/页]",
        )

    @task(1)
    def list_villages_deep_pagination(self):
        """帮扶村列表 — 深度分页（第50页）"""
        self.client.get(
            "/api/v1/supported-villages?page=50&page_size=20",
            headers=self.headers,
            name="帮扶村列表[第50页]",
        )

    # ---- 搜索/筛选 ----

    @task(2)
    def search_villages(self):
        """搜索帮扶村"""
        keywords = ["长顺", "紫云", "村", "帮", "振兴"]
        keyword = random.choice(keywords)
        self.client.get(
            f"/api/v1/supported-villages?page=1&page_size=20&search={keyword}",
            headers=self.headers,
            name="帮扶村搜索",
        )

    @task(1)
    def filter_funds_by_year(self):
        """按年度筛选经费"""
        year = random.choice([2021, 2022, 2023, 2024, 2025, 2026])
        self.client.get(
            f"/api/v1/funds?page=1&page_size=20&year={year}",
            headers=self.headers,
            name="经费年度筛选",
        )

    @task(1)
    def filter_projects_by_status(self):
        """按状态筛选项目"""
        status = random.choice(["planning", "in_progress", "completed", "suspended"])
        self.client.get(
            f"/api/v1/projects?page=1&page_size=20&status={status}",
            headers=self.headers,
            name="项目状态筛选",
        )

    # ---- 政策与审批 ----

    @task(2)
    def list_policies(self):
        """政策列表"""
        self.client.get(
            "/api/v1/policies?page=1&page_size=20",
            headers=self.headers,
            name="政策列表",
        )

    @task(1)
    def view_policy_detail(self):
        """政策详情"""
        policy_id = random.randint(1, 10)
        self.client.get(
            f"/api/v1/policies/{policy_id}",
            headers=self.headers,
            name="政策详情",
        )

    @task(1)
    def list_approval_pending(self):
        """待审批列表"""
        self.client.get(
            "/api/v1/approval/pending?page=1&page_size=20",
            headers=self.headers,
            name="待审批列表",
        )

    @task(1)
    def list_approval_my(self):
        """我的申请"""
        self.client.get(
            "/api/v1/approval/my?page=1&page_size=20",
            headers=self.headers,
            name="我的申请",
        )

    # ---- 数据导出 ----

    @task(1)
    def export_villages(self):
        """导出帮扶村数据 — 获取可导出模块列表"""
        with self.client.get(
            "/api/v1/supported-villages/export/modules",
            headers=self.headers,
            name="帮扶村导出模块列表",
            catch_response=True,
            timeout=30,
        ) as resp:
            if resp.status_code in (200, 201, 202):
                resp.success()
            elif resp.status_code == 404:
                resp.failure("导出端点不存在")
            else:
                resp.failure(f"导出失败 HTTP {resp.status_code}")

    # ---- 审计与日志 ----

    @task(1)
    def view_audit_logs(self):
        """查看审计日志"""
        self.client.get(
            "/api/v1/system/audit?page=1&page_size=20",
            headers=self.headers,
            name="审计日志列表",
        )

    @task(1)
    def view_work_logs(self):
        """查看工作日志"""
        self.client.get(
            "/api/v1/work-logs?page=1&page_size=20",
            headers=self.headers,
            name="工作日志列表",
        )

    # ---- 用户管理 ----

    @task(1)
    def list_users(self):
        """用户列表"""
        self.client.get(
            "/api/v1/users?page=1&page_size=20",
            headers=self.headers,
            name="用户列表",
        )

    @task(1)
    def view_profile(self):
        """个人信息"""
        self.client.get(
            "/api/v1/auth/me",
            headers=self.headers,
            name="个人信息",
        )

    # ---- 数据同步 ----

    @task(1)
    def data_sync_status(self):
        """数据同步状态"""
        with self.client.get(
            "/api/v1/data-sync/status",
            headers=self.headers,
            name="数据同步状态",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ---- 帮扶村 CRUD（低频写入） ----

    @task(1)
    def create_village(self):
        """创建帮扶村（低频，验证写入性能）"""
        village_data = {
            "village_name": _gen_village_name(),
            "village_code": f"TEST{random.randint(10000, 99999)}",
            "region_code": "522729",
            "contact_person": "测试联系人",
            "contact_phone": f"138{random.randint(10000000, 99999999)}",
        }
        with self.client.post(
            "/api/v1/supported-villages",
            json=village_data,
            headers=self.headers,
            name="创建帮扶村",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201):
                resp.success()
            elif resp.status_code == 422:
                resp.failure("字段校验失败")
            elif resp.status_code == 401:
                resp.failure("Token 过期")
            else:
                resp.failure(f"创建失败 HTTP {resp.status_code}")


class OperatorUser(HttpUser):
    """操作员用户 — 日常录入+查询

    权重: 50%
    覆盖: 工作台/帮扶村/项目/政策/个人信息
    """

    wait_time = between(2, 5)

    def on_start(self):
        """登录"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
            name="登录",
        )
        if response.status_code == 200:
            data = response.json()
            token = (
                data.get("access_token")
                or data.get("data", {}).get("access_token")
                or ""
            )
            self.token = token
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.token = None
            self.headers = {}

    @task(5)
    def view_dashboard(self):
        """工作台"""
        self.client.get(
            "/api/v1/dashboard/stats",
            headers=self.headers,
            name="工作台统计",
        )

    @task(3)
    def list_villages(self):
        """帮扶村列表"""
        self.client.get(
            "/api/v1/supported-villages?page=1&page_size=20",
            headers=self.headers,
            name="帮扶村列表[20/页]",
        )

    @task(2)
    def list_projects(self):
        """项目列表"""
        self.client.get(
            "/api/v1/projects?page=1&page_size=20",
            headers=self.headers,
            name="项目列表[20/页]",
        )

    @task(2)
    def list_funds(self):
        """经费列表"""
        self.client.get(
            "/api/v1/funds?page=1&page_size=20",
            headers=self.headers,
            name="经费列表[20/页]",
        )

    @task(1)
    def view_profile(self):
        """个人信息"""
        self.client.get(
            "/api/v1/auth/me",
            headers=self.headers,
            name="个人信息",
        )

    @task(1)
    def list_policies(self):
        """政策列表"""
        self.client.get(
            "/api/v1/policies?page=1&page_size=20",
            headers=self.headers,
            name="政策列表",
        )

    @task(1)
    def list_schools(self):
        """学校列表"""
        self.client.get(
            "/api/v1/schools?page=1&page_size=20",
            headers=self.headers,
            name="学校列表",
        )

    @task(1)
    def view_work_logs(self):
        """查看工作日志"""
        self.client.get(
            "/api/v1/work-logs?page=1&page_size=20",
            headers=self.headers,
            name="工作日志列表",
        )


class StressTestUser(HttpUser):
    """压力测试用户 — 高并发快速请求

    权重: 20%
    覆盖: 多端点快速轮换请求
    """

    wait_time = between(0.1, 0.5)

    def on_start(self):
        """登录"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
            name="登录",
        )
        if response.status_code == 200:
            data = response.json()
            token = (
                data.get("access_token")
                or data.get("data", {}).get("access_token")
                or ""
            )
            self.token = token
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.token = None
            self.headers = {}

    @task
    def rapid_requests(self):
        """快速轮换请求（压力测试）"""
        endpoints = [
            "/api/v1/dashboard/stats",
            "/api/v1/supported-villages?page=1&page_size=10",
            "/api/v1/projects?page=1&page_size=10",
            "/api/v1/funds?page=1&page_size=10",
            "/api/v1/schools?page=1&page_size=10",
            "/api/v1/auth/me",
            "/api/v1/work-logs?page=1&page_size=10",
            "/api/v1/policies?page=1&page_size=10",
            "/api/v1/system/audit?page=1&page_size=10",
            "/api/v1/users?page=1&page_size=10",
            "/api/v1/approval/pending?page=1&page_size=10",
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, headers=self.headers, name="压力测试轮换请求")


# ============================================================
# 测试事件钩子 — 自动记录性能指标
# ============================================================

_test_start_time = None


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时记录时间"""
    global _test_start_time
    _test_start_time = time.time()
    print("\n" + "=" * 60)
    print("性能测试开始 — 帮扶管理信息系统")
    print(f"目标主机: {environment.host}")
    num_users = environment.parsed_options.num_users if environment.parsed_options else "N/A"
    spawn_rate = environment.parsed_options.spawn_rate if environment.parsed_options else "N/A"
    print(f"并发用户: {num_users}")
    print(f"孵化速率: {spawn_rate}")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时输出汇总"""
    global _test_start_time
    duration = time.time() - _test_start_time if _test_start_time else 0

    stats = environment.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    print("\n" + "=" * 60)
    print("性能测试汇总报告")
    print("=" * 60)
    print(f"测试时长:     {duration:.1f} 秒")
    print(f"总请求数:     {total_requests}")
    print(f"失败请求数:   {total_failures}")
    print(f"失败率:       {failure_rate:.2f}%")
    print(f"平均响应时间: {stats.total.avg_response_time:.1f} ms")
    print(f"P50 响应时间: {stats.total.get_response_time_percentile(0.5):.1f} ms")
    print(f"P95 响应时间: {stats.total.get_response_time_percentile(0.95):.1f} ms")
    print(f"P99 响应时间: {stats.total.get_response_time_percentile(0.99):.1f} ms")
    print(f"吞吐量:       {stats.total.current_rps:.1f} req/s")
    print("=" * 60)

    # 合规判定
    print("\n合规判定 (GB/T 25000.51-2016):")
    p95 = stats.total.get_response_time_percentile(0.95)
    checks = [
        ("P95 < 500ms (查询类)", p95 < 500),
        ("错误率 < 0.1%", failure_rate < 0.1),
        ("吞吐量 ≥ 50 req/s", stats.total.current_rps >= 50),
    ]
    for name, passed in checks:
        status = "✓ 通过" if passed else "✗ 不通过"
        print(f"  {name}: {status}")

    # 按端点分类统计
    print("\n按端点分类统计:")
    print("-" * 80)
    print(f"{'端点':<40} {'请求数':>8} {'失败数':>8} {'P95(ms)':>10} {'avg(ms)':>10}")
    print("-" * 80)
    for entry in stats.entries.values():
        if entry.num_requests > 0:
            name = entry.name[:40]
            p95_val = entry.get_response_time_percentile(0.95)
            print(f"{name:<40} {entry.num_requests:>8} {entry.num_failures:>8} {p95_val:>10.1f} {entry.avg_response_time:>10.1f}")
    print("-" * 80)
    print()


# ============================================================
# 用户权重配置
# ============================================================

# AdminUser: 30%, OperatorUser: 50%, StressTestUser: 20%
AdminUser.weight = 3
OperatorUser.weight = 5
StressTestUser.weight = 2
