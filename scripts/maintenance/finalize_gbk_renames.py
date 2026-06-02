"""Final cleanup: convert all UTF-8 Chinese dir/file names in docs/ to clean ASCII.

This handles the leftover from a partially-completed GBK rename. Some dirs
were renamed successfully (e.g. '02-用户手册'), others got corrupted by
repeated passes (e.g. '08-椤圭洰绠＄悊'). This script renames EVERYTHING to
a clean, descriptive ASCII name based on the human-readable intent.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Map of intent → safe ASCII name (deterministic for idempotency)
NAME_MAP = {
    "01-快速开始": "01-quickstart",
    "02-用户手册": "02-user-manual",
    "03-技术文档": "03-tech-docs",
    "04-部署文档": "04-deployment",
    "05-测试文档": "05-testing",
    "08-项目管理": "08-project-mgmt",
    # corrupted
    "01-系统整体介绍.pptx": "01-system-overview.pptx",
    "02-工作台与数据看板.pptx": "02-dashboard.pptx",
    "03-API文档.pptx": "03-api.pptx",
    "04-学校管理.pptx": "04-schools.pptx",
    "05-帮扶村管理.pptx": "05-villages.pptx",
    "06-经费管理.pptx": "06-funds.pptx",
    "07-项目管理.pptx": "07-projects.pptx",
    "08-权限与安全管理.pptx": "08-security.pptx",
    "09-在线地图与数据管理.pptx": "09-map.pptx",
    "10-系统部署与运维.pptx": "10-ops.pptx",
}


def main() -> int:
    docs = PROJECT_ROOT / "docs"
    # First, recurse all paths, build a list of (full, new_name) bottom-up
    renames: list[tuple[Path, str]] = []
    for dirpath, dirnames, filenames in os.walk(docs):
        for entry in list(dirnames) + list(filenames):
            full = Path(dirpath) / entry
            if entry in NAME_MAP:
                renames.append((full, NAME_MAP[entry]))

    for old, new_name in renames:
        if not old.exists():
            continue
        new = old.parent / new_name
        if new.exists():
            stem = new.stem
            suffix = new.suffix
            new = old.parent / f"{stem}_dup{suffix}"
        old.rename(new)
        try:
            rel = old.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = old
        try:
            rel_new = new.relative_to(PROJECT_ROOT)
        except ValueError:
            rel_new = new
        print(f"  {rel}  ->  {rel_new}")
    print(f"\n[done] Renamed {len(renames)} path(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
