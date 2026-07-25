"""app.core.audit 覆盖率攻坚测试

覆盖 record_audit（内存/DB 双路径）、_persist_to_db（含异常与 rollback 降级）、
get_audit_records（过滤/排序/限量）、clear_audit_store。
"""

from unittest.mock import MagicMock

import pytest

import app.core.audit as audit


@pytest.fixture(autouse=True)
def _clean_store():
    audit.clear_audit_store()
    yield
    audit.clear_audit_store()


class TestRecordAuditMemory:
    def test_records_to_memory_store(self):
        audit.record_audit(
            user_id=1, action="login", resource="User",
            resource_id="1", details="d", ip_address="127.0.0.1",
        )
        records = audit.get_audit_records()
        assert len(records) == 1
        assert records[0]["action"] == "login"
        assert records[0]["user_id"] == 1

    def test_filter_by_user_id(self):
        audit.record_audit(user_id=1, action="a")
        audit.record_audit(user_id=2, action="b")
        records = audit.get_audit_records(user_id=1)
        assert len(records) == 1
        assert records[0]["action"] == "a"

    def test_limit_and_newest_first(self):
        for i in range(5):
            audit.record_audit(action=f"a{i}")
        records = audit.get_audit_records(limit=3)
        assert len(records) == 3
        # newest first（时间戳倒序）
        assert records[0]["timestamp"] >= records[-1]["timestamp"]


class TestPersistToDb:
    def test_happy_path_commits(self):
        db = MagicMock()
        audit.record_audit(
            user_id=1, action="login", resource="User",
            resource_id="5", details="x", ip_address="1.1.1.1", db=db,
        )
        db.add.assert_called_once()
        db.commit.assert_called_once()
        # DB 路径不写入内存库
        assert audit.get_audit_records() == []

    def test_optional_fields_none(self):
        # resource_id/details 为 None 的分支
        db = MagicMock()
        audit.record_audit(action="ping", db=db)
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_db_error_triggers_rollback(self):
        db = MagicMock()
        db.add.side_effect = RuntimeError("db down")
        # 不向外抛异常
        audit.record_audit(action="x", db=db)
        db.rollback.assert_called_once()

    def test_rollback_failure_swallowed(self):
        db = MagicMock()
        db.add.side_effect = RuntimeError("db down")
        db.rollback.side_effect = RuntimeError("rollback fail")
        # rollback 异常也被吞掉，不向外抛
        audit.record_audit(action="x", db=db)


class TestClearAuditStore:
    def test_clear(self):
        audit.record_audit(action="a")
        assert len(audit.get_audit_records()) == 1
        audit.clear_audit_store()
        assert audit.get_audit_records() == []
