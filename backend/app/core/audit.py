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
        请使用 :class:`app.services.audit_service.AuditService.log`
        或 :class:`app.utils.audit_logger.AuditLogger.log`（后者自动持久化到数据库）。
        此函数保留以支持现有的 `record_audit()` 公共 API 调用者。
    """
    try:
        from app.models.audit import AuditLog  # type: ignore[import-untyped]

        log_entry = AuditLog(
            user_id=entry.get("user_id"),
            action=entry.get("action", ""),
            resource_type=entry.get("resource"),
            resource_id=str(entry["resource_id"]) if entry.get("resource_id") else None,
            new_value={"details": entry.get("details")} if entry.get("details") else None,
            user_ip=entry.get("ip_address"),
            status="success",
            level="info",
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.exception("Failed to persist audit entry to database: %s", e)
        try:
            db.rollback()
        except Exception as rollback_err:
            logger.debug("Rollback failed after audit persist error: %s", rollback_err)


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
