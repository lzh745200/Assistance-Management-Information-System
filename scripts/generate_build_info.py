"""生成 _build_info.json — 在 CI 打包前调用。

用法: python scripts/generate_build_info.py [version]
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT_ROOT / "backend" / "app" / "core" / "_build_info.json"


def main():
    version = sys.argv[1].lstrip("v") if len(sys.argv) > 1 else None
    if not version:
        pkg = PROJECT_ROOT / "package.json"
        if pkg.exists():
            version = json.loads(pkg.read_text(encoding="utf-8")).get("version", "0.0.0")
        else:
            version = "0.0.0"

    try:
        git_hash = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, timeout=5)
            .decode()
            .strip()
        )
    except Exception:
        git_hash = "unknown"

    info = {
        "version": version,
        "git_hash": git_hash,
        "build_time": datetime.now(timezone.utc).isoformat(),
        "builder": "ci",
    }
    OUTPUT.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print(f"Build info written: {OUTPUT.relative_to(PROJECT_ROOT)} -> {info}")


if __name__ == "__main__":
    main()
