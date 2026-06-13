"""
启动脚本 — 单窗口运行，显示完整启动进度
"""
import os, sys, subprocess, webbrowser, socket, threading, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
RESOURCES_FRONTEND = PROJECT_ROOT / "resources" / "frontend"
PORT = 8000


def kill_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    busy = s.connect_ex(("127.0.0.1", PORT)) == 0
    s.close()
    if not busy:
        return
    try:
        subprocess.run(["cmd", "/c",
            f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{PORT} ^| findstr LISTENING\') do taskkill /F /PID %a'],
            capture_output=True, timeout=5)
    except Exception:
        pass


def open_browser_when_ready():
    """后台线程 — 等后端就绪后打开浏览器"""
    for _ in range(30):
        time.sleep(1)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            if s.connect_ex(("127.0.0.1", PORT)) == 0:
                s.close()
                webbrowser.open(f"http://localhost:{PORT}")
                return
            s.close()
        except Exception:
            pass


if not (RESOURCES_FRONTEND / "index.html").exists():
    print("[WARN] 前端未构建，仅提供 API 服务 (http://localhost:8000/docs)")
    print("  构建前端: cd frontend && npm run build")

kill_port()

# 预编译 Python 模块（首次较慢，后续 instant）
import compileall, os as _os
_compile_flag = BACKEND_DIR / "app" / ".pyc_compiled"
if not _compile_flag.exists():
    print("  预编译模块（首次启动需几秒）...")
    compileall.compile_dir(str(BACKEND_DIR / "app"), quiet=2, workers=0)
    _compile_flag.touch()

threading.Thread(target=open_browser_when_ready, daemon=True).start()

print()
print("  ================================================")
print("    军队乡村振兴管理系统 v1.2.0")
print("    关闭此窗口 = 停止系统")
print("  ================================================")
print()

os.chdir(BACKEND_DIR)
sys.exit(subprocess.run([sys.executable, "start.py"]).returncode)
