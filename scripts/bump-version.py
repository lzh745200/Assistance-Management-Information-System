#!/usr/bin/env python3
"""版本号统一管理脚本

用法：
    python scripts/bump-version.py 1.2.0

同步更新三处版本号：
- package.json（根目录）
- frontend/package.json
- backend/app/core/config.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FILES = {
    "root_pkg": ROOT / "package.json",
    "frontend_pkg": ROOT / "frontend" / "package.json",
    "config_py": ROOT / "backend" / "app" / "core" / "config.py",
}


def validate_version(version: str) -> bool:
    return bool(re.match(r"^\d+\.\d+\.\d+$", version))


def update_json(path: Path, version: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    old = data.get("version", "?")
    data["version"] = version
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  {path.name}: {old} -> {version}")


def update_config_py(path: Path, version: str) -> None:
    content = path.read_text(encoding="utf-8")
    new_content, count = re.subn(
        r'(PROJECT_VERSION:\s*str\s*=\s*")[^"]*(")',
        rf"\g<1>{version}\g<2>",
        content,
    )
    if count == 0:
        print(f"  ⚠ 未找到 PROJECT_VERSION 定义: {path}")
        return
    old_match = re.search(r'PROJECT_VERSION:\s*str\s*=\s*"([^"]*)"', content)
    old = old_match.group(1) if old_match else "?"
    path.write_text(new_content, encoding="utf-8")
    print(f"  config.py: {old} -> {version}")


def main():
    if len(sys.argv) != 2 or not validate_version(sys.argv[1]):
        print("用法: python scripts/bump-version.py <MAJOR.MINOR.PATCH>")
        print("示例: python scripts/bump-version.py 1.2.0")
        sys.exit(1)

    version = sys.argv[1]
    print(f"同步版本号到 {version}:")

    update_json(FILES["root_pkg"], version)
    update_json(FILES["frontend_pkg"], version)
    update_config_py(FILES["config_py"], version)

    print("✓ 完成")


if __name__ == "__main__":
    main()
