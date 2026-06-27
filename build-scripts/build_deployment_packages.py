"""
完整部署包构建脚本
构建 Windows .exe、ARM64 .deb 和 Docker 镜像
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

print("=" * 60)
print("帮扶管理信息系统 - 完整部署包构建")
print("=" * 60)

# 检查环境
print("\n[1] 环境检查")
print("-" * 60)

# 检查 Python 版本
python_version = sys.version_info
print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
if python_version.major != 3 or python_version.minor != 11:
    print("WARNING: 推荐使用 Python 3.11")

# 检查操作系统
os_type = platform.system()
print(f"操作系统: {os_type}")
print(f"架构: {platform.machine()}")

# 检查项目结构
project_root = Path.cwd()
print(f"项目根目录: {project_root}")

required_dirs = ['backend', 'frontend', 'scripts', 'docker']
for dir_name in required_dirs:
    dir_path = project_root / dir_name
    if dir_path.exists():
        print(f"  OK: {dir_name}/ 存在")
    else:
        print(f"  FAIL: {dir_name}/ 不存在")

# 检查关键文件
print("\n[2] 关键文件检查")
print("-" * 60)

key_files = [
    'backend/requirements.txt',
    'frontend/package.json',
    'package.json',
    'docker/Dockerfile.production',
]

for file_path in key_files:
    full_path = project_root / file_path
    if full_path.exists():
        print(f"  OK: {file_path}")
    else:
        print(f"  FAIL: {file_path} 不存在")

# 检查构建脚本
print("\n[3] 构建脚本检查")
print("-" * 60)

build_scripts = [
    'build-scripts/build_windows_complete.bat',
    'build-scripts/build-linux-arm64.sh',
]

for script in build_scripts:
    script_path = project_root / script
    if script_path.exists():
        print(f"  OK: {script}")
    else:
        print(f"  MISSING: {script}")

# 检查 Docker
print("\n[4] Docker 检查")
print("-" * 60)

try:
    result = subprocess.run(['docker', '--version'],
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"  OK: {result.stdout.strip()}")
    else:
        print("  FAIL: Docker 未安装或无法运行")
except Exception as e:
    print(f"  FAIL: Docker 检查失败 - {e}")

# 检查 Node.js
print("\n[5] Node.js 检查")
print("-" * 60)

try:
    result = subprocess.run(['node', '--version'],
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"  OK: Node.js {result.stdout.strip()}")
    else:
        print("  FAIL: Node.js 未安装")
except Exception as e:
    print(f"  FAIL: Node.js 检查失败 - {e}")

try:
    result = subprocess.run(['npm', '--version'],
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"  OK: npm {result.stdout.strip()}")
except Exception as e:
    print(f"  FAIL: npm 检查失败 - {e}")

print("\n" + "=" * 60)
print("环境检查完成")
print("=" * 60)
