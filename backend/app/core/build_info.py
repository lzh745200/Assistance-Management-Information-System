"""构建元数据 — 由 CI 打包前生成，运行时提供版本指纹。

开发环境下使用默认值（dev），CI 构建时由 generate_build_info.py 脚本覆写。
"""

import subprocess
from pathlib import Path

_BUILD_INFO_FILE = Path(__file__).with_name("_build_info.json")


def _load() -> dict:
    if _BUILD_INFO_FILE.exists():
        import json

        try:
            return json.loads(_BUILD_INFO_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


_cached: dict | None = None


def get_build_info() -> dict:
    """返回构建元数据：version / git_hash / build_time / builder。"""
    global _cached
    if _cached is not None:
        return _cached

    info = _load()
    if not info:
        git_hash = "dev"
        try:
            git_hash = (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
                .decode()
                .strip()
            )
        except Exception:
            pass
        info = {
            "git_hash": git_hash,
            "build_time": None,
            "builder": "dev",
        }

    from app.core.config import settings

    info.setdefault("version", settings.PROJECT_VERSION)
    _cached = info
    return info
