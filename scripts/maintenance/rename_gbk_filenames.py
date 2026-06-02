"""Rename GBK-encoded filesystem names to UTF-8 (Chinese) names.

NTFS stores filenames as raw bytes. When files are created on a Chinese
Windows system (default codepage 936 / GBK), the names appear garbled on
non-Chinese systems, and cross-platform tools (git on Linux, etc.) cannot
read them properly.

This script:
  1. Walks the target directories
  2. Encodes each name as cp936 (the Windows GBK codepage)
  3. Decodes those bytes as GBK to recover the original Chinese
  4. Renames to the new UTF-8 Chinese name

Skips .git, node_modules, .venv, __pycache__, dist, etc.
Skips any path that doesn't have GBK-decodable bytes (already ASCII/UTF-8).
Reports what it would do in dry-run; actually renames with --apply.

Usage:
    python scripts/maintenance/rename_gbk_filenames.py            # dry-run
    python scripts/maintenance/rename_gbk_filenames.py --apply    # rename
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

TARGETS = [
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "scripts",
    PROJECT_ROOT / "backend",
    PROJECT_ROOT,
]

SKIP_DIR_SEGMENTS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__",
    "dist", "build", ".next", "MagicMock", ".pytest_cache",
    "data", "logs", "uploads_snapshot_20260101_000000",
}


def has_gbk_bytes(name: str) -> bool:
    """Heuristic: the name's cp936 bytes differ from its UTF-8 bytes."""
    try:
        utf8 = name.encode("utf-8")
    except UnicodeEncodeError:
        return False
    try:
        decoded = utf8.decode("cp936")
    except UnicodeDecodeError:
        return False
    return decoded != name


def gbk_to_chinese(name: str) -> str:
    """Encode the (potentially garbled) name as cp936 then decode as GBK."""
    return name.encode("utf-8").decode("cp936")


def safe_fallback(name: str) -> str:
    """If decode fails, fall back to a hash-based ASCII name."""
    import hashlib
    h = hashlib.md5(name.encode("utf-8", errors="replace")).hexdigest()[:8]
    return f"renamed_{h}"


def is_skipped_dir(dirpath: str) -> bool:
    return any(seg in dirpath.replace("\\", "/").split("/") for seg in SKIP_DIR_SEGMENTS)


def walk_gbk_paths(roots: list[Path]) -> list[tuple[Path, str]]:
    """Bottom-up walk. Returns list of (path, new_name) for GBK-encoded paths."""
    renames: list[tuple[Path, str]] = []
    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if is_skipped_dir(dirpath):
                continue
            for entry in list(dirnames) + list(filenames):
                if not has_gbk_bytes(entry):
                    continue
                new_name = gbk_to_chinese(entry)
                if not new_name or new_name == entry:
                    new_name = safe_fallback(entry)
                renames.append((Path(dirpath) / entry, new_name))
    return renames


def main(dry_run: bool = True) -> int:
    pairs = walk_gbk_paths(TARGETS)
    if not pairs:
        print("[OK] No GBK-encoded paths found.")
        return 0

    print(f"Found {len(pairs)} GBK-encoded path(s):\n")
    for old, new_name in pairs:
        try:
            rel = old.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = old
        print(f"  {rel}")
        print(f"      -> {new_name}")

    if dry_run:
        print("\n[dry-run] Re-run with --apply to actually rename.")
        return 0

    renamed = 0
    skipped = 0
    for old, new_name in pairs:
        if not old.exists():
            skipped += 1
            continue
        new = old.parent / new_name
        if new.exists():
            stem = new.stem
            suffix = new.suffix
            new = old.parent / f"{stem}_renamed{suffix}"
        old.rename(new)
        renamed += 1
    print(f"\n[done] Renamed: {renamed}, skipped (missing): {skipped}")
    return 0


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    sys.exit(main(dry_run=not apply))
