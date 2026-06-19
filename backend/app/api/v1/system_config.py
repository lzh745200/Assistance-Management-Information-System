"""
System config helper functions - DB-backed implementation.

These plain async functions (NOT route handlers) are used by:
- encryption.py (:func:`get_system_config`, :func:`set_system_config`)
- backup_scheduler.py (:func:`get_system_config`)

They read/write the SystemConfig ORM model.
"""

import json
import logging

from app.core.database import SessionLocal
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)


async def get_system_config(key: str = None):
    """Get system config value(s) from the database.

    Args:
        key: Config key to fetch. If None, returns all config entries.

    Returns:
        dict: {key: value} mapping, or {} if no match.
    """
    db = SessionLocal()
    try:
        if key:
            row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if row:
                try:
                    return {key: json.loads(row.value)} if row.value else {key: None}
                except (json.JSONDecodeError, TypeError):
                    return {key: row.value}
            return {}
        rows = db.query(SystemConfig).all()
        result = {}
        for r in rows:
            try:
                result[r.key] = json.loads(r.value) if r.value else None
            except (json.JSONDecodeError, TypeError):
                result[r.key] = r.value
        return result
    finally:
        db.close()


async def set_system_config(key: str, value):
    """Set (upsert) a system config value in the database.

    Args:
        key: Config key.
        value: Config value (any JSON-serializable type).

    Returns:
        bool: True on success, False on failure.
    """
    db = SessionLocal()
    try:
        serialized = json.dumps(value) if not isinstance(value, str) else value
        row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if row:
            row.value = serialized
        else:
            db.add(SystemConfig(key=key, value=serialized))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error("Failed to set system config key=%s: %s", key, e)
        return False
    finally:
        db.close()


async def is_system_initialized():
    """Check whether the system has been initialized (has any config rows).

    Returns:
        bool: True if at least one config entry exists.
    """
    db = SessionLocal()
    try:
        return db.query(SystemConfig).count() > 0
    finally:
        db.close()
