#!/usr/bin/env python3
"""
一键部署脚本 — 离线单机版

自动完成以下步骤：
1. 检查 Python 3.10+ 和 Node.js 18+ 环境
2. 创建/激活虚拟环境
3. 安装后端依赖
4. 运行数据库迁移
5. 安装前端依赖并构建
6. 生成默认配置文件
7. 创建启动快捷方式

方案 #25 — 一键部署配置向导
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def _venv_bin(name: str) -> str:
    """Return path to a binary inside the backend venv (cross-platform)."""
    return str(BACKEND_DIR / ".venv" / ("Scripts" if os.name == "nt" else "bin") / name)


def run(cmd: list, cwd: Path = None, description: str = "") -> bool:
    """执行命令并报告结果。"""
    label = f"  {description}" if description else f"  {' '.join(cmd[:3])}"
    print(f"{label}...", end=" ", flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd or PROJECT_ROOT))
        if result.returncode == 0:
            print("OK")
            return True
        else:
            print(f"FAILED (exit {result.returncode})")
            if result.stderr.strip():
                print(f"    {result.stderr.strip()[:200]}")
            return False
    except FileNotFoundError as e:
        print(f"SKIPPED ({e})")
        return False


def check_prerequisites() -> bool:
    """验证运行时环境。"""
    print("\n[1/6] 检查环境...")
    ok = True

    # Python
    py_ver = sys.version_info
    if py_ver < (3, 10):
        print(f"  ERROR: Python 3.10+ required, found {py_ver.major}.{py_ver.minor}")
        ok = False
    else:
        print(f"  Python {py_ver.major}.{py_ver.minor}.{py_ver.micro} — OK")

    # Node.js
    if run(["node", "--version"], description="Node.js"):
        pass
    else:
        print("  WARNING: Node.js not found — frontend build will be skipped")

    # Disk space
    try:
        import shutil
        usage = shutil.disk_usage(str(PROJECT_ROOT))
        free_gb = usage.free / (1024**3)
        print(f"  磁盘可用空间: {free_gb:.1f} GB")
        if free_gb < 2:
            print("  WARNING: 磁盘空间不足 2GB，可能无法完成部署")
    except Exception:
        pass

    return ok


def setup_backend() -> bool:
    """安装后端依赖并初始化数据库。"""
    print("\n[2/6] 设置后端...")

    # Create venv if needed
    venv_dir = BACKEND_DIR / ".venv"
    if not (venv_dir / "Scripts" / "python.exe").exists() and not (venv_dir / "bin" / "python").exists():
        print("  创建虚拟环境...")
        run([sys.executable, "-m", "venv", str(venv_dir)], description="venv")

    # Install dependencies
    if not run([_venv_bin("pip"), "install", "-r", "requirements.txt", "--quiet"], cwd=BACKEND_DIR, description="pip install"):
        return False

    # Initialize DB
    run([_venv_bin("python"), "-c", "from app.core.database import engine; from app.models.base import Base; Base.metadata.create_all(bind=engine); print('DB initialized')"], cwd=BACKEND_DIR, description="DB init")

    return True


def setup_frontend() -> bool:
    """安装前端依赖并构建。"""
    print("\n[3/6] 构建前端...")
    if not (FRONTEND_DIR / "node_modules").exists():
        if not run(["npm", "install", "--prefer-offline"], cwd=FRONTEND_DIR, description="npm install"):
            return False
    return run(["npm", "run", "build"], cwd=FRONTEND_DIR, description="npm build")


def generate_config() -> None:
    """生成默认 .env 配置文件。"""
    print("\n[4/6] 生成配置...")
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        print("  .env 已存在，跳过")
        return

    import secrets
    secret_key = secrets.token_hex(32)
    csrf_key = secrets.token_hex(32)

    env_content = f"""# 帮扶管理信息系统 — 自动生成的配置文件
PROJECT_NAME=帮扶管理信息系统
PROJECT_VERSION=1.2.0
SECRET_KEY={secret_key}
CSRF_SECRET_KEY={csrf_key}
CSRF_ENABLED=True
DATABASE_URL=sqlite:///./data/rural_revitalization.db
ENVIRONMENT=production
DEBUG=False
HOST=127.0.0.1
PORT=8000
"""
    env_file.write_text(env_content, encoding="utf-8")
    print(f"  .env 已生成 — SECRET_KEY 和 CSRF_SECRET_KEY 已自动设置")


def create_startup_shortcut() -> None:
    """创建启动脚本。"""
    print("\n[5/6] 创建启动脚本...")

    if os.name == "nt":
        bat_content = """@echo off
cd /d "%~dp0"
echo 启动帮扶管理信息系统...
start "" http://127.0.0.1:8000
cd backend
.venv\\Scripts\\python.exe start.py
pause
"""
        bat_file = PROJECT_ROOT / "启动系统.bat"
        bat_file.write_text(bat_content, encoding="gbk")
        print(f"  已创建 {bat_file.name}")
    else:
        sh_content = """#!/bin/bash
cd "$(dirname "$0")"
echo "启动帮扶管理信息系统..."
cd backend && .venv/bin/python start.py &
sleep 3
xdg-open http://127.0.0.1:8000 2>/dev/null &
wait
"""
        sh_file = PROJECT_ROOT / "start.sh"
        sh_file.write_text(sh_content)
        sh_file.chmod(0o755)
        print(f"  已创建 {sh_file.name}")


def verify_deployment() -> None:
    """快速验证部署是否成功。"""
    print("\n[6/6] 验证部署...")
    checks = []

    # Check venv
    venv_dir = BACKEND_DIR / ".venv"
    checks.append(("虚拟环境", venv_dir.exists()))

    # Check DB
    db_file = BACKEND_DIR / "data" / "rural_revitalization.db"
    checks.append(("数据库文件", db_file.exists()))

    # Check frontend build
    dist_dir = FRONTEND_DIR / "dist"
    checks.append(("前端构建产物", dist_dir.exists()))

    # Check .env
    env_file = PROJECT_ROOT / ".env"
    checks.append(("配置文件", env_file.exists()))

    for name, ok in checks:
        status = "OK" if ok else "MISSING"
        print(f"  {name}: {status}")

    all_ok = all(ok for _, ok in checks)
    if all_ok:
        print("\n部署成功！运行 启动系统.bat 或 python backend/start.py 启动服务。")
    else:
        print("\n部分组件未就绪，请检查上述警告。")


def main():
    parser = argparse.ArgumentParser(description="帮扶管理信息系统 — 一键部署")
    parser.add_argument("--skip-frontend", action="store_true", help="跳过前端构建")
    parser.add_argument("--skip-config", action="store_true", help="跳过配置文件生成")
    args = parser.parse_args()

    print("=" * 60)
    print("  帮扶管理信息系统 — 离线单机版部署")
    print("=" * 60)

    if not check_prerequisites():
        print("\n环境检查未通过，请修复后重试。")
        sys.exit(1)

    if not setup_backend():
        print("\n后端设置失败。")
        sys.exit(1)

    if not args.skip_frontend:
        setup_frontend()

    if not args.skip_config:
        generate_config()

    create_startup_shortcut()
    verify_deployment()


if __name__ == "__main__":
    main()
