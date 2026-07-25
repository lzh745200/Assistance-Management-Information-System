# -*- coding: utf-8 -*-
"""ExportTask 模型属性覆盖率测试"""

from datetime import datetime, timedelta, timezone

from app.models.export_task import ExportStatus, ExportTask


def _task(status):
    return ExportTask(id=1, task_id="t-1", status=status)


def test_is_completed():
    assert _task(ExportStatus.COMPLETED.value).is_completed is True
    assert _task(ExportStatus.PENDING.value).is_completed is False


def test_is_failed():
    assert _task(ExportStatus.FAILED.value).is_failed is True
    assert _task(ExportStatus.PENDING.value).is_failed is False


def test_is_processing():
    assert _task(ExportStatus.PROCESSING.value).is_processing is True
    assert _task(ExportStatus.PENDING.value).is_processing is False


def test_is_expired():
    assert _task(ExportStatus.EXPIRED.value).is_expired is True
    assert _task(ExportStatus.PENDING.value).is_expired is False


def test_is_downloadable_not_completed():
    assert _task(ExportStatus.PENDING.value).is_downloadable is False


def test_is_downloadable_expired_past():
    t = _task(ExportStatus.COMPLETED.value)
    t.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    assert t.is_downloadable is False


def test_is_downloadable_ok():
    t = _task(ExportStatus.COMPLETED.value)
    t.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    assert t.is_downloadable is True
    t2 = _task(ExportStatus.COMPLETED.value)
    t2.expires_at = None
    assert t2.is_downloadable is True


def test_repr():
    assert "t-1" in repr(_task("pending"))
