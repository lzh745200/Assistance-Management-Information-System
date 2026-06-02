#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统稳定性验证脚本
执行全面的系统测试，确保系统稳定运行
"""
import sys
import os
import subprocess
import time
from pathlib import Path
import requests
import sqlite3

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class SystemValidator:
    """系统稳定性验证器"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.backend_dir = self.base_dir / 'backend'
        self.errors = []
        self.warnings = []
        self.passed_tests = 0
        self.failed_tests = 0

    def print_header(self, title):
        """打印标题"""
        print("\n" + "=" * 70)
        print(title)
        print("=" * 70)

    def test_database_integrity(self) -> bool:
        """测试数据库完整性"""
        self.print_header("测试 1: 数据库完整性检查")

        db_path = self.base_dir / 'data' / 'rural_revitalization.db'

        if not db_path.exists():
            self.warnings.append("数据库文件不存在（首次运行正常）")
            print("[SKIP] 数据库文件不存在")
            return True

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 检查数据库完整性
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            if result[0] != 'ok':
                self.errors.append(f"数据库完整性检查失败: {result[0]}")
                self.failed_tests += 1
                print(f"[FAIL] 数据库完整性检查失败: {result[0]}")
                return False

            # 检查关键表
            required_tables = ['users', 'villages', 'funds', 'projects']
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            missing_tables = [t for t in required_tables if t not in tables]
            if missing_tables:
                self.warnings.append(f"缺少表: {', '.join(missing_tables)}")
                print(f"[WARN] 缺少表: {', '.join(missing_tables)}")

            # 检查索引
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = cursor.fetchall()
            print(f"[INFO] 数据库包含 {len(indexes)} 个索引")

            conn.close()

            self.passed_tests += 1
            print("[PASS] 数据库完整性检查通过")
            return True

        except Exception as e:
            self.errors.append(f"数据库检查失败: {e}")
            self.failed_tests += 1
            print(f"[FAIL] 数据库��查失败: {e}")
            return False

    def test_configuration(self) -> bool:
        """测试配置文件"""
        self.print_header("测试 2: 配置文件检查")

        env_file = self.base_dir / '.env'

        if not env_file.exists():
            self.errors.append(".env 文件不存在")
            self.failed_tests += 1
            print("[FAIL] .env 文件不存在")
            return False

        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查必需配置项
            required_keys = [
                'SECRET_KEY',
                'DATABASE_URL',
                'CORS_ORIGINS'
            ]

            missing_keys = []
            for key in required_keys:
                if key not in content:
                    missing_keys.append(key)

            if missing_keys:
                self.errors.append(f"缺少配置项: {', '.join(missing_keys)}")
                self.failed_tests += 1
                print(f"[FAIL] 缺少配置项: {', '.join(missing_keys)}")
                return False

            # 检查默认值
            if 'change-in-production' in content.lower():
                self.warnings.append("SECRET_KEY 使用默认值")
                print("[WARN] SECRET_KEY 使用默认值，建议修改")

            self.passed_tests += 1
            print("[PASS] 配置文件检查通过")
            return True

        except Exception as e:
            self.errors.append(f"配置文件检查失败: {e}")
            self.failed_tests += 1
            print(f"[FAIL] 配置文件检查失败: {e}")
            return False

    def test_file_permissions(self) -> bool:
        """测试文件权限"""
        self.print_header("测试 3: 文件权限检查")

        required_dirs = [
            'data',
            'logs',
            'uploads',
            'backups',
            'exports'
        ]

        all_writable = True

        for dir_name in required_dirs:
            dir_path = self.base_dir / dir_name

            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"[INFO] 创建目录: {dir_name}")
                except Exception as e:
                    self.errors.append(f"无法创建目录 {dir_name}: {e}")
                    all_writable = False
                    print(f"[FAIL] 无法创建目录 {dir_name}: {e}")
                    continue

            # 测试写权限
            test_file = dir_path / '.write_test'
            try:
                test_file.touch()
                test_file.unlink()
                print(f"[PASS] 目录可写: {dir_name}")
            except Exception as e:
                self.errors.append(f"目录 {dir_name} 无写权限: {e}")
                all_writable = False
                print(f"[FAIL] 目录 {dir_name} 无写权限: {e}")

        if all_writable:
            self.passed_tests += 1
            return True
        else:
            self.failed_tests += 1
            return False

    def test_dependencies(self) -> bool:
        """测试依赖包"""
        self.print_header("测试 4: 依赖包检查")

        required_packages = [
            'fastapi',
            'uvicorn',
            'sqlalchemy',
            'pydantic',
            'bcrypt',
            'jose',
            'httpx'
        ]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
                print(f"[PASS] 依赖包已安装: {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"[FAIL] 缺少依赖包: {package}")

        if missing_packages:
            self.errors.append(f"缺少依赖包: {', '.join(missing_packages)}")
            self.failed_tests += 1
            return False
        else:
            self.passed_tests += 1
            return True

    def test_api_endpoints(self) -> bool:
        """测试API端点（需要服务运行）"""
        self.print_header("测试 5: API端点检查")

        base_url = "http://localhost:8000"

        # 检查服务是否运行
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("[PASS] 健康检查端点正常")
            else:
                self.warnings.append(f"健康检查返回状态码: {response.status_code}")
                print(f"[WARN] 健康检查返回状态码: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.warnings.append("API服务未运行（需要先启动服务）")
            print("[SKIP] API服务未运行")
            return True
        except Exception as e:
            self.warnings.append(f"API检查失败: {e}")
            print(f"[WARN] API检查失败: {e}")
            return True

        # 测试其他端点
        endpoints = [
            "/",
            "/docs",
            "/metrics",
            "/stats"
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code in [200, 401, 403]:  # 401/403表示需要认证，但端点存在
                    print(f"[PASS] 端点可访问: {endpoint}")
                else:
                    print(f"[WARN] 端点返回 {response.status_code}: {endpoint}")
            except Exception as e:
                print(f"[WARN] 端点检查失败 {endpoint}: {e}")

        self.passed_tests += 1
        return True

    def test_security_config(self) -> bool:
        """测试安全配置"""
        self.print_header("测试 6: 安全配置检查")

        env_file = self.base_dir / '.env'

        if not env_file.exists():
            self.failed_tests += 1
            return False

        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()

            security_checks = []

            # 检查密钥强度
            if 'SECRET_KEY' in content:
                if 'change-in-production' in content or 'your-secret-key' in content:
                    security_checks.append("SECRET_KEY 使用默认值")
                else:
                    print("[PASS] SECRET_KEY 已自定义")

            # 检查CORS配置
            if 'CORS_ORIGINS' in content:
                if '0.0.0.0' in content or '*' in content:
                    security_checks.append("CORS配置过于宽松")
                else:
                    print("[PASS] CORS配置合理")

            # 检查调试模式
            if 'DEBUG=true' in content.lower():
                security_checks.append("调试模式已启用（生产环境应关闭）")
            else:
                print("[PASS] 调试模式已关闭")

            if security_checks:
                for check in security_checks:
                    self.warnings.append(check)
                    print(f"[WARN] {check}")

            self.passed_tests += 1
            return True

        except Exception as e:
            self.errors.append(f"安全配置检查失败: {e}")
            self.failed_tests += 1
            print(f"[FAIL] 安全配置检查失败: {e}")
            return False

    def test_backup_system(self) -> bool:
        """测试备份系统"""
        self.print_header("测试 7: 备份系统检查")

        backups_dir = self.base_dir / 'backups'

        if not backups_dir.exists():
            backups_dir.mkdir(parents=True, exist_ok=True)
            print("[INFO] 创建备份目录")

        # 检查备份目录可写
        test_file = backups_dir / '.backup_test'
        try:
            test_file.touch()
            test_file.unlink()
            print("[PASS] 备份目录可写")
            self.passed_tests += 1
            return True
        except Exception as e:
            self.errors.append(f"备份目录不可写: {e}")
            self.failed_tests += 1
            print(f"[FAIL] 备份目录不可写: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print("系统稳定性验证")
        print("=" * 70)
        print()

        tests = [
            self.test_database_integrity,
            self.test_configuration,
            self.test_file_permissions,
            self.test_dependencies,
            self.test_api_endpoints,
            self.test_security_config,
            self.test_backup_system
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                self.errors.append(f"测试执行失败: {e}")
                self.failed_tests += 1
                print(f"[ERROR] 测试执行失败: {e}")

        # 输出总结
        self.print_header("测试总结")
        print()
        print(f"通过测试: {self.passed_tests}")
        print(f"失败测试: {self.failed_tests}")
        print(f"警告数量: {len(self.warnings)}")
        print(f"错误数量: {len(self.errors)}")
        print()

        if self.errors:
            print("[ERROR] 发现以下错误:")
            for error in self.errors:
                print(f"  - {error}")
            print()

        if self.warnings:
            print("[WARN] 发现以下警告:")
            for warning in self.warnings:
                print(f"  - {warning}")
            print()

        if self.failed_tests == 0:
            print("=" * 70)
            print("[SUCCESS] 所有测试通过，系统稳定")
            print("=" * 70)
            return True
        else:
            print("=" * 70)
            print("[FAILURE] 部分测试失败，请修复后重试")
            print("=" * 70)
            return False


if __name__ == '__main__':
    validator = SystemValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)
