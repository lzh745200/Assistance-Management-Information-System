#!/usr/bin/env python3
"""
系统功能全面检查脚本
"""
import requests
import json
from typing import Dict, List, Tuple

BASE_URL = "http://127.0.0.1:8000/api/v1"

class SystemChecker:
    def __init__(self):
        self.token = None
        self.results = []

    def login(self) -> bool:
        """登录"""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("data", {}).get("access_token")
                return bool(self.token)
        except Exception as e:
            print(f"登录失败: {e}")
        return False

    def get_headers(self) -> Dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def check_endpoint(self, method: str, path: str, name: str,
                      data: dict = None, params: dict = None) -> Tuple[bool, str]:
        """检查单个端点"""
        try:
            url = f"{BASE_URL}{path}"
            kwargs = {
                "headers": self.get_headers(),
                "timeout": 10
            }

            if params:
                kwargs["params"] = params
            if data:
                kwargs["json"] = data

            if method == "GET":
                response = requests.get(url, **kwargs)
            elif method == "POST":
                response = requests.post(url, **kwargs)
            elif method == "PUT":
                response = requests.put(url, **kwargs)
            elif method == "DELETE":
                response = requests.delete(url, **kwargs)
            else:
                return False, f"不支持的方法: {method}"

            if response.status_code in [200, 201]:
                return True, "OK"
            elif response.status_code == 404:
                return False, "端点不存在"
            elif response.status_code == 401:
                return False, "未授权"
            elif response.status_code == 403:
                return False, "无权限"
            elif response.status_code == 422:
                return False, f"参数错误: {response.text[:100]}"
            elif response.status_code == 500:
                return False, f"服务器错误: {response.text[:100]}"
            else:
                return False, f"状态码: {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "请求超时"
        except requests.exceptions.ConnectionError:
            return False, "连接失败"
        except Exception as e:
            return False, f"异常: {str(e)[:100]}"

    def check_module(self, module_name: str, endpoints: List[Tuple]):
        """检查模块"""
        print(f"\n{'='*60}")
        print(f"检查模块: {module_name}")
        print(f"{'='*60}")

        passed = 0
        failed = 0

        for method, path, name, data, params in endpoints:
            success, message = self.check_endpoint(method, path, name, data, params)
            status = "[PASS]" if success else "[FAIL]"

            if success:
                passed += 1
            else:
                failed += 1

            print(f"{status} {name}: {message}")

            self.results.append({
                "module": module_name,
                "name": name,
                "method": method,
                "path": path,
                "success": success,
                "message": message
            })

        print(f"\n模块统计: 通过 {passed}/{passed+failed}")
        return passed, failed

    def run_checks(self):
        """运行所有检查"""
        print("="*60)
        print("系统功能全面检查")
        print("="*60)

        # 登录
        print("\n1. 登录系统...")
        if not self.login():
            print("[FAIL] 登录失败，无法继续检查")
            return
        print("[PASS] 登录成功")

        total_passed = 0
        total_failed = 0

        # 组织管理
        passed, failed = self.check_module("组织管理", [
            ("GET", "/organizations", "查询组织列表", None, {"page": 1, "page_size": 10, "is_active": True}),
            ("GET", "/organizations/tree", "查询组织树", None, None),
            ("GET", "/organizations/types/options", "查询类型选项", None, None),
        ])
        total_passed += passed
        total_failed += failed

        # 村庄管理
        passed, failed = self.check_module("村庄管理", [
            ("GET", "/villages", "查询村庄列表", None, {"page": 1, "page_size": 10}),
        ])
        total_passed += passed
        total_failed += failed

        # 经费管理
        passed, failed = self.check_module("经费管理", [
            ("GET", "/funds", "查询经费列表", None, {"page": 1, "page_size": 10}),
            ("GET", "/fund-budgets", "查询预算列表", None, {"page": 1, "page_size": 10}),
        ])
        total_passed += passed
        total_failed += failed

        # 项目管理
        passed, failed = self.check_module("项目管理", [
            ("GET", "/projects", "查询项目列表", None, {"page": 1, "page_size": 10}),
        ])
        total_passed += passed
        total_failed += failed

        # 学校管理
        passed, failed = self.check_module("学校管理", [
            ("GET", "/schools", "查询学校列表", None, {"page": 1, "page_size": 10}),
        ])
        total_passed += passed
        total_failed += failed

        # 政策管理
        passed, failed = self.check_module("政策管理", [
            ("GET", "/policies", "查询政策列表", None, {"page": 1, "page_size": 10}),
        ])
        total_passed += passed
        total_failed += failed

        # 乡村工作
        passed, failed = self.check_module("乡村工作", [
            ("GET", "/rural-works", "查询工作列表", None, {"page": 1, "page_size": 10}),
            ("GET", "/rural-tasks", "查询任务列表", None, {"page": 1, "page_size": 10}),
        ])
        total_passed += passed
        total_failed += failed

        # 系统管理
        passed, failed = self.check_module("系统管理", [
            ("GET", "/system/health", "健康检查", None, None),
            ("GET", "/backup", "备份列表", None, None),
        ])
        total_passed += passed
        total_failed += failed

        # 用户管理
        passed, failed = self.check_module("用户管理", [
            ("GET", "/users", "查询用户列表", None, {"page": 1, "page_size": 10}),
        ])
        total_passed += passed
        total_failed += failed

        # 数据分析
        passed, failed = self.check_module("数据分析", [
            ("GET", "/data/dashboard", "仪表盘数据", None, None),
        ])
        total_passed += passed
        total_failed += failed

        # 总结
        print(f"\n{'='*60}")
        print(f"检查完成")
        print(f"{'='*60}")
        print(f"总计: 通过 {total_passed}, 失败 {total_failed}")
        print(f"通过率: {total_passed/(total_passed+total_failed)*100:.1f}%")

        # 失败的端点
        failed_endpoints = [r for r in self.results if not r["success"]]
        if failed_endpoints:
            print(f"\n失败的端点 ({len(failed_endpoints)}个):")
            for r in failed_endpoints:
                print(f"  - [{r['module']}] {r['name']}: {r['message']}")

        return self.results

if __name__ == "__main__":
    checker = SystemChecker()
    results = checker.run_checks()
