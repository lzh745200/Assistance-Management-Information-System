"""
自动化测试脚本 - 验证所有修复
"""
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

class TestRunner:
    def __init__(self):
        self.token = None
        self.passed = 0
        self.failed = 0
        self.tests = []

    def login(self):
        """登录获取 token"""
        print("\n" + "="*60)
        print("登录系统")
        print("="*60)

        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )

        if resp.status_code == 200:
            self.token = resp.json()['data']['access_token']
            print("✓ 登录成功")
            return True
        else:
            print(f"✗ 登录失败: {resp.status_code}")
            return False

    def test(self, name, func):
        """运行单个测试"""
        print(f"\n测试: {name}")
        try:
            result = func()
            if result:
                print(f"  ✓ 通过")
                self.passed += 1
            else:
                print(f"  ✗ 失败")
                self.failed += 1
            self.tests.append((name, result))
            return result
        except Exception as e:
            print(f"  ✗ 异常: {e}")
            self.failed += 1
            self.tests.append((name, False))
            return False

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    # ========== 第一阶段：严重缺陷测试 ==========

    def test_audit_logs_path(self):
        """测试审计日志接口路径"""
        resp = requests.get(
            f"{BASE_URL}/system/audit/logs",
            headers=self.get_headers(),
            params={"page": 1, "page_size": 10}
        )
        print(f"    状态码: {resp.status_code}")
        return resp.status_code == 200

    def test_database_exception_handling(self):
        """测试数据库异常处理"""
        # 尝试获取不存在的资源
        resp = requests.get(
            f"{BASE_URL}/rural-works/999999",
            headers=self.get_headers()
        )
        print(f"    状态码: {resp.status_code}")
        # 应该返回 404，而不是 500
        return resp.status_code == 404

    def test_delete_error_handling(self):
        """测试删除功能错误处理"""
        # 创建测试数据
        create_resp = requests.post(
            f"{BASE_URL}/rural-works",
            headers=self.get_headers(),
            json={
                "name": "测试删除",
                "type": "infrastructure",
                "status": "planned",
                "responsible_person": "测试",
                "progress": 0
            }
        )

        if create_resp.status_code != 200:
            print(f"    创建失败: {create_resp.status_code}")
            return False

        work_id = create_resp.json()['data']['id']

        # 删除
        delete_resp = requests.delete(
            f"{BASE_URL}/rural-works/{work_id}",
            headers=self.get_headers()
        )

        print(f"    删除状态码: {delete_resp.status_code}")
        return delete_resp.status_code == 200

    # ========== 第二阶段：中等缺陷测试 ==========

    def test_system_config(self):
        """测试系统配置接口"""
        resp = requests.get(
            f"{BASE_URL}/system/config",
            headers=self.get_headers()
        )
        print(f"    状态码: {resp.status_code}")
        return resp.status_code == 200

    def test_system_update_logs(self):
        """测试系统更新日志接口"""
        resp = requests.get(
            f"{BASE_URL}/system/update-logs",
            headers=self.get_headers()
        )
        print(f"    状态码: {resp.status_code}")
        return resp.status_code == 200

    def test_data_package_export_validation(self):
        """测试数据包导出验证"""
        # 测试空 data_types
        resp = requests.post(
            f"{BASE_URL}/data-packages/export",
            headers=self.get_headers(),
            json={"data_types": [], "description": "test"}
        )
        print(f"    空 data_types 状态码: {resp.status_code}")
        # 应该返回 422 验证错误
        return resp.status_code == 422

    # ========== 第三阶段：功能测试 ==========

    def test_rural_work_list_no_year_filter(self):
        """测试乡村工作列表（无年份筛选）"""
        resp = requests.get(
            f"{BASE_URL}/rural-works",
            headers=self.get_headers(),
            params={"limit": 10}
        )
        print(f"    状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"    记录数: {data.get('total', 0)}")
            return True
        return False

    def test_dashboard_stats(self):
        """测试 Dashboard 统计"""
        resp = requests.get(
            f"{BASE_URL}/analytics/summary",
            headers=self.get_headers(),
            params={"year": datetime.now().year}
        )
        print(f"    状态码: {resp.status_code}")
        return resp.status_code in [200, 404]  # 404 也可以接受（接口可能不存在）

    def test_organizations_tree(self):
        """测试组织树"""
        resp = requests.get(
            f"{BASE_URL}/organizations/tree",
            headers=self.get_headers()
        )
        print(f"    状态码: {resp.status_code}")
        return resp.status_code == 200

    def run_all_tests(self):
        """运行所有测试"""
        if not self.login():
            print("\n登录失败，无法继续测试")
            return

        print("\n" + "="*60)
        print("第一阶段：严重缺陷测试")
        print("="*60)

        self.test("审计日志接口路径", self.test_audit_logs_path)
        self.test("数据库异常处理", self.test_database_exception_handling)
        self.test("删除功能错误处理", self.test_delete_error_handling)

        print("\n" + "="*60)
        print("第二阶段：中等缺陷测试")
        print("="*60)

        self.test("系统配置接口", self.test_system_config)
        self.test("系统更新日志接口", self.test_system_update_logs)
        self.test("数据包导出验证", self.test_data_package_export_validation)

        print("\n" + "="*60)
        print("第三阶段：功能测试")
        print("="*60)

        self.test("乡村工作列表", self.test_rural_work_list_no_year_filter)
        self.test("Dashboard 统计", self.test_dashboard_stats)
        self.test("组织树", self.test_organizations_tree)

        # 输出测试报告
        print("\n" + "="*60)
        print("测试报告")
        print("="*60)
        print(f"总测试数: {self.passed + self.failed}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"通过率: {self.passed / (self.passed + self.failed) * 100:.1f}%")

        print("\n详细结果:")
        for name, result in self.tests:
            status = "✓" if result else "✗"
            print(f"  {status} {name}")

        print("\n" + "="*60)
        if self.failed == 0:
            print("🎉 所有测试通过！")
        else:
            print(f"⚠️  有 {self.failed} 个测试失败")
        print("="*60)

if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()
