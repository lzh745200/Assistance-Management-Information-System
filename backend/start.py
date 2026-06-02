#!/usr/bin/env python
"""
军队乡村振兴管理系统 - 后端服务启动入口
用于 PyInstaller 打包时作为入口脚本
"""

import os
import sys
import socket

# ── 关键修复：Windows 中文系统的控制台默认 GBK 编码，无法输出 Unicode 字符 ──
# 必须在任何 print() 之前执行，否则 PyInstaller 打包后在 GBK 环境会崩溃
try:
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
# 备用方案：如果 reconfigure 不可用（Python < 3.7 或缓冲区问题），用环境变量强制
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# PyInstaller 打包后, 确保能正确找到 app 模块
if getattr(sys, 'frozen', False):
    # 运行在 PyInstaller 打包环境中
    base_dir = os.path.dirname(sys.executable)
    os.chdir(base_dir)
    # 关键修复：PyInstaller 打包后 app 目录在 _MEIPASS 中，
    # 必须将 _MEIPASS 添加到 sys.path 才能正确导入
    if hasattr(sys, '_MEIPASS'):
        meipass_dir = sys._MEIPASS
        if meipass_dir not in sys.path:
            sys.path.insert(0, meipass_dir)
        # 同时确保 exe 所在目录在 sys.path（用于数据文件）
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)


def _check_python_arch():
    """检查 Python 架构 — 64-bit Windows 上使用 32-bit Python 性能显著下降"""
    import struct
    bits = struct.calcsize("P") * 8
    if bits == 32 and sys.platform == 'win32':
        # 检查是否在 64-bit OS 上
        import platform
        machine = platform.machine().lower()
        if machine in ('amd64', 'x86_64', 'arm64'):
            print("[WARN] 检测到 32-bit Python 运行在 64-bit Windows 上")
            print("  性能将显著下降（加密操作慢 2-5x，内存操作慢 30%+）")
            print(f"  当前: {sys.executable}")
            # 检查 64-bit Python 是否可用
            possible_paths = [
                r'C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe',
                r'C:\Python311\python.exe',
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    print(f"  建议使用: {p}")
                    break
            print("  或通过 .venv\\Scripts\\python start.py 启动（64-bit）")
        else:
            print(f"[INFO] 32-bit Python on 32-bit OS — this is expected")
    else:
        print(f"[OK] Python {bits}-bit — optimal")


def _check_vcruntime():
    """检查 VC++ 运行时 DLL 是否可用（仅 Windows）"""
    if sys.platform != 'win32':
        return
    import ctypes
    dlls_to_check = ['vcruntime140', 'vcruntime140_1', 'msvcp140']
    missing = []
    for dll_name in dlls_to_check:
        try:
            ctypes.WinDLL(dll_name)
        except OSError:
            missing.append(dll_name + '.dll')
    if missing:
        print(f"[WARN] 缺少 VC++ 运行时 DLL: {', '.join(missing)}")
        print("  请安装 Visual C++ 2015-2022 Redistributable (x64)")
        print("  下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe")
        # 不退出，让后续启动尝试继续（PyInstaller 打包可能自带了这些 DLL）
    else:
        print("[OK] VC++ 运行时 DLL 检查通过")


def _check_port_available(host: str, port: int) -> bool:
    """检查端口是否可用，不可用时打印占用进程信息"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        sock.close()
        print(f"[WARN] 端口 {port} 已被占用")
        # 尝试打印占用进程信息
        if sys.platform == 'win32':
            try:
                import subprocess
                result = subprocess.run(
                    ['netstat', '-aon'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        pid = parts[-1] if parts else '未知'
                        print(f"  占用进程 PID: {pid}")
                        # 尝试获取进程名
                        try:
                            name_result = subprocess.run(
                                ['tasklist', '/fi', f'PID eq {pid}', '/fo', 'csv', '/nh'],
                                capture_output=True, text=True, timeout=5
                            )
                            if name_result.stdout.strip():
                                print(f"  占用进程: {name_result.stdout.strip()}")
                        except Exception:
                            pass
                        break
            except Exception:
                pass
        return False


def _ensure_dirs():
    """确保运行时所需的目录存在（打包后首次运行时创建）"""
    dirs = [
        os.environ.get("UPLOAD_DIR", "./uploads"),
        os.environ.get("CACHE_DIR", "./data/cache"),
        os.environ.get("EXPORT_DIR", "./exports"),
    ]
    # 从 LOG_FILE 提取日志目录
    log_file = os.environ.get("LOG_FILE", "./logs/app.log")
    dirs.append(os.path.dirname(log_file))

    # 从 DATABASE_URL 提取数据库目录
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./data/rural_revitalization.db")
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            dirs.append(db_dir)

    for d in dirs:
        if d:
            os.makedirs(d, exist_ok=True)


def _check_database_integrity():
    """启动时执行 SQLite PRAGMA integrity_check，异常时尝试从最近备份恢复"""
    import sqlite3

    db_url = os.environ.get("DATABASE_URL", "sqlite:///./data/rural_revitalization.db")
    if not db_url.startswith("sqlite"):
        return

    db_path = db_url.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        print(f"数据库文件不存在，将在启动时自动创建: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()

        if result and result[0] == "ok":
            print("[OK] 数据库完整性检查通过")
        else:
            print(f"[WARN] 数据库完整性检查异常: {result}")
            _try_restore_from_backup(db_path)
    except Exception as e:
        print(f"[ERROR] 数据库完整性检查失败: {e}")
        _try_restore_from_backup(db_path)


def _try_restore_from_backup(db_path: str):
    """尝试从最近的备份文件恢复数据库，无备份时删除损坏文件并让应用自动创建空库"""
    import glob
    import shutil

    backup_dir = os.environ.get("BACKUP_DIR", "./backups")
    backups = []
    if os.path.exists(backup_dir):
        # 查找最近的 .db 或 .db.gz 备份文件
        backups = sorted(
            glob.glob(os.path.join(backup_dir, "*.db")) +
            glob.glob(os.path.join(backup_dir, "*.db.gz")),
            key=os.path.getmtime,
            reverse=True,
        )

    # 先备份损坏文件
    corrupted_path = db_path + ".corrupted"
    try:
        shutil.copy2(db_path, corrupted_path)
        print(f"[INFO] 损坏的数据库已保存为: {corrupted_path}")
    except Exception as e:
        print(f"[WARN] 备份损坏文件失败: {e}")

    if backups:
        latest_backup = backups[0]
        print(f"[INFO] 尝试从备份恢复: {latest_backup}")
        try:
            if latest_backup.endswith(".gz"):
                import gzip
                with gzip.open(latest_backup, 'rb') as f_in:
                    with open(db_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(latest_backup, db_path)
            print("[OK] 数据库已从备份恢复")
            return
        except Exception as e:
            print(f"[ERROR] 从备份恢复失败: {e}")

    # 无备份或备份恢复失败：删除损坏文件，让应用启动时自动创建空库
    print("[INFO] 无可用备份，将删除损坏数据库并自动创建空库")
    try:
        os.remove(db_path)
        # 同时删除 SQLite WAL/SHM 文件
        for suffix in ('-wal', '-shm'):
            wal_path = db_path + suffix
            if os.path.exists(wal_path):
                os.remove(wal_path)
        print("[OK] 损坏数据库已删除，应用启动时将自动创建新数据库")
    except Exception as e:
        print(f"[ERROR] 删除损坏数据库失败: {e}, 请手动删除: {db_path}")


def _setup_fallback_connection_reset_handler():
    """回退方案：简单的 loop 异常处理器。

    当 win_proactor_fix 模块导入失败时使用。此方法仅设置当前运行中
    或缓存的 loop 的处理器，不如 win_proactor_fix 的 Policy 级别方案全面。
    """
    import asyncio

    def _silence_connection_reset(loop, context):
        exc = context.get("exception")
        if isinstance(exc, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
            return
        message = context.get("message", "")
        if isinstance(message, str) and "connection reset" in message.lower():
            return
        loop.default_exception_handler(context)

    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(_silence_connection_reset)
        print("[OK] 回退 ConnectionResetError 处理器已设置 (runtime loop)")
    except RuntimeError:
        # 无运行时 loop — 在最后一个可能的时机设置
        pass


def main():
    import uvicorn

    print("=" * 50)
    print("军队乡村振兴管理系统 - 后端服务启动中")
    print("=" * 50)

    # ── 预检：Python 架构 + VC++ 运行时 DLL ──
    _check_python_arch()
    _check_vcruntime()

    # ── 关键修复：Windows ProactorEventLoop ConnectionResetError ──
    # 必须在任何 asyncio 操作之前应用，使用三层纵深防御：
    #   Layer 1: Monkey-patch ProactorBasePipeTransport._call_connection_lost
    #   Layer 2: 替换全局 EventLoopPolicy，所有新 loop 自动继承异常处理器
    #   Layer 3: 对当前运行时 loop 设置异常处理器
    # 修复后 uvicorn 创建的每个事件循环都自动包含安全处理器。
    if sys.platform == "win32":
        try:
            from app.utils.win_proactor_fix import apply_windows_proactor_fix

            applied = apply_windows_proactor_fix()
            if applied:
                print("[OK] Windows ProactorEventLoop ConnectionResetError 修复已应用")
        except Exception as e:
            print(f"[WARN] ProactorEventLoop 修复应用失败: {e}")
            # 回退：设置简单的异常处理器作为最低限度保护
            _setup_fallback_connection_reset_handler()

    _ensure_dirs()
    from app.utils.runtime_secrets import ensure_runtime_secrets  # noqa: E402
    ensure_runtime_secrets()
    _check_database_integrity()

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))

    # 检查端口可用性（仅作为诊断信息，不阻止启动）
    if not _check_port_available(host, port):
        print(f"  提示：端口 {port} 被占用，服务可能无法正常监听")
        print("  请关闭占用该端口的程序后重试")

    print(f"\n正在启动后端服务: http://{host}:{port}")
    print(f"API 文档: http://{host}:{port}/docs")

    # ── 麒麟模式：延迟自动打开系统浏览器 ──
    if os.environ.get("KYLIN_MODE", "false").lower() == "true":
        _auto_open_browser(host, port)

    # PyInstaller 环境下必须使用直接引用的 app 对象，
    # 字符串 "app.main:app" 依赖 importlib 动态导入，在冻结环境中会失败。
    from app.main import app  # noqa: E402

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )


def _auto_open_browser(host: str, port: int):
    """麒麟模式：延迟 3 秒后自动打开系统浏览器。

    优先使用 webbrowser 标准库，失败时回退到 xdg-open。
    仅在 KYLIN_MODE=true 时由 main() 调用。
    """
    import subprocess
    import threading
    import time
    import webbrowser

    def _open():
        time.sleep(3)  # 等待 Uvicorn 完成启动
        url = f"http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}"
        print(f"[Kylin] 正在打开浏览器: {url}")
        try:
            webbrowser.open(url)
            return
        except Exception as e:
            print(f"[Kylin] webbrowser.open 失败: {e}，尝试 xdg-open...")

        try:
            subprocess.Popen(["xdg-open", url], start_new_session=True)
        except Exception as e2:
            print(f"[Kylin] xdg-open 也不可用: {e2}")
            print(f"[Kylin] 请手动打开浏览器访问: {url}")

    threading.Thread(target=_open, daemon=True).start()


if __name__ == "__main__":
    main()
