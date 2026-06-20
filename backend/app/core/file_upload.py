"""File upload helpers.

Provides upload path generation, filename sanitisation, and MIME-type
validation utilities used by upload endpoints.
"""

import mimetypes
import os
import re
import time
import uuid
from pathlib import Path
from typing import Optional, Set

# python-magic (libmagic wrapper) is *optional*. On some Windows environments
# the native libmagic binary triggers a fatal access violation during
# ``import magic`` that cannot be caught by try/except and crashes the whole
# process. To keep the module importable everywhere we deliberately avoid the
# top-level import: ``magic`` stays ``None`` and detection falls back to the
# stdlib ``mimetypes`` module + extension mapping, which is dependency-free and
# sufficient for an offline desktop deployment.
magic = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# MIME helpers
# ---------------------------------------------------------------------------

# Common MIME types that are always considered safe
SAFE_MIME_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "application/pdf",
    "text/csv",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "application/msword",
    # CSV may be detected as either
    "application/csv",
    "text/comma-separated-values",
}


def detect_mime_type(file_path: str) -> str:
    """Detect the MIME type of a file.

    Detection order:
      1. stdlib :func:`mimetypes.guess_type` (extension-based, no native deps)
      2. optional ``python-magic`` content sniffing (if the library loads)
      3. internal extension mapping :func:`_guess_mime_from_extension`

    Args:
        file_path: Path to the file.

    Returns:
        MIME type string, e.g. ``"image/png"``.
    """
    # 1. stdlib mimetypes — always safe, works on the extension
    guessed, _ = mimetypes.guess_type(file_path)
    if guessed:
        return guessed

    # 2. optional content-based detection via python-magic (if importable)
    if magic is not None:
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(file_path)
        except Exception:
            pass  # fall through to extension mapping

    # 3. final fallback: internal extension mapping
    suffix = Path(file_path).suffix.lower()
    return _guess_mime_from_extension(suffix)


def detect_mime_type_from_bytes(content: bytes) -> str:
    """Detect MIME type from raw bytes.

    Uses ``python-magic`` content sniffing when the library is available;
    otherwise returns ``"application/octet-stream"`` as a safe default (byte-level
    detection without a filename cannot fall back to extension mapping).

    Args:
        content: File content as bytes.

    Returns:
        MIME type string.
    """
    if magic is not None:
        try:
            mime = magic.Magic(mime=True)
            return mime.from_buffer(content)
        except Exception:
            pass
    return "application/octet-stream"


def is_allowed_mime(mime_type: str, allowed_types: Optional[Set[str]] = None) -> bool:
    """Check whether a MIME type is in the allowed set.

    Args:
        mime_type: The MIME type to check.
        allowed_types: Set of allowed MIME types. Defaults to :data:`SAFE_MIME_TYPES`.

    Returns:
        *True* if allowed.
    """
    types = allowed_types or SAFE_MIME_TYPES
    return mime_type in types


# ---------------------------------------------------------------------------
# Filename utilities
# ---------------------------------------------------------------------------

# Characters allowed in a sanitised filename
_SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._\-一-龥]")


def sanitize_filename(filename: str) -> str:
    """Remove potentially dangerous characters from a filename.

    Args:
        filename: Original filename from the upload.

    Returns:
        A safe filename with only alphanumeric, dot, dash, underscore, and
        Chinese characters.
    """
    name, ext = os.path.splitext(filename)
    ext = ext.lower()
    # Keep only safe characters, replace others with underscore
    safe_name = _SAFE_FILENAME_RE.sub("_", name)
    # Collapse multiple underscores
    safe_name = re.sub(r"_+", "_", safe_name).strip("_")
    if not safe_name:
        safe_name = "file"
    # Truncate to reasonable length (leave room for timestamp + uuid)
    max_len = 150 - 32 - 20
    if len(safe_name) > max_len:
        safe_name = safe_name[:max_len]
    return f"{safe_name}{ext}"


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """Generate a unique, sanitised filename.

    Args:
        original_filename: The user-uploaded filename.
        prefix: Optional prefix prepended to the generated name.

    Returns:
        A unique filename string.
    """
    safe = sanitize_filename(original_filename)
    name, ext = os.path.splitext(safe)
    uid = uuid.uuid4().hex[:12]
    ts = int(time.time())
    parts = [p for p in (prefix, f"{ts}_{uid}", name) if p]
    return f"{'_'.join(parts)}{ext}"


# ---------------------------------------------------------------------------
# Upload path helpers
# ---------------------------------------------------------------------------


def get_upload_dir(*, settings=None) -> str:
    """Return the configured upload directory.

    Args:
        settings: Optional :class:`Settings` instance.

    Returns:
        Absolute path to the upload directory.
    """
    if settings is None:
        try:
            from app.core.config import settings  # type: ignore[import-untyped]
        except Exception:
            settings = None

    upload_dir = getattr(settings, "UPLOAD_DIR", "./uploads") if settings else "./uploads"
    path = Path(upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return str(path.absolute())


def get_upload_subdir(subdir: str, *, settings=None) -> str:
    """Return the path to a sub-directory of the upload directory.

    Args:
        subdir: Sub-directory name (e.g. ``"avatars"``, ``"reports"``).
        settings: Optional :class:`Settings` instance.

    Returns:
        Absolute path to the sub-directory (created if needed).
    """
    base = Path(get_upload_dir(settings=settings))
    target = base / subdir
    target.mkdir(parents=True, exist_ok=True)
    return str(target.absolute())


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _guess_mime_from_extension(suffix: str) -> str:
    """Rudimentary extension-to-MIME mapping."""
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".pdf": "application/pdf",
        ".csv": "text/csv",
        ".txt": "text/plain",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".ppt": "application/vnd.ms-powerpoint",
        ".json": "application/json",
    }
    return mapping.get(suffix, "application/octet-stream")
