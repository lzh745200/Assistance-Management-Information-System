"""File utility functions.

Provides helpers for common file-system operations: reading, writing,
copying, computing hashes, and validating paths.
"""

import hashlib
import logging
import os
import shutil
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure that a directory exists, creating it if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_path(base_dir: Union[str, Path], *parts: str) -> Path:
    """Join path components under base_dir and verify no path-traversal."""
    resolved = Path(base_dir).resolve()
    target = resolved.joinpath(*parts).resolve()
    if not str(target).startswith(str(resolved) + os.sep) and target != resolved:
        raise ValueError(f"路径越界: {target}")
    return target


def is_safe_path(base_dir: Union[str, Path], target_path: Union[str, Path]) -> bool:
    """Check whether target_path is within base_dir."""
    try:
        safe_path(base_dir, target_path)
        return True
    except ValueError:
        return False


def read_file(file_path: Union[str, Path], *, binary: bool = False) -> Union[str, bytes]:
    """Read the entire contents of a file."""
    mode = "rb" if binary else "r"
    encoding = None if binary else "utf-8"
    with open(file_path, mode, encoding=encoding) as f:
        return f.read()


def write_file(
    file_path: Union[str, Path],
    content: Union[str, bytes],
    *,
    binary: bool = False,
    atomic: bool = False,
) -> None:
    """Write content to a file, optionally atomically."""
    mode = "wb" if binary else "w"
    encoding = None if binary else "utf-8"
    target = Path(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if atomic:
        tmp = target.with_suffix(target.suffix + ".tmp")
        with open(tmp, mode, encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(target)
    else:
        with open(target, mode, encoding=encoding) as f:
            f.write(content)


def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Copy a file from src to dst."""
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def delete_file(path: Union[str, Path], *, missing_ok: bool = True) -> None:
    """Delete a file."""
    p = Path(path)
    try:
        p.unlink()
    except FileNotFoundError:
        if not missing_ok:
            raise


def delete_directory(path: Union[str, Path], *, missing_ok: bool = True) -> None:
    """Recursively delete a directory."""
    p = Path(path)
    if p.exists() and p.is_dir():
        shutil.rmtree(p)
    elif not p.exists() and not missing_ok:
        raise FileNotFoundError(f"目录不存在: {path}")


def file_md5(path: Union[str, Path]) -> str:
    """Compute the MD5 hash of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def file_sha256(path: Union[str, Path]) -> str:
    """Compute the SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def file_size(path: Union[str, Path]) -> int:
    """Return the size of a file in bytes."""
    return Path(path).stat().st_size


def file_extension(path: Union[str, Path]) -> str:
    """Return the lower-cased file extension (with leading dot)."""
    return Path(path).suffix.lower()


def temp_filename(suffix: str = "") -> str:
    """Generate a random temporary filename."""
    import uuid
    return f"{uuid.uuid4().hex}{suffix}"
