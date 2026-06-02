"""
军队乡村振兴管理系统 - 后端打包脚本
使用 PyInstaller 将 FastAPI 后端打包成独立可执行文件
支持 Windows x64 和 Linux ARM64
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
DIST_DIR = ROOT_DIR / "dist" / "backend"

def clean_dist():
    """清理旧的构建文件"""
    print("清理旧的构建文件...")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    build_dir = BACKEND_DIR / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)

    print("[PASS] 清理完成")

def install_dependencies():
    """安装打包依赖"""
    print("安装打包依赖...")
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "pyinstaller==6.3.0",
        "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
    ], check=True)
    print("[PASS] 依赖安装完成")

def create_spec_file():
    """创建 PyInstaller spec 文件"""
    print("创建 spec 文件...")

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 收集所有数据文件
datas = []
datas += collect_data_files('fastapi')
datas += collect_data_files('uvicorn')
datas += collect_data_files('pydantic')
datas += collect_data_files('sqlalchemy')

# 添加应用代码
datas += [('app', 'app')]

# 收集隐藏导入
hiddenimports = []
hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('uvicorn.logging')
hiddenimports += collect_submodules('uvicorn.loops')
hiddenimports += collect_submodules('uvicorn.protocols')
hiddenimports += collect_submodules('uvicorn.lifespan')
hiddenimports += collect_submodules('sqlalchemy')
hiddenimports += collect_submodules('sqlalchemy.ext')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('fastapi')
hiddenimports += [
    'passlib.handlers.bcrypt',
    'jose',
    'email_validator',
    'multipart',
    'aiosqlite',
    'openpyxl',
    'xlsxwriter',
    'pandas',
    'reportlab',
    'mammoth',
    'docx',
    'PIL',
    'PIL._imaging',
    'magic',
    'structlog',
    'apscheduler',
    'apscheduler.schedulers.background',
    'apscheduler.triggers.cron',
    'apscheduler.triggers.interval',
    'apscheduler.executors.pool',
    'apscheduler.jobstores.memory',
]

# 排除不需要的模块
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    'pytest',
    'IPython',
    'jupyter',
]

a = Analysis(
    ['start.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='military-rural-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='military-rural-backend',
)
'''

    spec_file = BACKEND_DIR / "backend.spec"
    spec_file.write_text(spec_content, encoding='utf-8')
    print(f"[PASS] Spec 文件已创建: {spec_file}")
    return spec_file

def build_backend(platform_name):
    """构建后端可执行文件"""
    print(f"\n开始构建 {platform_name} 后端...")

    spec_file = create_spec_file()

    # 运行 PyInstaller
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    print(f"执行命令: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=BACKEND_DIR, check=True)

    # 移动构建产物到目标目录
    source_dist = BACKEND_DIR / "dist" / "military-rural-backend"
    target_dist = DIST_DIR / platform_name

    if target_dist.exists():
        shutil.rmtree(target_dist)

    shutil.move(str(source_dist), str(target_dist))
    print(f"[PASS] 后端构建完成: {target_dist}")

    return target_dist

def verify_build(dist_path):
    """验证构建产物"""
    print(f"\n验证构建产物: {dist_path}")

    exe_name = "military-rural-backend.exe" if platform.system() == "Windows" else "military-rural-backend"
    exe_path = dist_path / exe_name

    if not exe_path.exists():
        print(f"[FAIL] 可执行文件不存在: {exe_path}")
        return False

    # 检查文件大小
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"  可执行文件大小: {size_mb:.1f} MB")

    if size_mb < 10:
        print(f"[FAIL] 文件大小异常（小于 10MB），可能构建失败")
        return False

    print("[PASS] 构建产物验证通过")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("军队乡村振兴管理系统 - 后端打包")
    print("=" * 60)

    # 检查当前平台
    current_platform = platform.system()
    current_arch = platform.machine()

    print(f"\n当前平台: {current_platform} {current_arch}")

    if current_platform == "Windows":
        platform_name = "windows"
    elif current_platform == "Linux":
        if "aarch64" in current_arch.lower() or "arm64" in current_arch.lower():
            platform_name = "linux-arm64"
        else:
            platform_name = "linux"
    else:
        print(f"[FAIL] 不支持的平台: {current_platform}")
        return 1

    try:
        # 1. 清理旧文件
        clean_dist()

        # 2. 安装依赖
        install_dependencies()

        # 3. 构建后端
        dist_path = build_backend(platform_name)

        # 4. 验证构建
        if not verify_build(dist_path):
            print("\n[FAIL] 构建验证失败")
            return 1

        print("\n" + "=" * 60)
        print("[PASS] 后端打包完成")
        print(f"输出目录: {dist_path}")
        print("=" * 60)

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
