"""
麒麟 ARM64 完整构建脚本
使用 Docker 在 ARM64 环境中从源码构建
"""

import os
import sys
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DOCKERFILE = ROOT_DIR / "Dockerfile.kylin-arm64-full"
IMAGE_NAME = "military-rural-kylin-builder:arm64"
CONTAINER_NAME = "kylin-arm64-builder"

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def check_docker():
    """检查 Docker 环境"""
    print_header("检查 Docker 环境")

    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        print(f"Docker 版本: {result.stdout.strip()}")

        # 检查 buildx
        result = subprocess.run(["docker", "buildx", "version"], capture_output=True, text=True)
        print(f"Buildx 版本: {result.stdout.strip()}")

        print("[PASS] Docker 环境正常")
        return True
    except Exception as e:
        print(f"[FAIL] Docker 检查失败: {e}")
        return False

def setup_buildx():
    """设置 buildx 多架构支持"""
    print_header("设置 Buildx")

    try:
        # 创建新的 builder
        subprocess.run([
            "docker", "buildx", "create",
            "--name", "kylin-arm64-builder",
            "--use"
        ], capture_output=True)

        # 启动 builder
        subprocess.run([
            "docker", "buildx", "inspect",
            "--bootstrap"
        ], capture_output=True)

        print("[PASS] Buildx 设置完成")
        return True
    except Exception as e:
        print(f"[WARN] Buildx 设置: {e}")
        return True  # 不阻塞

def build_image():
    """构建 Docker 镜像"""
    print_header("构建 ARM64 构建镜像")

    print("这将需要较长时间（10-30分钟），请耐心等待...")
    print(f"Dockerfile: {DOCKERFILE}")

    cmd = [
        "docker", "buildx", "build",
        "--platform", "linux/arm64",
        "-f", str(DOCKERFILE),
        "-t", IMAGE_NAME,
        "--load",  # 加载到本地
        str(ROOT_DIR)
    ]

    print(f"\n执行命令: {' '.join(cmd)}\n")

    try:
        # 实时输出构建日志
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            print(line, end='')

        process.wait()

        if process.returncode == 0:
            print("\n[PASS] 镜像构建成功")
            return True
        else:
            print(f"\n[FAIL] 镜像构建失败，退出码: {process.returncode}")
            return False

    except Exception as e:
        print(f"\n[FAIL] 构建过程出错: {e}")
        return False

def run_build():
    """运行构建容器"""
    print_header("运行构建容器")

    # 清理旧容器
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)

    # 创建输出目录
    output_dir = ROOT_DIR / "dist" / "kylin-arm64"
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "docker", "run",
        "--name", CONTAINER_NAME,
        "--platform", "linux/arm64",
        "-v", f"{output_dir}:/output",
        IMAGE_NAME
    ]

    print(f"执行命令: {' '.join(cmd)}\n")

    try:
        # 实时输出构建日志
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            print(line, end='')

        process.wait()

        if process.returncode == 0:
            print("\n[PASS] 构建执行成功")
            return True
        else:
            print(f"\n[FAIL] 构建执行失败，退出码: {process.returncode}")
            return False

    except Exception as e:
        print(f"\n[FAIL] 执行过程出错: {e}")
        return False

def extract_artifacts():
    """提取构建产物"""
    print_header("提取构建产物")

    output_dir = ROOT_DIR / "dist" / "kylin-arm64"

    try:
        # 从容器复制 DEB 包
        subprocess.run([
            "docker", "cp",
            f"{CONTAINER_NAME}:/build/dist/electron/",
            str(output_dir)
        ], check=True)

        # 列出产物
        deb_files = list(output_dir.glob("**/*.deb"))

        if deb_files:
            print("[PASS] 构建产物已提取:")
            for deb in deb_files:
                size_mb = deb.stat().st_size / (1024 * 1024)
                print(f"  - {deb.name} ({size_mb:.1f} MB)")
            return True
        else:
            print("[FAIL] 未找到 DEB 包")
            return False

    except Exception as e:
        print(f"[FAIL] 提取产物失败: {e}")
        return False

def verify_package():
    """验证 DEB 包"""
    print_header("验证 DEB 包")

    output_dir = ROOT_DIR / "dist" / "kylin-arm64"
    deb_files = list(output_dir.glob("**/*.deb"))

    if not deb_files:
        print("[FAIL] 未找到 DEB 包")
        return False

    deb_file = deb_files[0]
    print(f"验证文件: {deb_file}")

    # 在容器中验证
    cmd = [
        "docker", "run", "--rm",
        "--platform", "linux/arm64",
        "-v", f"{deb_file}:/package.deb",
        "ubuntu:20.04",
        "bash", "-c",
        "dpkg-deb --info /package.deb && dpkg-deb --contents /package.deb | head -20"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)

        if "Architecture: arm64" in result.stdout:
            print("\n[PASS] 架构验证通过: ARM64")
            return True
        else:
            print("\n[FAIL] 架构验证失败")
            return False

    except Exception as e:
        print(f"[FAIL] 验证失败: {e}")
        return False

def cleanup():
    """清理资源"""
    print_header("清理资源")

    # 删除容器
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)

    print("[PASS] 清理完成")

def main():
    """主函数"""
    print_header("麒麟 ARM64 完整构建")

    print("\n警告: 此构建过程将需要 10-30 分钟")
    print("将在 ARM64 环境中从源码完整构建应用\n")

    response = input("是否继续? (y/n): ")
    if response.lower() != 'y':
        print("已取消")
        return 0

    try:
        # 1. 检查环境
        if not check_docker():
            return 1

        # 2. 设置 buildx
        setup_buildx()

        # 3. 构建镜像
        if not build_image():
            return 1

        # 4. 运行构建
        if not run_build():
            return 1

        # 5. 提取产物
        if not extract_artifacts():
            return 1

        # 6. 验证包
        if not verify_package():
            return 1

        # 7. 清理
        cleanup()

        print_header("[PASS] 构建完成")
        print("\n输出目录: dist/kylin-arm64/")

        return 0

    except KeyboardInterrupt:
        print("\n\n[WARN] 用户中断")
        cleanup()
        return 1
    except Exception as e:
        print(f"\n[FAIL] 构建失败: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        return 1

if __name__ == "__main__":
    sys.exit(main())
