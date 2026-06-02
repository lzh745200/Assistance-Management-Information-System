"""Audit logging models and helpers.

Provides a lightweight audit-log entry model and service utilities for
recording security-relevant events (login, CRUD operations, etc.).
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory store for audit entries (when no DB session is available).
# In production the AuditLogService is expected to write to the database.
# ---------------------------------------------------------------------------
_audit_store: list[dict] = []


def record_audit(
    user_id: Optional[int] = None,
    action: str = "",
    resource: str = "",
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    *,
    db=None,
) -> None:
    """Record an audit event.

    If *db* is provided the entry is flushed to the database via the ORM
    AuditLog model; otherwise it is kept in a simple in-memory list for
    development / testing.

    Args:
        user_id: ID of the user who performed the action.
        action: Short action label (e.g. ``"login"``, ``"delete"``).
        resource: Affected resource type (e.g. ``"User"``, ``"Village"``).
        resource_id: Affected resource identifier.
        details: Human-readable description of the event.
        ip_address: Client IP address.
        db: Optional SQLAlchemy session.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc),
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "details": details,
        "ip_address": ip_address,
    }

    if db is not None:
        _persist_to_db(db, entry)
    else:
        _audit_store.append(entry)
        logger.debug("Audit (memory): %s", entry)


def _persist_to_db(db, entry: dict) -> None:
    """Persist an audit entry via the ORM AuditLog model.

    .. deprecated::
        直接 ORM 写入已标记为遗留模式。对于新的审计日志需求，
        请使用 :class:`app.services.audit_service.AuditService.log`。
        此函数保留以支持现有的 `record_audit()` 公共 API 调用者。
    """
    try:
        from app.models.audit import AuditLog  # type: ignore[import-untyped]

        log_entry = AuditLog(
            user_id=entry["user_id"],
            action=entry["action"],
            resource=entry["resource"],
            resource_id=entry.get("resource_id"),
            details=entry.get("details"),
            ip_address=entry.get("ip_address"),
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        logger.exception("Failed to persist audit entry to database")
        try:
            db.rollback()
        except Exception:
            pass


def get_audit_records(
    user_id: Optional[int] = None,
    limit: int = 100,
) -> list[dict]:
    """Retrieve recent audit records from the in-memory store.

    Args:
        user_id: Optional filter by user ID.
        limit: Maximum number of records to return.

    Returns:
        List of audit entry dicts, newest first.
    """
    filtered = _audit_store
    if user_id is not None:
        filtered = [e for e in filtered if e.get("user_id") == user_id]
    return sorted(filtered, key=lambda e: e["timestamp"], reverse=True)[:limit]


def clear_audit_store() -> None:
    """Clear the in-memory audit store (useful for testing)."""
    _audit_store.clear()
