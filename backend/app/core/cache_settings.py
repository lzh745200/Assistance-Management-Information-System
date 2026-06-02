"""Cache settings.

Bridges the application Settings with the cache layer, providing
convenience defaults for TTLs, max sizes, and backend selection.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CacheSettings:
    """Cache configuration dataclass.

    All values are loaded from the application :class:`Settings` at startup
    and can be accessed by the cache backends.
    """

    enabled: bool = True
    """Whether the cache layer is active."""

    backend: str = "memory"
    """Cache backend identifier (``"memory"`` or ``"redis"``)."""

    default_ttl: int = 3600
    """Default TTL (seconds) for cached entries."""

    redis_url: Optional[str] = None
    """Redis connection URL (only used when *backend* is ``"redis"``)."""

    max_entries: int = 10_000
    """Maximum number of entries in the in-memory cache."""

    @classmethod
    def from_settings(cls) -> "CacheSettings":
        """Build a CacheSettings instance from the application settings."""
        try:
            from app.core.config import settings  # type: ignore[import-untyped]

            return cls(
                enabled=getattr(settings, "CACHE_ENABLED", True),
                backend=getattr(settings, "CACHE_BACKEND", "memory"),
                default_ttl=getattr(settings, "CACHE_DEFAULT_TTL", 3600),
                redis_url=getattr(settings, "REDIS_URL", None),
                max_entries=getattr(settings, "CACHE_MAX_SIZE", 10_000),
            )
        except Exception:
            return cls()


# Singleton instance
_cache_settings: Optional[CacheSettings] = None


def get_cache_settings() -> CacheSettings:
    """Return (and lazily create) the cache settings singleton."""
    global _cache_settings
    if _cache_settings is None:
        _cache_settings = CacheSettings.from_settings()
    return _cache_settings
