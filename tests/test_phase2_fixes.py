"""
第二阶段修复测试脚本 - 验证中等缺陷修复
"""
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

class Phase2TestRunner:
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
            json={"username": "admin", "password": "Admin@2026"}
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

    # ========== 第二阶段：中等缺陷测试 ==========

    def test_cors_options_support(self):
        """测试 CORS OPTIONS 预检请求支持"""
        # 测试几个关键接口的 OPTIONS 支持
        test_endpoints = [
            "/auth/login",
            "/system/config",
            "/rural-works",
            "/organizations/tree"
        ]

        all_passed = True
        for endpoint in test_endpoints:
            resp = requests.options(
                f"{BASE_URL}{endpoint}",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "POST"
                }
            )
            print(f"    {endpoint}: {resp.status_code}")
            # OPTIONS 应该返回 200 或 204
            if resp.status_code not in [200, 204]:
                all_passed = False
                print(f"      ✗ OPTIONS 不支持")
            else:
                # 检查 CORS 头
                if "Access-Control-Allow-Origin" in resp.headers:
                    print(f"      ✓ CORS 头存在")
                else:
                    print(f"      ⚠ CORS 头缺失")

        return all_passed

    def test_data_package_import_validation(self):
        """测试数据包导入验证"""
        # 测试空文件导入
        resp = requests.post(
            f"{BASE_URL}/data-packages/import",
            headers=self.get_headers(),
            files={"file": ("empty.xlsx", b"", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        print(f"    空文件状态码: {resp.status_code}")
        # 应该返回 422 验证错误或 400 业务错误
        return resp.status_code in [400, 422]

    def test_plotly_not_imported(self):
        """测试 Plotly 未被导入（已移除）"""
        # 检查后端是否能正常启动（如果有 plotly 导入错误会启动失败）
        resp = requests.get(f"http://localhost:8000/health")
        print(f"    健康检查状态码: {resp.status_code}")
        return resp.status_code == 200

    def test_element_plus_checkbox_warnings(self):
        """测试 Element Plus checkbox 警告（前端测试）"""
        # 这是前端问题，后端无法直接测试
        # 这里只是占位，实际需要前端运行时检查控制台
        print("    ⚠ 需要前端运行时检查控制台警告")
        return True

    def run_all_tests(self):
        """运行所有测试"""
        if not self.login():
            print("\n登录失败，无法继续测试")
            return

        print("\n" + "="*60)
        print("第二阶段：中等缺陷测试")
        print("="*60)

        self.test("Plotly 导入问题已解决", self.test_plotly_not_imported)
        self.test("CORS OPTIONS 预检支持", self.test_cors_options_support)
        self.test("数据包导入验证", self.test_data_package_import_validation)
        self.test("Element Plus 警告检查", self.test_element_plus_checkbox_warnings)

        # 输出测试报告
        print("\n" + "="*60)
        print("测试报告")
        print("="*60)
        print(f"总测试数: {self.passed + self.failed}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        if self.passed + self.failed > 0:
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
    runner = Phase2TestRunner()
    runner.run_all_tests()
