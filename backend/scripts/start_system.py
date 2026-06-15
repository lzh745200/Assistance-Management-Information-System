#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统启动脚本
执行启动前检查、数据库初始化、系统配置等
"""
import sys
import os
from pathlib import Path
import subprocess
import time

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class SystemStarter:
    """系统启动器"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.backend_dir = self.base_dir / 'backend'

    def print_banner(self):
        """打印启动横幅"""
        print("=" * 70)
        print("军民融合乡村振兴管理系统 v1.1.0")
        print("Assistance Management Information Management System")
        print("=" * 70)
        print()

    def run_health_check(self) -> bool:
        """运行健康检查"""
        print("[1/5] 运行系统健康���查...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.backend_dir / 'scripts' / 'system_health_check.py')],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            print(result.stdout)
            if result.returncode != 0:
                print("[ERROR] 系统健康检查失败")
                return False

            print("[OK] 系统健康检查通过")
            return True
        except Exception as e:
            print(f"[ERROR] 健康检查失败: {e}")
            return False

    def check_database(self) -> bool:
        """检查数据库"""
        print("\n[2/5] 检查数据库...")
        db_path = self.base_dir / 'data' / 'rural_revitalization.db'

        if not db_path.exists():
            print("[WARN] 数据库不存在，将在首次启动时自动创建")
            return True

        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 检查关键表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                print("[WARN] 数据库缺少关键表，可能需要运行迁移")

            conn.close()
            print("[OK] 数据库检查通过")
            return True
        except Exception as e:
            print(f"[ERROR] 数据库检查失败: {e}")
            return False

    def check_env_config(self) -> bool:
        """检查环境配置"""
        print("\n[3/5] 检查环境配置...")
        env_file = self.base_dir / '.env'

        if not env_file.exists():
            print("[WARN] .env 文件不存在")
            env_example = self.base_dir / '.env.example'

            if env_example.exists():
                print("[INFO] 正在从 .env.example 创建 .env 文件...")
                try:
                    import shutil
                    shutil.copy(env_example, env_file)
                    print("[OK] .env 文件已创建，请检查配置")
                except Exception as e:
                    print(f"[ERROR] 创建 .env 文件失败: {e}")
                    return False
            else:
                print("[ERROR] .env.example 文件也不存在")
                return False

        # 检查关键配置项
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()

        warnings = []
        if 'change-in-production' in content.lower():
            warnings.append("SECRET_KEY 使用默认值，建议修改")
        if 'your-secret-key' in content.lower():
            warnings.append("配置项使用默认值，建议修改")

        if warnings:
            print("[WARN] 配置警告:")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print("[OK] 环境配置检查通过")

        return True

    def optimize_system(self):
        """系统优化"""
        print("\n[4/5] 应用系统优化...")

        # 清理临时文件
        temp_dirs = [
            self.base_dir / 'logs',
            self.base_dir / 'uploads',
        ]

        for temp_dir in temp_dirs:
            if temp_dir.exists():
                # 清理超过30天的文件
                try:
                    import time
                    current_time = time.time()
                    cleaned = 0

                    for file_path in temp_dir.rglob('*'):
                        if file_path.is_file():
                            file_age = current_time - file_path.stat().st_mtime
                            if file_age > 30 * 24 * 3600:  # 30天
                                file_path.unlink()
                                cleaned += 1

                    if cleaned > 0:
                        print(f"[INFO] 清理了 {cleaned} 个过期文件")
                except Exception as e:
                    print(f"[WARN] 清理临时文件失败: {e}")

        print("[OK] 系统优化完成")

    def start_backend(self):
        """启动后端服务"""
        print("\n[5/5] 启动后端服务...")
        print("-" * 70)
        print()

        try:
            # 切换到backend目录
            os.chdir(self.backend_dir)

            # 启动uvicorn
            cmd = [
                sys.executable,
                '-m',
                'uvicorn',
                'app.main:app',
                '--host', '0.0.0.0',
                '--port', '8000',
                '--reload',
                '--log-level', 'info'
            ]

            print(f"[INFO] 执行命令: {' '.join(cmd)}")
            print()
            print("=" * 70)
            print("后端服务启动中...")
            print("API文档: http://localhost:8000/docs")
            print("健康检查: http://localhost:8000/health")
            print("按 Ctrl+C 停止服务")
            print("=" * 70)
            print()

            subprocess.run(cmd)

        except KeyboardInterrupt:
            print("\n\n[INFO] 服务已停止")
        except Exception as e:
            print(f"\n[ERROR] 启动失败: {e}")
            return False

        return True

    def run(self):
        """运行启动流程"""
        self.print_banner()

        # 1. 健康检查
        if not self.run_health_check():
            print("\n[ERROR] 启动失败：健康检查未通过")
            print("[INFO] 请修复上述问题后重试")
            return False

        # 2. 数据库检查
        if not self.check_database():
            print("\n[ERROR] 启动失败：数据库检查未通过")
            return False

        # 3. 环境配置检查
        if not self.check_env_config():
            print("\n[ERROR] 启动失败：环境配置检查未通过")
            return False

        # 4. 系统优化
        self.optimize_system()

        # 5. 启动服务
        return self.start_backend()


if __name__ == '__main__':
    starter = SystemStarter()
    success = starter.run()
    sys.exit(0 if success else 1)
