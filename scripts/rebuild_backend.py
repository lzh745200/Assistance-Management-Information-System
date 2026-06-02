#!/usr/bin/env python3
"""
重新构建后端 - 修复登录404问题
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    print("=" * 60)
    print("重新构建后端 - 修复登录404问题")
    print("=" * 60)
    print()

    # 切换到backend目录
    backend_dir = Path(__file__).parent.parent / "backend"
    os.chdir(backend_dir)
    print(f"工作目录: {backend_dir}")
    print()

    # 检查虚拟环境
    venv_python = backend_dir / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print("[错误] 虚拟环境不存在")
        print(f"路径: {venv_python}")
        return 1

    print(f"[✓] 找到虚拟环境: {venv_python}")
    print()

    # 清理旧构建
    print("[1/3] 清理旧构建...")
    for dir_name in ["build", "dist"]:
        dir_path = backend_dir / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  已删除: {dir_name}/")
    print("[✓] 清理完成")
    print()

    # 运行PyInstaller
    print("[2/3] 运行 PyInstaller...")
    print("这可能需要几分钟时间，请耐心等待...")
    print()

    spec_file = backend_dir / "military-rural-backend-full.spec"
    cmd = [
        str(venv_python),
        "-m", "PyInstaller",
        str(spec_file),
        "--clean",
        "--noconfirm"
    ]

    print(f"命令: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            capture_output=False,
            text=True
        )

        if result.returncode != 0:
            print()
            print("[错误] PyInstaller 构建失败")
            return 1

    except Exception as e:
        print(f"[错误] 执行失败: {e}")
        return 1

    # 检查输出
    print()
    print("[3/3] 检查构建结果...")

    exe_file = backend_dir / "dist" / "military-rural-backend.exe"
    if not exe_file.exists():
        print("[错误] 未找到生成的可执行文件")
        print(f"预期路径: {exe_file}")
        return 1

    file_size = exe_file.stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    print(f"[✓] 后端可执行文件已生成")
    print(f"位置: {exe_file}")
    print(f"大小: {file_size:,} 字节 ({file_size_mb:.1f} MB)")
    print()

    print("=" * 60)
    print("构建完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("1. 测试新构建的后端: python scripts/test_backend.py")
    print("2. 或运行: scripts\\启动系统-调试模式.bat")
    print("3. 如果测试成功，更新安装包")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
