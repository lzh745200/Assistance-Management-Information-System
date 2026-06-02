"""
军队乡村振兴管理系统 - 快速打包测试
仅构建后端，用于快速验证打包流程
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

def test_backend_simple():
    """简单测试后端是否可以启动"""
    print("=" * 60)
    print("测试后端启动")
    print("=" * 60)

    # 检查后端依赖
    print("\n检查后端依赖...")
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print(f"FastAPI: {fastapi.__version__}")
        print(f"Uvicorn: {uvicorn.__version__}")
        print(f"SQLAlchemy: {sqlalchemy.__version__}")
        print("[PASS] 后端依赖检查通过")
    except ImportError as e:
        print(f"[FAIL] 缺少依赖: {e}")
        return False

    # 测试后端启动脚本
    print("\n测试后端启动脚本...")
    start_py = BACKEND_DIR / "start.py"
    if not start_py.exists():
        print(f"[FAIL] 启动脚本不存在: {start_py}")
        return False

    print(f"[PASS] 启动脚本存在: {start_py}")

    # 检查数据库
    db_path = BACKEND_DIR / "data" / "rural_revitalization.db"
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"[PASS] 数据库文件存在: {db_path} ({size_mb:.1f} MB)")
    else:
        print(f"[WARN] 数据库文件不存在: {db_path}")

    return True

def test_frontend_build():
    """测试前端构建产物"""
    print("\n=" * 60)
    print("测试前端构建产物")
    print("=" * 60)

    frontend_dist = ROOT_DIR / "frontend" / "dist"
    if not frontend_dist.exists():
        print(f"[FAIL] 前端构建产物不存在: {frontend_dist}")
        return False

    index_html = frontend_dist / "index.html"
    if not index_html.exists():
        print(f"[FAIL] index.html 不存在")
        return False

    # 统计文件数量
    files = list(frontend_dist.rglob("*"))
    file_count = len([f for f in files if f.is_file()])
    print(f"[PASS] 前端文件数量: {file_count}")

    # 检查关键文件
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        js_files = list(assets_dir.glob("*.js"))
        css_files = list(assets_dir.glob("*.css"))
        print(f"[PASS] JS 文件: {len(js_files)}, CSS 文件: {len(css_files)}")

    return True

def test_electron_config():
    """测试 Electron 配置"""
    print("\n=" * 60)
    print("测试 Electron 配置")
    print("=" * 60)

    # 检查 package.json
    package_json = ROOT_DIR / "package.json"
    if not package_json.exists():
        print(f"[FAIL] package.json 不存在")
        return False

    print(f"[PASS] package.json 存在")

    # 检查 electron 目录
    electron_dir = ROOT_DIR / "electron"
    if not electron_dir.exists():
        print(f"[FAIL] electron 目录不存在")
        return False

    main_js = electron_dir / "main.js"
    if not main_js.exists():
        print(f"[FAIL] main.js 不存在")
        return False

    print(f"[PASS] Electron 主进程文件存在")

    # 检查资源目录
    resources_dir = ROOT_DIR / "resources"
    if resources_dir.exists():
        icons_dir = resources_dir / "icons"
        if icons_dir.exists():
            icon_files = list(icons_dir.glob("*"))
            print(f"[PASS] 图标文件数量: {len(icon_files)}")

    return True

def main():
    """主函数"""
    print("=" * 60)
    print("军队乡村振兴管理系统 - 快速测试")
    print("=" * 60)

    results = []

    # 测试后端
    results.append(("后端环境", test_backend_simple()))

    # 测试前端
    results.append(("前端构建", test_frontend_build()))

    # 测试 Electron
    results.append(("Electron配置", test_electron_config()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n[PASS] 所有测试通过，可以进行完整打包")
        return 0
    else:
        print("\n[FAIL] 部分测试失败，请检查问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())
