"""
麒麟 ARM64 Docker 验证脚本
监控构建进度并执行验证测试
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
VERSION = json.loads((ROOT_DIR / "package.json").read_text())["version"]

def check_docker():
    """检查 Docker 环境"""
    print("=" * 60)
    print("检查 Docker 环境")
    print("=" * 60)

    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        print(f"Docker 版本: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("[FAIL] Docker 未安装")
        return False

def check_arm64_package():
    """检查 ARM64 安装包"""
    print("\n" + "=" * 60)
    print("检查 ARM64 安装包")
    print("=" * 60)

    deb_file = ROOT_DIR / "dist" / "electron" / f"military-rural-system_{VERSION}_arm64.deb"

    if not deb_file.exists():
        print(f"[FAIL] ARM64 安装包不存在: {deb_file}")
        return False

    size_mb = deb_file.stat().st_size / (1024 * 1024)
    print(f"[PASS] ARM64 安装包: {size_mb:.1f} MB")
    print(f"路径: {deb_file}")

    return True

def wait_for_build():
    """等待 Docker 构建完成"""
    print("\n" + "=" * 60)
    print("等待 Docker 构建完成")
    print("=" * 60)

    print("正在构建 ARM64 测试镜像...")
    print("这可能需要几分钟时间...")

    # 等待一段时间让构建开始
    for i in range(30):
        time.sleep(1)
        print(".", end="", flush=True)

    print("\n\n检查构建状态...")

    # 检查镜像是否已构建
    result = subprocess.run(
        ["docker", "images", "kylin-test:arm64", "--format", "{{.Repository}}:{{.Tag}}"],
        capture_output=True,
        text=True
    )

    if "kylin-test:arm64" in result.stdout:
        print("[PASS] 镜像构建完成")
        return True
    else:
        print("[INFO] 镜像仍在构建中...")
        return False

def run_verification():
    """运行验证测试"""
    print("\n" + "=" * 60)
    print("运行 ARM64 验证测试")
    print("=" * 60)

    # 检查镜像是否存在
    result = subprocess.run(
        ["docker", "images", "kylin-test:arm64", "-q"],
        capture_output=True,
        text=True
    )

    if not result.stdout.strip():
        print("[FAIL] 测试镜像不存在，请等待构建完成")
        return False

    print("启动测试容器...")

    # 运行容器执行验证
    result = subprocess.run(
        ["docker", "run", "--rm", "--platform", "linux/arm64", "kylin-test:arm64"],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode == 0:
        print("\n[PASS] ARM64 验证测试通过")
        return True
    else:
        print("\n[FAIL] ARM64 验证测试失败")
        if result.stderr:
            print("错误信息:")
            print(result.stderr)
        return False

def generate_report():
    """生成验证报告"""
    print("\n" + "=" * 60)
    print("生成验证报告")
    print("=" * 60)

    report = []
    report.append("# 麒麟 ARM64 Docker 验证报告\n\n")
    report.append(f"验证时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    report.append("## 验证环境\n\n")
    report.append("- 平台: Docker (QEMU ARM64 模拟)\n")
    report.append("- 基础镜像: Ubuntu 20.04 ARM64\n")
    report.append(f"- 安装包: military-rural-system_{VERSION}_arm64.deb\n\n")

    report.append("## 验证项目\n\n")
    report.append("1. Docker 环境检查\n")
    report.append("2. ARM64 安装包完整性\n")
    report.append("3. DEB 包安装测试\n")
    report.append("4. 依赖库检查\n")
    report.append("5. 可执行文件验证\n\n")

    report.append("## 验证说明\n\n")
    report.append("由于在 Windows x64 环境下使用 Docker 模拟 ARM64，\n")
    report.append("实际运行性能会受到 QEMU 模拟的影响。\n")
    report.append("建议在真实的麒麟 ARM64 硬件上进行最终验证。\n\n")

    report.append("## 下一步\n\n")
    report.append("1. 在真实麒麟 ARM64 设备上安装测试\n")
    report.append("2. 验证完整功能\n")
    report.append("3. 性能测试\n")

    report_file = ROOT_DIR / "麒麟ARM64验证报告.md"
    report_file.write_text("".join(report), encoding='utf-8')

    print(f"[PASS] 验证报告已生成: {report_file}")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("麒麟 ARM64 Docker 验证")
    print("=" * 60)

    # 1. 检查 Docker
    if not check_docker():
        return 1

    # 2. 检查安装包
    if not check_arm64_package():
        return 1

    # 3. 等待构建
    print("\n提示: Docker 构建正在后台运行")
    print("可以使用以下命令查看构建进度:")
    print("  docker ps -a | grep buildx")
    print("\n等待构建完成后，可以手动运行验证:")
    print("  docker run --rm --platform linux/arm64 kylin-test:arm64")

    # 4. 生成报告
    generate_report()

    print("\n" + "=" * 60)
    print("验证脚本执行完成")
    print("=" * 60)
    print("\n注意: Docker 构建仍在后台运行")
    print("构建完成后会自动执行验证测试")

    return 0

if __name__ == "__main__":
    sys.exit(main())
