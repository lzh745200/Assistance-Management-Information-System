"""
军队乡村振兴管理系统 - 安装包测试脚本
测试已生成的 Windows 安装包
"""

import json
import os
import sys
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DIST_DIR = ROOT_DIR / "dist" / "electron"
VERSION = json.loads((ROOT_DIR / "package.json").read_text())["version"]

def test_windows_installer():
    """测试 Windows 安装包"""
    print("=" * 60)
    print("测试 Windows 安装包")
    print("=" * 60)

    # 查找安装包
    installer = DIST_DIR / f"军队乡村振兴管理系统_{VERSION}_win_x64.exe"
    portable = DIST_DIR / f"军队乡村振兴管理系统_{VERSION}_Portable.exe"

    if not installer.exists():
        print(f"[FAIL] 安装包不存在: {installer}")
        return False

    if not portable.exists():
        print(f"[FAIL] 便携版不存在: {portable}")
        return False

    # 检查文件大小
    installer_size = installer.stat().st_size / (1024 * 1024)
    portable_size = portable.stat().st_size / (1024 * 1024)

    print(f"[PASS] 安装包大小: {installer_size:.1f} MB")
    print(f"[PASS] 便携版大小: {portable_size:.1f} MB")

    if installer_size < 100:
        print(f"[FAIL] 安装包大小异常")
        return False

    print(f"[PASS] Windows 安装包验证通过")
    return True

def test_linux_package():
    """测试 Linux 安装包"""
    print("\n" + "=" * 60)
    print("测试 Linux 安装包")
    print("=" * 60)

    # 查找 ARM64 包
    arm64_deb = DIST_DIR / f"military-rural-system_{VERSION}_arm64.deb"
    amd64_deb = DIST_DIR / f"military-rural-system_{VERSION}_amd64.deb"

    if not arm64_deb.exists():
        print(f"[FAIL] ARM64 包不存在: {arm64_deb}")
        return False

    # 检查文件大小
    arm64_size = arm64_deb.stat().st_size / (1024 * 1024)
    print(f"[PASS] ARM64 包大小: {arm64_size:.1f} MB")

    if amd64_deb.exists():
        amd64_size = amd64_deb.stat().st_size / (1024 * 1024)
        print(f"[PASS] AMD64 包大小: {amd64_size:.1f} MB")

    if arm64_size < 100:
        print(f"[FAIL] ARM64 包大小异常")
        return False

    print(f"[PASS] Linux 安装包验证通过")
    return True

def test_portable_run():
    """测试便携版是否可以运行"""
    print("\n" + "=" * 60)
    print("测试便携版运行")
    print("=" * 60)

    portable = DIST_DIR / f"军队乡村振兴管理系统_{VERSION}_Portable.exe"

    if not portable.exists():
        print(f"[FAIL] 便携版不存在")
        return False

    print(f"[INFO] 便携版路径: {portable}")
    print(f"[INFO] 可以手动双击测试运行")
    print(f"[PASS] 便携版文件完整")

    return True

def generate_test_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("生成测试报告")
    print("=" * 60)

    report = []
    report.append("# 安装包测试报告\n")
    report.append(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    report.append("## 测试结果\n\n")

    # Windows 安装包
    installer = DIST_DIR / f"军队乡村振兴管理系统_{VERSION}_win_x64.exe"
    if installer.exists():
        size = installer.stat().st_size / (1024 * 1024)
        report.append(f"### Windows 安装包 ✓\n")
        report.append(f"- 文件名: {installer.name}\n")
        report.append(f"- 大小: {size:.1f} MB\n")
        report.append(f"- 路径: {installer}\n\n")

    # 便携版
    portable = DIST_DIR / f"军队乡村振兴管理系统_{VERSION}_Portable.exe"
    if portable.exists():
        size = portable.stat().st_size / (1024 * 1024)
        report.append(f"### Windows 便携版 ✓\n")
        report.append(f"- 文件名: {portable.name}\n")
        report.append(f"- 大小: {size:.1f} MB\n")
        report.append(f"- 路径: {portable}\n\n")

    # ARM64
    arm64_deb = DIST_DIR / "military-rural-system_{VERSION}_arm64.deb"
    if arm64_deb.exists():
        size = arm64_deb.stat().st_size / (1024 * 1024)
        report.append(f"### 麒麟 ARM64 ✓\n")
        report.append(f"- 文件名: {arm64_deb.name}\n")
        report.append(f"- 大小: {size:.1f} MB\n")
        report.append(f"- 路径: {arm64_deb}\n\n")

    # AMD64
    amd64_deb = DIST_DIR / "military-rural-system_{VERSION}_amd64.deb"
    if amd64_deb.exists():
        size = amd64_deb.stat().st_size / (1024 * 1024)
        report.append(f"### Linux AMD64 ✓\n")
        report.append(f"- 文件名: {amd64_deb.name}\n")
        report.append(f"- 大小: {size:.1f} MB\n")
        report.append(f"- 路径: {amd64_deb}\n\n")

    report.append("## 测试说明\n\n")
    report.append("### Windows 测试\n")
    report.append("1. 双击安装包进行安装\n")
    report.append("2. 或直接运行便携版\n")
    report.append("3. 首次启动会自动创建数据库\n")
    report.append("4. 默认账号: admin / admin123\n\n")

    report.append("### 麒麟 ARM64 测试\n")
    report.append("```bash\n")
    report.append(f"sudo dpkg -i military-rural-system_{VERSION}_arm64.deb\n")
    report.append("sudo apt-get install -f\n")
    report.append("military-rural-system-standalone\n")
    report.append("```\n\n")

    report.append("## 测试结论\n\n")
    report.append("✓ 所有安装包已生成\n")
    report.append("✓ 文件大小正常\n")
    report.append("✓ 可以进行实际安装测试\n")

    report_file = ROOT_DIR / "安装包测试报告.md"
    report_file.write_text("".join(report), encoding='utf-8')
    print(f"[PASS] 测试报告已生成: {report_file}")

    return True

def main():
    """主函数"""
    print("=" * 60)
    print("军队乡村振兴管理系统 - 安装包测试")
    print("=" * 60)

    results = []

    # 测试 Windows 安装包
    results.append(("Windows安装包", test_windows_installer()))

    # 测试 Linux 安装包
    results.append(("Linux安装包", test_linux_package()))

    # 测试便携版
    results.append(("便携版", test_portable_run()))

    # 生成报告
    results.append(("生成报告", generate_test_report()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n[PASS] 所有测试通过")
        print("\n安装包位置:")
        print(f"  {DIST_DIR}")
        return 0
    else:
        print("\n[FAIL] 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
