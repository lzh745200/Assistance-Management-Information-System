"""
军队乡村振兴管理系统 - 一键启动脚本
双击运行或命令行: python 启动系统.py
"""
import os
import sys
import time
import socket
import subprocess
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
RESOURCES_FRONTEND = PROJECT_ROOT / "resources" / "frontend"

PYTHON = sys.executable


def find_free_port(start=8000):
    """查找可用端口"""
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return 8000


def kill_port(port):
    """清理占用端口的进程"""
    try:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if f":{port} " in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                subprocess.run(["taskkill", "/F", "/PID", pid],
                               capture_output=True, timeout=10)
    except Exception:
        pass


def check_frontend():
    """检查前端是否已构建"""
    if (RESOURCES_FRONTEND / "index.html").exists():
        return True
    print("  前端未构建，正在构建...")
    try:
        subprocess.run(["npm", "run", "build"], cwd=FRONTEND_DIR,
                       capture_output=True, timeout=120, check=True)
        # 同步到 resources/frontend
        import shutil
        dist = FRONTEND_DIR / "dist"
        if dist.exists():
            if RESOURCES_FRONTEND.exists():
                shutil.rmtree(RESOURCES_FRONTEND, ignore_errors=True)
            shutil.copytree(dist, RESOURCES_FRONTEND)
            print(f"  前端已同步：{RESOURCES_FRONTEND}")
            return True
    except Exception as e:
        print(f"  [警告] 前端构建失败: {e}")
    return False


def main():
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║     军队乡村振兴管理系统 v1.2.0             ║")
    print("  ║     一键启动                                ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print(f"  Python: {sys.version.split()[0]}  [{PYTHON}]")

    port = 8000

    # 1. 清理端口
    print("[1/4] 清理后端端口...")
    kill_port(port)
    print(f"      端口 {port} 已清理")

    # 2. 检查前端
    print("[2/4] 检查前端...")
    check_frontend()

    # 3. 启动后端
    print("[3/4] 启动后端服务...")
    backend_proc = subprocess.Popen(
        [PYTHON, str(BACKEND_DIR / "start.py")],
        cwd=BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    # 4. 等待就绪
    print("[4/4] 等待后端就绪...")
    for i in range(60):
        time.sleep(1)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                print(f"      后端已就绪! (耗时约 {i + 1} 秒)")
                break
    else:
        print("      [警告] 后端启动超时")

    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║  系统启动完成!                              ║")
    print("  ║                                            ║")
    print(f"  ║  访问地址: http://localhost:{port}           ")
    print(f"  ║  API 文档: http://localhost:{port}/docs      ")
    print("  ║                                            ║")
    print("  ║  默认账号: admin / admin123                 ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()

    webbrowser.open(f"http://localhost:{port}")

    print("  后端正在运行中，关闭此窗口不会停止后端")
    print("  停止后端请运行: scripts\\stop-all.bat")
    print()
    input("  按 Enter 关闭此窗口...")


if __name__ == "__main__":
    main()
