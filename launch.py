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
# 注意：Windows 上 compileall 使用 ProcessPoolExecutor（spawn 方式），
# worker 进程可能因各种原因崩溃（DLL 缺失、内存不足等），导致
# concurrent.futures.process.BrokenProcessPool 启动失败。
# 解决方案：Windows 上使用 workers=1（单进程），避免进程池问题。
_compile_flag = BACKEND_DIR / "app" / ".pyc_compiled"
if not _compile_flag.exists():
    import compileall
    print("  预编译模块（首次启动需几秒）...")
    # 使用 sys.platform 与代码库其余 21 处保持一致（避免 platform 模块 wmic 开销）
    _compile_workers = 1 if sys.platform == "win32" else 0
    try:
        _compile_ok = compileall.compile_dir(
            str(BACKEND_DIR / "app"), quiet=2, workers=_compile_workers,
        )
        if _compile_ok:
            _compile_flag.touch()
        else:
            print("  [WARN] 部分 .pyc 编译失败（不影响系统运行，首次运行可能稍慢）")
    except Exception as _compile_err:
        print(f"  [WARN] 预编译失败（不影响系统运行）: {_compile_err}")
        print("  系统将继续启动，首次运行可能稍慢...")

threading.Thread(target=open_browser_when_ready, daemon=True).start()

print()
print("  ================================================")
print("    帮扶管理信息系统 v1.2.0")
print("    关闭此窗口 = 停止系统")
print("  ================================================")
print()

os.chdir(BACKEND_DIR)
sys.exit(subprocess.run([sys.executable, "start.py"]).returncode)
