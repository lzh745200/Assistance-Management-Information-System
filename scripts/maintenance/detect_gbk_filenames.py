"""Identify filenames that are not valid UTF-8 OR contain non-ASCII bytes that
look like GBK (not Chinese in UTF-8).

A filename with GBK bytes looks like: 椤圭洰 (each Chinese char is 2 bytes,
which when interpreted as UTF-8 would form 3-byte chars). A truly UTF-8
Chinese name looks like: 项目 (each Chinese char is 3 bytes in UTF-8).

This script walks and reports paths where the FILENAME'S raw bytes (not
the path's string representation) are GBK encoded.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Skip these directory segments
SKIP_SEGMENTS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "MagicMock"}


def is_path_skipped(dirpath: str) -> bool:
    parts = dirpath.replace("\\", "/").split("/")
    return any(seg in parts for seg in SKIP_SEGMENTS)


def is_gbk_filename(name: str) -> bool:
    """True if the filename's UTF-8 bytes, when decoded as GBK, give a
    shorter (i.e. 2-byte-per-char) result. This is the GBK signature."""
    raw = name.encode("utf-8", errors="ignore")
    try:
        decoded = raw.decode("gbk")
    except UnicodeDecodeError:
        return False
    return len(decoded) < len(name)


def gbk_decode(name: str) -> str:
    return name.encode("utf-8", errors="ignore").decode("gbk")


def find_gbk_filenames(roots: list[Path]) -> list[Path]:
    found = []
    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if is_path_skipped(dirpath):
                continue
            for entry in list(dirnames) + list(filenames):
                if is_gbk_filename(entry):
                    found.append(Path(dirpath) / entry)
    return found


def main() -> int:
    roots = [PROJECT_ROOT / "docs", PROJECT_ROOT / "scripts",
             PROJECT_ROOT / "backend", PROJECT_ROOT]
    found = find_gbk_filenames(roots)
    if not found:
        print("[OK] No GBK-byte filenames found.")
        return 0
    for p in found:
        try:
            rel = p.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = p
        try:
            decoded = gbk_decode(p.name)
            print(f"  {rel}  ->  {decoded}")
        except Exception as e:
            print(f"  {rel}  ->  (decode failed: {e})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
