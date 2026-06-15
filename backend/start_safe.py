#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全启动脚本 - 带完整错误捕获和自动修复
"""

import os
import sys
import time
import signal
import traceback
from pathlib import Path

# 设置UTF-8编码
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# 确保在正确的目录
base_dir = Path(__file__).parent
os.chdir(base_dir)
sys.path.insert(0, str(base_dir))

def print_banner():
    """打印启动横幅"""
    print("\n" + "=" * 70)
    print("  帮扶管理信息系统 - 后端服务")
    print("  版本: 1.0.4 (增强版)")
    print("=" * 70 + "\n")

def check_and_kill_existing():
    """检查并终止已存在的进程"""
    import socket
    port = int(os.getenv('PORT', '8000'))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()

        if result == 0:
            print(f"[INFO] 检测到端口 {port} 已被占用")

            if sys.platform == 'win32':
                try:
                    import subprocess
                    # 获取占用端口的PID
                    result = subprocess.run(
                        ['netstat', '-ano'],
                        capture_output=True, text=True, timeout=5
                    )
                    pid = None
                    for line in result.stdout.splitlines():
                        if f':{port}' in line and 'LISTENING' in line:
                            parts = line.split()
                            pid = parts[-1] if parts else None
                            break

                    if pid:
                        print(f"[INFO] 正在终止进程 PID: {pid}")
                        subprocess.run(['taskkill', '/F', '/PID', pid],
                                     capture_output=True, timeout=5)
                        time.sleep(2)
                        print("[OK] 已终止旧进程")
                except Exception as e:
                    print(f"[WARN] 无法自动终止旧进程: {e}")
                    print("请手动关闭占用端口的程序")
                    return False
    except Exception as e:
        print(f"[ERROR] 端口检查失败: {e}")

    return True

def ensure_directories():
    """确保必要的目录存在"""
    dirs = [
        './data',
        './logs',
        './uploads',
        './exports',
        './backups',
        './data/cache',
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def check_database():
    """检查数据库状态"""
    import sqlite3

    db_path = os.getenv('DATABASE_URL', 'sqlite:///./data/rural_revitalization.db')
    db_path = db_path.replace('sqlite:///', '')

    if not os.path.exists(db_path):
        print("[INFO] 数据库文件不存在，将自动创建")
        return True

    try:
        conn = sqlite3.connect(db_path)
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()

        if result[0] == "ok":
            print("[OK] 数据库完整性检查通过")
            return True
        else:
            print(f"[ERROR] 数据库损坏: {result[0]}")
            # 备份损坏的数据库
            backup_path = f"{db_path}.corrupted.{int(time.time())}"
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"[INFO] 损坏的数据库已备份到: {backup_path}")
            os.remove(db_path)
            print("[INFO] 已删除损坏的数据库，将自动创建新数据库")
            return True
    except Exception as e:
        print(f"[ERROR] 数据库检查失败: {e}")
        return False

def initialize_database():
    """初始化数据库"""
    try:
        print("[INFO] 正在初始化数据库...")
        from app.core.database import engine
        from app.models.base import Base
        import app.models  # 导入所有模型

        Base.metadata.create_all(bind=engine)
        print("[OK] 数据库初始化完成")
        return True
    except Exception as e:
        print(f"[ERROR] 数据库初始化失败: {e}")
        traceback.print_exc()
        return False

def check_python_version():
    """检查Python版本"""
    print("[INFO] 检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"[ERROR] Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("[ERROR] 需要Python 3.8或更高版本")
        return False
    print(f"[OK] Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """检查依赖包"""
    print("[INFO] 检查依赖包...")
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pydantic',
        'dotenv',  # python-dotenv的导入名是dotenv
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"[ERROR] 缺少依赖包: {', '.join(missing)}")
        print(f"[INFO] 请运行: pip install {' '.join(missing)}")
        return False

    print(f"[OK] 所有依赖包已安装")
    return True

def check_config_file():
    """检查配置文件"""
    print("[INFO] 检查配置文件...")
    env_file = Path('.env')

    if not env_file.exists():
        print("[WARN] .env文件不存在，将使用默认配置")
        return True

    # 检查必要的配置项
    required_configs = ['SECRET_KEY', 'DATABASE_URL']
    missing_configs = []

    try:
        from dotenv import dotenv_values
        config = dotenv_values('.env')

        for key in required_configs:
            if key not in config or not config[key]:
                missing_configs.append(key)

        if missing_configs:
            print(f"[WARN] 缺少配置项: {', '.join(missing_configs)}")
            print("[INFO] 将使用默认值")

        print("[OK] 配置文件检查完成")
        return True

    except Exception as e:
        print(f"[WARN] 配置文件检查失败: {e}")
        return True  # 不阻止启动

def check_disk_space():
    """检查磁盘空间"""
    print("[INFO] 检查磁盘空间...")
    try:
        import shutil
        stat = shutil.disk_usage('.')
        free_gb = stat.free / (1024 ** 3)

        if free_gb < 1:
            print(f"[ERROR] 磁盘空间不足: {free_gb:.2f}GB")
            print("[ERROR] 至少需要1GB可用空间")
            return False

        print(f"[OK] 可用磁盘空间: {free_gb:.2f}GB")
        return True

    except Exception as e:
        print(f"[WARN] 磁盘空间检查失败: {e}")
        return True  # 不阻止启动

def check_permissions():
    """检查文件权限"""
    print("[INFO] 检查文件权限...")
    critical_dirs = ['./data', './logs', './uploads', './backups']

    for dir_path in critical_dirs:
        path = Path(dir_path)
        if path.exists():
            # 尝试写入测试文件
            test_file = path / '.write_test'
            try:
                test_file.write_text('test')
                test_file.unlink()
            except Exception as e:
                print(f"[ERROR] 目录 {dir_path} 无写入权限: {e}")
                return False

    print("[OK] 文件权限检查通过")
    return True

def check_version_change():
    """检查版本变更"""
    print("[INFO] 检查版本变更...")
    try:
        from app.services.version_service import version_service

        version_check = version_service.check_version_change()
        if version_check and version_check.get('changed'):
            old_ver = version_check.get('old_version')
            new_ver = version_check.get('new_version')
            print(f"[INFO] 检测到版本变更: {old_ver} -> {new_ver}")
            print("[INFO] 将执行自动升级...")

            # 执行升级
            upgrade_result = version_service.upgrade(
                new_version=new_ver,
                description="自动升级",
                backup_before_upgrade=True
            )

            if upgrade_result.get('status') == 'success':
                print("[OK] 版本升级完成")
            else:
                print(f"[WARN] 版本升级失败: {upgrade_result.get('message')}")

        else:
            current_ver = version_check.get('version') if version_check else 'unknown'
            print(f"[OK] 当前版本: {current_ver}")

        return True

    except Exception as e:
        print(f"[WARN] 版本检查失败: {e}")
        return True  # 不阻止启动

def start_server():
    """启动服务器"""
    try:
        import uvicorn
        from app.main import app

        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', '8000'))

        print(f"\n[INFO] 正在启动服务器...")
        print(f"[INFO] 地址: http://{host}:{port}")
        print(f"[INFO] API文档: http://{host}:{port}/docs")
        print(f"[INFO] 按 Ctrl+C 停止服务\n")

        # 配置uvicorn
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False,  # 禁用自动重载以避免多进程问题
            workers=1,  # 单进程模式
        )

        server = uvicorn.Server(config)
        server.run()

    except KeyboardInterrupt:
        print("\n\n[INFO] 收到停止信号，正在关闭服务器...")
    except Exception as e:
        print(f"\n[ERROR] 服务器启动失败: {e}")
        traceback.print_exc()
        return False

    return True

def main():
    """主函数"""
    print_banner()

    # 1. 检查Python版本
    if not check_python_version():
        return False

    # 2. 检查依赖包
    if not check_dependencies():
        return False

    # 3. 检查配置文件
    if not check_config_file():
        return False

    # 4. 检查磁盘空间
    if not check_disk_space():
        return False

    # 5. 检查并终止已存在的进程
    if not check_and_kill_existing():
        print("\n[ERROR] 无法清理端口，请手动关闭占用端口的程序后重试")
        return False

    # 6. 确保目录存在
    print("[INFO] 检查目录结构...")
    ensure_directories()
    print("[OK] 目录结构检查完成")

    # 7. 检查文件权限
    if not check_permissions():
        return False

    # 8. 检查数据库
    print("[INFO] 检查数据库...")
    if not check_database():
        return False

    # 9. 初始化数据库
    if not initialize_database():
        return False

    # 10. 检查版本变更
    if not check_version_change():
        return False

    # 11. 启动服务器
    return start_server()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] 服务已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[FATAL ERROR] 启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)
