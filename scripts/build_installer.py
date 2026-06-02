#!/usr/bin/env python3
"""
军队乡村振兴管理系统 - 安装程序自动化构建脚本

用法:
    python scripts/build_installer.py --platform windows   # 构建 Windows NSIS 安装程序
    python scripts/build_installer.py --platform linux      # 构建 Linux/麒麟V10 deb 包
    python scripts/build_installer.py --platform all        # 构建全部平台

构建流程:
    1. 构建前端 (npm run build)
    2. PyInstaller 打包后端为单文件可执行程序
    3. 复制后端产物到 dist/backend/<platform>/
    4. electron-builder 打包为安装程序

前置条件:
    - Node.js >= 18, npm >= 9
    - Python >= 3.10, pip
    - PyInstaller (`pip install pyinstaller`)
    - electron, electron-builder (`npm install` in project root)

版本: 1.0.4
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── 路径常量 ───
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"
DIST_DIR = PROJECT_ROOT / "dist"
BACKEND_DIST_WIN = DIST_DIR / "backend" / "windows"
BACKEND_DIST_LINUX = DIST_DIR / "backend" / "linux"
BACKEND_DIST_LINUX_ARM64 = DIST_DIR / "backend" / "linux-arm64"
SPEC_FILE = BACKEND_DIR / "military-rural-backend.spec"
BUILD_LOG_FILE = DIST_DIR / "build.log"

# ─── 日志工具 ───
_log_lines: list[str] = []


def log(msg: str, level: str = "INFO"):
    """输出日志并记录到内存"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    _log_lines.append(line)


def save_build_log():
    """保存构建日志到文件"""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(BUILD_LOG_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(_log_lines))
        log(f"构建日志已保存: {BUILD_LOG_FILE}")
    except Exception as e:
        print(f"[WARN] 保存构建日志失败: {e}")


def run_command(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> bool:
    """执行命令并打印输出，返回是否成功"""
    cmd_str = " ".join(str(c) for c in cmd)
    log(f"执行: {cmd_str}")

    merged_env = {**os.environ, **(env or {})}
    # Windows 上 npx/npm 是 .cmd 文件，必须通过 shell=True 执行
    use_shell = platform.system().lower() == "windows"
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=merged_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,  # 10 分钟超时
            shell=use_shell,
        )
        if result.stdout.strip():
            for line in result.stdout.strip().split("\n")[-20:]:
                log(f"  stdout: {line}")
        if result.stderr.strip():
            for line in result.stderr.strip().split("\n")[-10:]:
                log(f"  stderr: {line}", "WARN")
        if result.returncode != 0:
            log(f"命令失败 (exit={result.returncode}): {cmd_str}", "ERROR")
            return False
        return True
    except subprocess.TimeoutExpired:
        log(f"命令超时: {cmd_str}", "ERROR")
        return False
    except Exception as e:
        log(f"命令执行异常: {e}", "ERROR")
        return False


# ─── 构建步骤 ───

def check_prerequisites() -> bool:
    """检查构建前置条件"""
    log("=== 检查构建前置条件 ===")
    ok = True

    # Node.js
    if not shutil.which("node"):
        log("未找到 node，请安装 Node.js >= 18", "ERROR")
        ok = False
    else:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True)
        log(f"Node.js 版本: {r.stdout.strip()}")

    # npm
    if not shutil.which("npm"):
        log("未找到 npm", "ERROR")
        ok = False

    # Python
    log(f"Python 版本: {sys.version}")

    # PyInstaller
    try:
        import PyInstaller
        log(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        log("未安装 PyInstaller，请运行: pip install pyinstaller", "ERROR")
        ok = False

    # electron (通过 npx)
    if not (PROJECT_ROOT / "node_modules" / "electron").exists():
        log("未安装 electron，请在项目根目录运行: npm install", "ERROR")
        ok = False

    # spec 文件
    if not SPEC_FILE.exists():
        log(f"PyInstaller spec 文件不存在: {SPEC_FILE}", "ERROR")
        ok = False

    return ok


def build_frontend() -> bool:
    """步骤1: 构建前端"""
    log("=== 步骤1: 构建前端 ===")

    if not (FRONTEND_DIR / "package.json").exists():
        log(f"前端目录不存在: {FRONTEND_DIR}", "ERROR")
        return False

    # 确保前端依赖已安装
    if not (FRONTEND_DIR / "node_modules").exists():
        log("安装前端依赖...")
        if not run_command(["npm", "install", "--legacy-peer-deps"], cwd=FRONTEND_DIR):
            return False

    # 构建
    log("构建前端...")
    if not run_command(["npm", "run", "build"], cwd=FRONTEND_DIR):
        return False

    # 验证产物
    dist_index = FRONTEND_DIR / "dist" / "index.html"
    if not dist_index.exists():
        log(f"前端构建产物不存在: {dist_index}", "ERROR")
        return False

    file_count = sum(1 for _ in (FRONTEND_DIR / "dist").rglob("*") if _.is_file())
    log(f"前端构建完成: {file_count} 个文件")
    return True


def build_backend(target_platform: str) -> bool:
    """步骤2: PyInstaller 打包后端"""
    log(f"=== 步骤2: PyInstaller 打包后端 (目标: {target_platform}) ===")

    current_os = platform.system().lower()
    is_cross = (target_platform == "linux" and current_os == "windows") or \
               (target_platform == "windows" and current_os != "windows")

    if is_cross:
        log(f"⚠️  当前系统 ({current_os}) 无法交叉编译 {target_platform} 后端。", "WARN")
        log("请在目标系统上运行此脚本的后端构建步骤。", "WARN")
        log("跳过后端打包，请确保手动将后端可执行文件放入正确目录。")
        return True

    # 清理旧的 PyInstaller 产物
    pyinstaller_dist = BACKEND_DIR / "dist"
    pyinstaller_build = BACKEND_DIR / "build"
    if pyinstaller_dist.exists():
        shutil.rmtree(pyinstaller_dist, ignore_errors=True)
    if pyinstaller_build.exists():
        shutil.rmtree(pyinstaller_build, ignore_errors=True)

    # 执行 PyInstaller
    log("执行 PyInstaller 打包...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE),
    ]
    if not run_command(cmd, cwd=BACKEND_DIR):
        return False

    # 确定产物路径
    is_win = current_os == "windows"
    exe_name = "military-rural-backend.exe" if is_win else "military-rural-backend"
    exe_path = pyinstaller_dist / exe_name

    if not exe_path.exists():
        log(f"后端可执行文件不存在: {exe_path}", "ERROR")
        return False

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    log(f"后端可执行文件大小: {size_mb:.1f} MB")

    if size_mb < 1:
        log("后端可执行文件过小 (<1MB)，可能打包失败", "ERROR")
        return False

    # 复制到目标目录
    target_dir = BACKEND_DIST_WIN if is_win else BACKEND_DIST_LINUX
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / exe_name

    # 同时复制到 arm64 目录（如果当前架构是 aarch64）
    current_arch = platform.machine().lower()
    if not is_win and current_arch in ("aarch64", "arm64"):
        target_dir = BACKEND_DIST_LINUX_ARM64
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / exe_name

    shutil.copy2(str(exe_path), str(target_path))
    log(f"后端产物已复制到: {target_path}")

    return True


def build_electron_installer(target_platform: str, arch: str = "x64") -> bool:
    """步骤3: electron-builder 打包安装程序"""
    log(f"=== 步骤3: electron-builder 打包 ({target_platform}, {arch}) ===")

    # 确保根目录依赖已安装
    if not (PROJECT_ROOT / "node_modules").exists():
        log("安装根目录依赖...")
        if not run_command(["npm", "install"], cwd=PROJECT_ROOT):
            return False

    # 验证必要的资源文件
    frontend_dist = FRONTEND_DIR / "dist"
    if not (frontend_dist / "index.html").exists():
        log("前端构建产物不存在，请先执行前端构建", "ERROR")
        return False

    if target_platform == "windows":
        backend_check = BACKEND_DIST_WIN / "military-rural-backend.exe"
        if not backend_check.exists():
            log(f"Windows 后端可执行文件不存在: {backend_check}", "ERROR")
            log("请先在 Windows 上完成后端打包步骤。")
            return False

        log("构建 Windows NSIS 安装程序...")
        cmd = ["npx", "electron-builder", "--win", "nsis", "--x64"]
        if not run_command(cmd, cwd=PROJECT_ROOT):
            return False

    elif target_platform == "linux":
        # arm64 构建: 将 linux-arm64 后端复制到 linux/ 目录（electron-builder 读取固定路径）
        if arch == "arm64":
            arm64_backend = BACKEND_DIST_LINUX_ARM64 / "military-rural-backend"
            linux_backend = BACKEND_DIST_LINUX / "military-rural-backend"
            if arm64_backend.exists():
                BACKEND_DIST_LINUX.mkdir(parents=True, exist_ok=True)
                # 备份 x64 后端（如果存在）
                if linux_backend.exists():
                    backup_path = BACKEND_DIST_LINUX / "military-rural-backend.x64.bak"
                    shutil.copy2(str(linux_backend), str(backup_path))
                    log(f"x64 后端已备份到: {backup_path}")
                shutil.copy2(str(arm64_backend), str(linux_backend))
                log(f"arm64 后端已复制到: {linux_backend}")
            else:
                log(f"arm64 后端不存在: {arm64_backend}", "ERROR")
                log("请先在 aarch64 环境中运行 scripts/build-backend-aarch64.sh")
                return False

        backend_check = BACKEND_DIST_LINUX / "military-rural-backend"
        if not backend_check.exists():
            log(f"Linux 后端可执行文件不存在: {backend_check}", "ERROR")
            log("请先在 Linux/麒麟V10 上完成后端打包步骤。")
            return False

        arch_flag = f"--{arch}"
        log(f"构建 Linux deb 安装包 ({arch})（兼容麒麟V10）...")
        cmd = ["npx", "electron-builder", "--linux", "deb", arch_flag]
        if not run_command(cmd, cwd=PROJECT_ROOT):
            return False

        # arm64 构建后恢复 x64 后端
        if arch == "arm64":
            backup_path = BACKEND_DIST_LINUX / "military-rural-backend.x64.bak"
            if backup_path.exists():
                shutil.copy2(str(backup_path), str(BACKEND_DIST_LINUX / "military-rural-backend"))
                backup_path.unlink()
                log("x64 后端已恢复")

    else:
        log(f"不支持的平台: {target_platform}", "ERROR")
        return False

    # 验证产物
    electron_dist = DIST_DIR / "electron"
    if electron_dist.exists():
        installers = list(electron_dist.glob("*.*"))
        if installers:
            log("已生成安装程序:")
            for f in installers:
                if f.is_file() and f.suffix in (".exe", ".deb", ".AppImage", ".yml", ".yaml"):
                    size_mb = f.stat().st_size / (1024 * 1024)
                    log(f"  {f.name} ({size_mb:.1f} MB)")
        else:
            log("electron-builder 产物目录为空", "WARN")
    else:
        log("electron-builder 产物目录不存在", "WARN")

    return True


def generate_build_report(target_platform: str, success: bool, elapsed: float):
    """生成构建报告"""
    log("=== 构建报告 ===")
    log(f"目标平台:   {target_platform}")
    log(f"构建结果:   {'✅ 成功' if success else '❌ 失败'}")
    log(f"构建耗时:   {elapsed:.0f} 秒")
    log(f"版本号:     {get_version()}")
    log(f"构建时间:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"构建环境:   {platform.system()} {platform.release()} ({platform.machine()})")
    log(f"Python:     {sys.version.split()[0]}")

    if success:
        log("")
        log("变更说明 (v1.0.4):")
        log("  1. [新增] 麒麟 V10 aarch64 DEB 安装包支持")
        log("  2. [修复] Electron 版本锁定 28.3.3，确保构建可重复")
        log("  3. [修复] 14项问题修复与功能增强（日期验证/报表模板/审计权限等）")
        log("  4. [修复] 系统问题全面修复（安全/架构/代码质量）")
        log("  5. [构建] 新增 arm64 构建脚本和 DEB 后置脚本")
        log("")
        log("验证清单:")
        log("  [ ] 安装过程无错误中断")
        log("  [ ] 安装完成后系统正常启动（后端进程 + 前端界面）")
        log("  [ ] 用户登录功能正常（admin 账户，无 405 或其他登录错误）")
        log("  [ ] 核心功能模块可正常访问（组织管理、项目管理、资金管理等）")
        log("  [ ] 重复以上验证至少 3 次")


def get_version() -> str:
    """从 package.json 读取版本号"""
    try:
        pkg = json.loads((PROJECT_ROOT / "package.json").read_text(encoding="utf-8"))
        return pkg.get("version", "unknown")
    except Exception:
        return "unknown"


# ─── 主流程 ───

def main():
    parser = argparse.ArgumentParser(description="军队乡村振兴管理系统 - 安装程序构建工具")
    parser.add_argument(
        "--platform",
        choices=["windows", "linux", "all"],
        default="windows",
        help="目标平台 (default: windows)",
    )
    parser.add_argument(
        "--arch",
        choices=["x64", "arm64"],
        default="x64",
        help="目标架构 (default: x64)，仅对 Linux 平台有效",
    )
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="跳过前端构建（使用已有产物）",
    )
    parser.add_argument(
        "--skip-backend",
        action="store_true",
        help="跳过后端打包（使用已有产物）",
    )
    parser.add_argument(
        "--skip-electron",
        action="store_true",
        help="仅构建前端+后端，跳过 electron-builder 打包",
    )
    args = parser.parse_args()

    start_time = time.time()
    platforms = ["windows", "linux"] if args.platform == "all" else [args.platform]

    log("=" * 60)
    log("军队乡村振兴管理系统 - 安装程序构建")
    log(f"版本: {get_version()}")
    log(f"目标平台: {', '.join(platforms)}")
    log("=" * 60)

    # 前置检查
    if not check_prerequisites():
        log("前置条件检查未通过，构建中止", "ERROR")
        save_build_log()
        sys.exit(1)

    # 构建前端（所有平台共享）
    if not args.skip_frontend:
        if not build_frontend():
            log("前端构建失败，构建中止", "ERROR")
            save_build_log()
            sys.exit(1)
    else:
        log("跳过前端构建（使用已有产物）")

    # 对每个目标平台执行后端打包 + electron 打包
    all_success = True
    for plat in platforms:
        log(f"\n{'=' * 40}")
        log(f"构建目标: {plat}")
        log(f"{'=' * 40}")

        if not args.skip_backend:
            if not build_backend(plat):
                log(f"{plat} 后端打包失败", "ERROR")
                all_success = False
                continue
        else:
            log("跳过后端打包（使用已有产物）")

        if not args.skip_electron:
            arch = args.arch if plat == "linux" else "x64"
            if not build_electron_installer(plat, arch=arch):
                log(f"{plat} ({arch}) electron-builder 打包失败", "ERROR")
                all_success = False
                continue
        else:
            log("跳过 electron-builder 打包")

    elapsed = time.time() - start_time
    generate_build_report(args.platform, all_success, elapsed)
    save_build_log()

    if not all_success:
        sys.exit(1)

    log("\n✅ 构建完成！")


if __name__ == "__main__":
    main()
