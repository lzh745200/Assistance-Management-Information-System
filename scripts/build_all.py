"""
军队乡村振兴管理系统 - 完整打包脚本
构建 Windows x64 和麒麟 ARM64 安装包
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
BACKEND_DIR = ROOT_DIR / "backend"
DIST_DIR = ROOT_DIR / "dist"
SCRIPTS_DIR = ROOT_DIR / "scripts"

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def run_command(cmd, cwd=None, check=True):
    """运行命令"""
    print(f"执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result

def check_environment():
    """检查构建环境"""
    print_header("检查构建环境")

    # 检查 Python
    python_version = sys.version_info
    print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version < (3, 11):
        print("[FAIL] Python 版本过低，需要 3.11+")
        return False

    # 检查 Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, shell=True)
        print(f"Node.js 版本: {result.stdout.strip()}")
    except FileNotFoundError:
        print("[FAIL] 未找到 Node.js")
        return False

    # 检查 npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, shell=True)
        print(f"npm 版本: {result.stdout.strip()}")
    except FileNotFoundError:
        print("[FAIL] 未找到 npm")
        return False

    print("[PASS] 环境检查通过")
    return True

def build_frontend():
    """构建前端"""
    print_header("构建前端")

    # 安装依赖
    print("安装前端依赖...")
    run_command(["npm", "ci"], cwd=FRONTEND_DIR)

    # 构建
    print("构建前端...")
    run_command(["npm", "run", "build"], cwd=FRONTEND_DIR)

    # 验证构建产物
    dist_path = FRONTEND_DIR / "dist"
    if not dist_path.exists():
        print("[FAIL] 前端构建失败")
        return False

    index_html = dist_path / "index.html"
    if not index_html.exists():
        print("[FAIL] 前端构建产物不完整")
        return False

    print(f"[PASS] 前端构建完成: {dist_path}")
    return True

def build_backend():
    """构建后端"""
    print_header("构建后端")

    # 运行后端打包脚本
    build_script = SCRIPTS_DIR / "build_backend.py"
    run_command([sys.executable, str(build_script)])

    # 验证构建产物
    current_platform = platform.system()
    if current_platform == "Windows":
        platform_name = "windows"
        exe_name = "military-rural-backend.exe"
    else:
        platform_name = "linux-arm64"
        exe_name = "military-rural-backend"

    backend_dist = DIST_DIR / "backend" / platform_name
    exe_path = backend_dist / exe_name

    if not exe_path.exists():
        print(f"[FAIL] 后端构建失败: {exe_path}")
        return False

    print(f"[PASS] 后端构建完成: {backend_dist}")
    return True

def prepare_resources():
    """准备资源文件"""
    print_header("准备资源文件")

    # 创建初始数据库
    db_source = BACKEND_DIR / "data" / "rural_revitalization.db"
    db_target = ROOT_DIR / "resources" / "database"
    db_target.mkdir(parents=True, exist_ok=True)

    if db_source.exists():
        shutil.copy2(db_source, db_target / "rural_revitalization.db")
        print(f"[PASS] 数据库文件已复制")
    else:
        print("[WARN] 数据库文件不存在，将使用空数据库")

    print("[PASS] 资源准备完成")
    return True

def build_electron():
    """构建 Electron 应用"""
    print_header("构建 Electron 应用")

    # 安装根目录依赖
    print("安装 Electron 依赖...")
    run_command(["npm", "install"], cwd=ROOT_DIR)

    # 根据当前平台构建
    current_platform = platform.system()
    current_arch = platform.machine()

    if current_platform == "Windows":
        print("构建 Windows x64 安装包...")
        run_command(["npm", "run", "build:win"], cwd=ROOT_DIR)
    elif current_platform == "Linux":
        if "aarch64" in current_arch.lower() or "arm64" in current_arch.lower():
            print("构建麒麟 ARM64 安装包...")
            run_command(["npm", "run", "build:linux-arm64"], cwd=ROOT_DIR)
        else:
            print("构建 Linux x64 安装包...")
            run_command(["npm", "run", "build:linux"], cwd=ROOT_DIR)
    else:
        print(f"[FAIL] 不支持的平台: {current_platform}")
        return False

    # 验证构建产物
    electron_dist = DIST_DIR / "electron"
    if not electron_dist.exists() or not list(electron_dist.glob("*")):
        print("[FAIL] Electron 构建失败")
        return False

    print(f"[PASS] Electron 构建完成: {electron_dist}")
    return True

def list_output_files():
    """列出生成的文件"""
    print_header("构建产物")

    electron_dist = DIST_DIR / "electron"
    if electron_dist.exists():
        for file in electron_dist.iterdir():
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  {file.name} ({size_mb:.1f} MB)")

def main():
    """主函数"""
    print_header("军队乡村振兴管理系统 - 完整打包")

    current_platform = platform.system()
    current_arch = platform.machine()
    print(f"当前平台: {current_platform} {current_arch}")

    try:
        # 1. 检查环境
        if not check_environment():
            return 1

        # 2. 构建前端
        if not build_frontend():
            return 1

        # 3. 构建后端
        if not build_backend():
            return 1

        # 4. 准备资源
        if not prepare_resources():
            return 1

        # 5. 构建 Electron 应用
        if not build_electron():
            return 1

        # 6. 列出构建产物
        list_output_files()

        print_header("[PASS] 打包完成")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] 构建失败: {e}")
        return 1
    except Exception as e:
        print(f"\n[FAIL] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
