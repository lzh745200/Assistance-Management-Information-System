"""Scan for files whose first 64 bytes are all zero (NTFS corruption symptom).

Run as a pre-commit guard or CI check. Exits non-zero on findings.

Usage:
    python scripts/maintenance/scan_corrupted_files.py
    python scripts/maintenance/scan_corrupted_files.py --check-bytes 1024

Only scans directories that should be in version control (or that are part of
the runtime build). Always skips:
- .git/
- node_modules/, .venv*, venv_*/
- __pycache__/
- dist/ build artifacts (build/, frontend/dist, resources/frontend)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SKIP_DIR_NAMES = {
    ".git", ".gstack", ".worktrees", ".arts", ".claude",
    "node_modules", "node_modules_old", "node_modules_corrupted",
    ".venv", ".venv_corrupted", "venv", "venv_corrupted", "venv_arm64",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".hypothesis",
    "dist", "build", ".cache", "coverage", "htmlcov",
    "frontend_corrupted", "_empty", "_trash", "MagicMock",
    "exports", "uploads", "backups", "logs", "temp_build",
    "data",
}

# By default scan only sources that are tracked or in source trees
DEFAULT_TARGETS = [
    "frontend/public",
    "frontend/src",
    "resources/icons",
    "resources/map-tiles",
    "resources/config",
    "database",
    "docs",
    "backend/app",
    "backend/alembic",
    "backend/tests",
    "scripts",
    "electron",
    "build-scripts",
    "installers",
    "backend/build-scripts",
]


def is_all_zero(data: bytes, n: int) -> bool:
    return n > 0 and all(b == 0 for b in data[:n])


def scan(check_bytes: int) -> list[tuple[Path, int]]:
    findings: list[tuple[Path, int]] = []
    for rel in DEFAULT_TARGETS:
        root = PROJECT_ROOT / rel
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
            for fname in filenames:
                p = Path(dirpath) / fname
                try:
                    size = p.stat().st_size
                except OSError:
                    continue
                # 0-byte files are legitimately empty (e.g. __init__.py) — skip
                if size == 0:
                    continue
                try:
                    with open(p, "rb") as f:
                        head = f.read(check_bytes)
                except (OSError, PermissionError):
                    continue
                if is_all_zero(head, check_bytes):
                    findings.append((p, size))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-bytes",
        type=int,
        default=64,
        help="How many leading bytes must all be zero to flag the file (default: 64)",
    )
    args = parser.parse_args()

    findings = scan(args.check_bytes)
    if not findings:
        print(f"[OK] No files with all-zero prefix (first {args.check_bytes} bytes).")
        return 0

    print(f"[FAIL] Found {len(findings)} file(s) with all-zero prefix:")
    for path, size in findings:
        print(f"  {path.relative_to(PROJECT_ROOT)} ({size} bytes)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
