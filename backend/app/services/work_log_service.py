"""Work log service -- CRUD operations for work logs."""

from app.models.work_log import WorkLog

_WORKLOG_COLS = {c.name for c in WorkLog.__table__.columns}


class WorkLogService:
    """Service for work log operations."""

    def __init__(self, db):
        self.db = db

    def get_work_logs(self, skip=0, limit=10, **_filters):
        from app.models.work_log import WorkLog
        query = self.db.query(WorkLog)
        total = query.count()
        items = query.order_by(WorkLog.id.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_work_log(self, log_id: int):
        from app.models.work_log import WorkLog
        return self.db.query(WorkLog).filter(WorkLog.id == log_id).first()

    def create_work_log(self, data: dict):
        from app.models.work_log import WorkLog
        log = WorkLog(**data)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def update_work_log(self, log_id: int, data: dict):
        from app.models.work_log import WorkLog
        log = self.db.query(WorkLog).filter(WorkLog.id == log_id).first()
        if log:
            for key, value in data.items():
                if hasattr(log, key):
                    setattr(log, key, value)
            self.db.commit()
        return log

    def delete_work_log(self, log_id: int):
        from app.models.work_log import WorkLog
        log = self.db.query(WorkLog).filter(WorkLog.id == log_id).first()
        if log:
            self.db.delete(log)
            self.db.commit()
        return log


def write_work_log(db, log_type, action, entity_id, entity_name, **kwargs):
    """Write a work log entry -- used by other services for audit trail.

    Args:
        db: Database session
        log_type: 'project' | 'school' | etc
        action: 'create' | 'update' | 'delete'
        entity_id: ID of the entity being logged
        entity_name: Name of the entity being logged
        **kwargs: user_id, username, detail, etc.
    """
    from datetime import date, datetime, timezone
    # Build content with all available context (not silently dropped)
    detail = kwargs.pop("detail", "")
    username = kwargs.pop("username", "")
    parts = [f"{action}: {entity_name}"]
    if username:
        parts.append(f"by {username}")
    if detail:
        parts.append(detail)
    log = WorkLog(
        category=log_type,
        content=" | ".join(parts),
        log_date=date.today(),
        **{k: v for k, v in kwargs.items() if k in _WORKLOG_COLS},
    )
    db.add(log)
    db.commit()
    return log
