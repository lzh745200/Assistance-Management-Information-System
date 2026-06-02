#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装后验证脚本
验证系统安装是否成功，所有功能是否正常
"""

import os
import sys
import time
import json
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Tuple

# 颜色定义
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'


class InstallationVerifier:
    """安装验证器"""

    def __init__(self, install_dir: str = None):
        self.install_dir = Path(install_dir) if install_dir else self._detect_install_dir()
        self.backend_url = "http://localhost:8000"
        self.backend_process = None
        self.results = {
            "environment": [],
            "startup": [],
            "functionality": [],
            "performance": [],
            "errors": []
        }

    def _detect_install_dir(self) -> Path:
        """检测安装目录"""
        if sys.platform == "win32":
            # Windows 默认安装路径
            possible_paths = [
                Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "军队乡村振兴管理系统",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "military-rural-system",
                Path.cwd()  # 当前目录（开发环境）
            ]
        else:
            # Linux 默认安装路径
            possible_paths = [
                Path("/opt/MRRMS"),
                Path.home() / ".local" / "share" / "military-rural-system",
                Path.cwd()  # 当前目录（开发环境）
            ]

        for path in possible_paths:
            if path.exists():
                return path

        return Path.cwd()

    def print_header(self, text: str):
        """打印标题"""
        print(f"\n{YELLOW}{'=' * 60}{NC}")
        print(f"{YELLOW}{text}{NC}")
        print(f"{YELLOW}{'=' * 60}{NC}\n")

    def print_success(self, text: str):
        """打印成功信息"""
        print(f"{GREEN}✓ {text}{NC}")

    def print_error(self, text: str):
        """打印错误信息"""
        print(f"{RED}✗ {text}{NC}")

    def print_warning(self, text: str):
        """打印警告信息"""
        print(f"{YELLOW}⚠ {text}{NC}")

    def check_environment(self) -> bool:
        """检查环境"""
        self.print_header("1. 环境检查")

        all_passed = True

        # 检查安装目录
        if self.install_dir.exists():
            self.print_success(f"安装目录存在: {self.install_dir}")
            self.results["environment"].append(("安装目录", "通过", str(self.install_dir)))
        else:
            self.print_error(f"安装目录不存在: {self.install_dir}")
            self.results["environment"].append(("安装目录", "失败", str(self.install_dir)))
            all_passed = False

        # 检查数据目录
        data_dir = self.install_dir / "data"
        if data_dir.exists():
            self.print_success(f"数据目录存在: {data_dir}")
            self.results["environment"].append(("数据目录", "通过", str(data_dir)))

            # 检查数据目录权限
            if os.access(data_dir, os.W_OK):
                self.print_success("数据目录可写")
                self.results["environment"].append(("数据目录权限", "通过", "可写"))
            else:
                self.print_error("数据目录不可写")
                self.results["environment"].append(("数据目录权限", "失败", "不可写"))
                all_passed = False
        else:
            self.print_warning(f"数据目录不存在: {data_dir}")
            self.results["environment"].append(("数据目录", "警告", "不存在"))

        # 检查后端二进制
        backend_bin = self._find_backend_binary()
        if backend_bin and backend_bin.exists():
            self.print_success(f"后端二进制存在: {backend_bin}")
            self.results["environment"].append(("后端二进制", "通过", str(backend_bin)))

            # 检查可执行权限
            if os.access(backend_bin, os.X_OK):
                self.print_success("后端二进制可执行")
                self.results["environment"].append(("后端可执行权限", "通过", "可执行"))
            else:
                self.print_error("后端二进制不可执行")
                self.results["environment"].append(("后端可执行权限", "失败", "不可执行"))
                all_passed = False
        else:
            self.print_error("后端二进制不存在")
            self.results["environment"].append(("后端二进制", "失败", "不存在"))
            all_passed = False

        return all_passed

    def _find_backend_binary(self) -> Path:
        """查找后端二进制文件"""
        possible_paths = [
            self.install_dir / "backend" / "dist" / "military-rural-backend.exe",
            self.install_dir / "backend" / "dist" / "military-rural-backend",
            self.install_dir / "resources" / "backend" / "military-rural-backend.exe",
            self.install_dir / "resources" / "backend" / "military-rural-backend",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def start_backend(self) -> bool:
        """启动后端服务"""
        self.print_header("2. 启动测试")

        backend_bin = self._find_backend_binary()
        if not backend_bin:
            self.print_error("无法找到后端二进制文件")
            return False

        try:
            # 启动后端
            print(f"启动后端服务: {backend_bin}")
            self.backend_process = subprocess.Popen(
                [str(backend_bin)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.install_dir)
            )

            # 等待启动
            print("等待后端启动...")
            max_retries = 30
            for i in range(max_retries):
                try:
                    response = requests.get(f"{self.backend_url}/health", timeout=1)
                    if response.status_code == 200:
                        self.print_success(f"后端启动成功 (耗时 {i + 1} 秒)")
                        self.results["startup"].append(("后端启动", "通过", f"{i + 1}秒"))
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)

            self.print_error(f"后端启动超时 (>{max_retries}秒)")
            self.results["startup"].append(("后端启动", "失败", "超时"))
            return False

        except Exception as e:
            self.print_error(f"启动后端失败: {e}")
            self.results["startup"].append(("后端启动", "失败", str(e)))
            return False

    def check_health(self) -> bool:
        """检查健康状态"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"健康检查通过: {data}")
                self.results["startup"].append(("健康检查", "通过", str(data)))
                return True
            else:
                self.print_error(f"健康检查失败: HTTP {response.status_code}")
                self.results["startup"].append(("健康检查", "失败", f"HTTP {response.status_code}"))
                return False
        except Exception as e:
            self.print_error(f"健康检查异常: {e}")
            self.results["startup"].append(("健康检查", "失败", str(e)))
            return False

    def check_database(self) -> bool:
        """检查数据库连接"""
        try:
            # 尝试登录（会触发数据库查询）
            response = requests.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"username": "admin", "password": "Admin@2026"},
                timeout=5
            )

            if response.status_code in [200, 401]:  # 200=成功, 401=密码错误但数据库正常
                self.print_success("数据库连接正常")
                self.results["startup"].append(("数据库连接", "通过", "正常"))
                return True
            else:
                self.print_error(f"数据库连接失败: HTTP {response.status_code}")
                self.results["startup"].append(("数据库连接", "失败", f"HTTP {response.status_code}"))
                return False
        except Exception as e:
            self.print_error(f"数据库连接异常: {e}")
            self.results["startup"].append(("数据库连接", "失败", str(e)))
            return False

    def test_functionality(self) -> bool:
        """测试功能"""
        self.print_header("3. 功能测试")

        all_passed = True

        # 测试登录
        if not self._test_login():
            all_passed = False

        # 测试基础 CRUD（需要登录后的 token）
        if hasattr(self, 'auth_token'):
            if not self._test_crud():
                all_passed = False
        else:
            self.print_warning("跳过 CRUD 测试（未登录）")

        return all_passed

    def _test_login(self) -> bool:
        """测试登录功能"""
        try:
            response = requests.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"username": "admin", "password": "Admin@2026"},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("data", {}).get("access_token")
                if not self.auth_token:
                    self.print_error("登录响应缺少 access_token 字段")
                    self.results["functionality"].append(("登录", "失败", "缺少 access_token"))
                    return False
                self.print_success("登录功能正常")
                self.results["functionality"].append(("登录", "通过", "成功"))
                return True
            else:
                self.print_error(f"登录失败: HTTP {response.status_code}")
                self.results["functionality"].append(("登录", "失败", f"HTTP {response.status_code}"))
                return False
        except Exception as e:
            self.print_error(f"登录异常: {e}")
            self.results["functionality"].append(("登录", "失败", str(e)))
            return False

    def _test_crud(self) -> bool:
        """测试基础 CRUD 操作"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        try:
            # 测试查询村庄列表
            response = requests.get(
                f"{self.backend_url}/api/v1/villages",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                self.print_success("村庄列表查询正常")
                self.results["functionality"].append(("村庄列表", "通过", "成功"))
                return True
            else:
                self.print_error(f"村庄列表查询失败: HTTP {response.status_code}")
                self.results["functionality"].append(("村庄列表", "失败", f"HTTP {response.status_code}"))
                return False
        except Exception as e:
            self.print_error(f"CRUD 测试异常: {e}")
            self.results["functionality"].append(("CRUD", "失败", str(e)))
            return False

    def test_performance(self) -> bool:
        """测试性能"""
        self.print_header("4. 性能测试")

        all_passed = True

        # 测试 API 响应时间
        if not self._test_api_response_time():
            all_passed = False

        # 测试内存占用
        if not self._test_memory_usage():
            all_passed = False

        return all_passed

    def _test_api_response_time(self) -> bool:
        """测试 API 响应时间"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            elapsed = (time.time() - start_time) * 1000  # 转换为毫秒

            if elapsed < 500:
                self.print_success(f"API 响应时间: {elapsed:.2f}ms (< 500ms)")
                self.results["performance"].append(("API响应时间", "通过", f"{elapsed:.2f}ms"))
                return True
            else:
                self.print_warning(f"API 响应时间: {elapsed:.2f}ms (>= 500ms)")
                self.results["performance"].append(("API响应时间", "警告", f"{elapsed:.2f}ms"))
                return True
        except Exception as e:
            self.print_error(f"API 响应时间测试失败: {e}")
            self.results["performance"].append(("API响应时间", "失败", str(e)))
            return False

    def _test_memory_usage(self) -> bool:
        """测试内存占用"""
        if not self.backend_process:
            self.print_warning("后端进程不存在，跳过内存测试")
            return True

        try:
            import psutil
            process = psutil.Process(self.backend_process.pid)
            memory_mb = process.memory_info().rss / 1024 / 1024

            if memory_mb < 500:
                self.print_success(f"内存占用: {memory_mb:.2f}MB (< 500MB)")
                self.results["performance"].append(("内存占用", "通过", f"{memory_mb:.2f}MB"))
                return True
            else:
                self.print_warning(f"内存占用: {memory_mb:.2f}MB (>= 500MB)")
                self.results["performance"].append(("内存占用", "警告", f"{memory_mb:.2f}MB"))
                return True
        except ImportError:
            self.print_warning("未安装 psutil，跳过内存测试")
            return True
        except Exception as e:
            self.print_error(f"内存测试失败: {e}")
            self.results["performance"].append(("内存占用", "失败", str(e)))
            return False

    def generate_report(self) -> Dict:
        """生成验证报告"""
        self.print_header("验证报告")

        total_tests = sum(len(v) for v in self.results.values() if isinstance(v, list))
        passed_tests = sum(
            1 for v in self.results.values() if isinstance(v, list)
            for item in v if item[1] == "通过"
        )
        failed_tests = sum(
            1 for v in self.results.values() if isinstance(v, list)
            for item in v if item[1] == "失败"
        )

        print(f"总测试数: {total_tests}")
        print(f"通过: {GREEN}{passed_tests}{NC}")
        print(f"失败: {RED}{failed_tests}{NC}")
        print(f"通过率: {passed_tests / total_tests * 100:.1f}%")

        # 保存报告
        report_path = self.install_dir / "verification_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"\n报告已保存: {report_path}")

        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": passed_tests / total_tests * 100 if total_tests > 0 else 0
        }

    def cleanup(self):
        """清理资源"""
        if self.backend_process:
            print("\n停止后端服务...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            print("后端服务已停止")

    def run(self) -> bool:
        """运行完整验证"""
        try:
            # 1. 环境检查
            if not self.check_environment():
                self.print_error("环境检查失败，终止验证")
                return False

            # 2. 启动后端
            if not self.start_backend():
                self.print_error("后端启动失败，终止验证")
                return False

            # 3. 健康检查
            if not self.check_health():
                self.print_error("健康检查失败")

            # 4. 数据库检查
            if not self.check_database():
                self.print_error("数据库检查失败")

            # 5. 功能测试
            self.test_functionality()

            # 6. 性能测试
            self.test_performance()

            # 7. 生成报告
            report = self.generate_report()

            return report["failed"] == 0

        finally:
            self.cleanup()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="军队乡村振兴管理系统 - 安装验证")
    parser.add_argument("--install-dir", help="安装目录路径")
    args = parser.parse_args()

    verifier = InstallationVerifier(args.install_dir)
    success = verifier.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
