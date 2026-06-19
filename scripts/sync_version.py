"""版本号同步脚本 — 从 version.txt 或 git tag 同步到所有配置文件

用法: python scripts/sync_version.py [version]
  - 不带参数：从 version.txt 读取
  - 带参数：直接使用该版本号 (如 v1.4.0 → 1.4.0)

同步目标: config.py, package.json, NSIS 脚本, .env.example
"""

import json
import os
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_version():
    if len(sys.argv) > 1:
        v = sys.argv[1].lstrip("v")
    else:
        vf = PROJECT_ROOT / "version.txt"
        if vf.exists():
            v = vf.read_text().strip()
        else:
            print("ERROR: 无 version.txt 且未提供参数")
            sys.exit(1)
    return v


def update_config_py(version: str):
    path = PROJECT_ROOT / "backend" / "app" / "core" / "config.py"
    content = path.read_text()
    new_content = re.sub(
        r'PROJECT_VERSION:\s*str\s*=\s*"[^"]*"',
        f'PROJECT_VERSION: str = "{version}"',
        content,
    )
    if new_content != content:
        path.write_text(new_content)
        print(f"  UPD: {path.relative_to(PROJECT_ROOT)}")


def update_package_json(version: str):
    path = PROJECT_ROOT / "frontend" / "package.json"
    pkg = json.loads(path.read_text())
    if pkg.get("version") != version:
        pkg["version"] = version
        path.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + "\n")
        print(f"  UPD: {path.relative_to(PROJECT_ROOT)}")


def update_nsis_scripts(version: str):
    for nsi in (PROJECT_ROOT / "build-scripts").glob("*.nsi"):
        content = nsi.read_text()
        new_content = re.sub(
            r'!define PRODUCT_VERSION\s+"[^"]*"',
            f'!define PRODUCT_VERSION "{version}"',
            content,
        )
        if new_content != content:
            nsi.write_text(new_content)
            print(f"  UPD: {nsi.relative_to(PROJECT_ROOT)}")


def update_env_example(version: str):
    for env_path in [
        PROJECT_ROOT / "frontend" / ".env.example",
        PROJECT_ROOT / "frontend" / ".env.production",
    ]:
        if not env_path.exists():
            continue
        content = env_path.read_text()
        new_content = re.sub(
            r'VITE_APP_VERSION=\S+',
            f'VITE_APP_VERSION={version}',
            content,
        )
        if new_content != content:
            env_path.write_text(new_content)
            print(f"  UPD: {env_path.relative_to(PROJECT_ROOT)}")


def main():
    version = get_version()
    print(f"Syncing version to {version}...")
    update_config_py(version)
    update_package_json(version)
    update_nsis_scripts(version)
    update_env_example(version)
    print("Done.")


if __name__ == "__main__":
    main()
