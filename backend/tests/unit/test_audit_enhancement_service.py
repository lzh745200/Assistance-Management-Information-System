from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest

from app.models.audit import AuditAction, AuditStatus
from app.services.audit_enhancement_service import AuditEnhancementService


class TestCreateAuditLog:
    def test_with_id_and_username(self):
        db = MagicMock()
        user = MagicMock(id=1, username="admin")
        log = AuditEnhancementService.create_audit_log(
            db, AuditAction.CREATE, user, "user", "123", detail="created",
        )
        assert log.user_id == 1
        assert log.username == "admin"
        assert log.action == "create"
        assert log.resource_type == "user"
        assert log.resource_id == "123"
        assert log.status == "success"
        assert log.level == "info"
        assert log.metadata_ == {"detail": "created"}
        db.add.assert_called_once_with(log)
        # 修复后改为显式 commit（原 flush 会让无 commit 的调用方静默丢失审计）
        db.commit.assert_called_once()

    def test_without_detail(self):
        db = MagicMock()
        user = MagicMock(id=2, username="editor")
        log = AuditEnhancementService.create_audit_log(
            db, AuditAction.UPDATE, user, "project", "456",
        )
        assert log.metadata_ is None

    def test_user_with_full_name_only(self):
        db = MagicMock()
        user = type("FakeUser", (), {"id": 3, "full_name": "FullOnly"})()
        log = AuditEnhancementService.create_audit_log(
            db, AuditAction.CREATE, user, "report", "789",
        )
        assert log.username == "FullOnly"

    def test_user_no_attributes(self):
        db = MagicMock()
        log = AuditEnhancementService.create_audit_log(
            db, AuditAction.DELETE, object(), "file", "101",
        )
        assert log.user_id is None
        assert log.username is None


class TestLogEntityChanges:
    def test_create(self):
        db = MagicMock()
        user = MagicMock(id=1, username="admin")
        log = AuditEnhancementService.log_entity_changes(
            db, AuditAction.CREATE, user, "project", "1",
            None, {"name": "New"}, detail="creation",
        )
        assert log is not None
        assert log.action == "create"

    def test_update(self):
        db = MagicMock()
        user = MagicMock(id=1, username="admin")
        log = AuditEnhancementService.log_entity_changes(
            db, AuditAction.UPDATE, user, "project", "1",
            {"name": "Old"}, {"name": "New"},
        )
        assert log is not None

    def test_delete(self):
        db = MagicMock()
        user = MagicMock(id=1, username="admin")
        log = AuditEnhancementService.log_entity_changes(
            db, AuditAction.DELETE, user, "project", "1",
            {"name": "Old"}, None,
        )
        assert log is not None

    def test_unknown_action_falls_back_to_value(self):
        db = MagicMock()
        user = MagicMock(id=1, username="admin")
        log = AuditEnhancementService.log_entity_changes(
            db, AuditAction.LOGIN, user, "session", "1",
            {"old": "v"}, {"new": "v"},
        )
        assert log is not None


class TestRecordChanges:
    def test_create_with_data(self):
        db = MagicMock()
        log_mock = MagicMock(id=1)
        AuditEnhancementService.record_changes(
            db, log_mock, None, {"name": "N", "status": "A", "id": 99}, "create",
        )
        assert db.add.call_count == 2
        fields = {c.args[0].field_name for c in db.add.call_args_list}
        assert fields == {"name", "status"}
        for c in db.add.call_args_list:
            ch = c.args[0]
            assert ch.old_value is None
            assert ch.change_type == "create"

    def test_create_with_key_fields(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1), None,
            {"name": "N", "status": "A", "desc": "D"}, "create",
            key_fields=["name"],
        )
        fields = {c.args[0].field_name for c in db.add.call_args_list}
        assert fields == {"name"}

    def test_create_no_new_data(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1), None, None, "create",
        )
        db.add.assert_not_called()

    def test_update_with_changes(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1),
            {"name": "O", "status": "off", "extra": "same"},
            {"name": "N", "status": "on", "extra": "same", "id": 1},
            "update",
        )
        fields = {c.args[0].field_name for c in db.add.call_args_list}
        assert fields == {"name", "status"}

    def test_update_with_key_fields(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1),
            {"name": "O", "status": "off"},
            {"name": "N", "status": "on"},
            "update",
            key_fields=["name"],
        )
        fields = {c.args[0].field_name for c in db.add.call_args_list}
        assert fields == {"name"}

    def test_update_no_changes_same_values(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1),
            {"name": "S", "status": "S"},
            {"name": "S", "status": "S"},
            "update",
        )
        db.add.assert_not_called()

    def test_update_no_old_data(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1), None, {"name": "N"}, "update",
        )
        db.add.assert_not_called()

    def test_update_no_new_data(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1), {"name": "O"}, None, "update",
        )
        db.add.assert_not_called()

    def test_delete_with_data(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1),
            {"name": "Del", "status": "gone", "id": 1}, None, "delete",
        )
        fields = {c.args[0].field_name for c in db.add.call_args_list}
        assert fields == {"name", "status"}
        for c in db.add.call_args_list:
            ch = c.args[0]
            assert ch.new_value is None
            assert ch.change_type == "delete"

    def test_delete_with_key_fields(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1),
            {"name": "Del", "status": "gone"}, None, "delete",
            key_fields=["name"],
        )
        fields = {c.args[0].field_name for c in db.add.call_args_list}
        assert fields == {"name"}

    def test_delete_no_old_data(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1), None, None, "delete",
        )
        db.add.assert_not_called()

    def test_unknown_change_type_noop(self):
        db = MagicMock()
        AuditEnhancementService.record_changes(
            db, MagicMock(id=1), {"n": "o"}, {"n": "n"}, "bogus",
        )
        db.add.assert_not_called()


class TestSerializeValue:
    def test_none(self):
        assert AuditEnhancementService._serialize_value(None) is None

    def test_str(self):
        assert AuditEnhancementService._serialize_value("hello") == "hello"

    def test_int(self):
        assert AuditEnhancementService._serialize_value(42) == 42

    def test_float(self):
        assert AuditEnhancementService._serialize_value(3.14) == 3.14

    def test_bool(self):
        assert AuditEnhancementService._serialize_value(True) is True
        assert AuditEnhancementService._serialize_value(False) is False

    def test_datetime(self):
        dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        assert AuditEnhancementService._serialize_value(dt) == "2024-01-01T12:00:00+00:00"

    def test_list(self):
        assert AuditEnhancementService._serialize_value([1, 2]) == [1, 2]

    def test_dict(self):
        assert AuditEnhancementService._serialize_value({"k": "v"}) == {"k": "v"}

    def test_other(self):
        class Obj:
            def __str__(self):
                return "custom"
        assert AuditEnhancementService._serialize_value(Obj()) == "custom"


class TestGetChangeHistory:
    def test_no_audit_logs_returns_empty(self):
        db = MagicMock()
        q = MagicMock()
        db.query.return_value = q
        q.filter.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        assert AuditEnhancementService.get_change_history(db, "project", "1") == []

    def test_with_logs_and_changes(self):
        db = MagicMock()

        log1 = MagicMock(id=1, user_id=1, username="admin", action="update",
                         created_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
        log2 = MagicMock(id=2, user_id=2, username="editor", action="create",
                         created_at=datetime(2024, 1, 2, tzinfo=timezone.utc))

        q1 = MagicMock(name="audit_log_query")
        q2 = MagicMock(name="audit_change_query")
        db.query.side_effect = [q1, q2]

        q1.filter.return_value = q1
        q1.order_by.return_value = q1
        q1.limit.return_value = q1
        q1.all.return_value = [log1, log2]

        change1 = MagicMock(field_name="name", old_value="O", new_value="N",
                            change_type="update", audit_log_id=1)
        change2 = MagicMock(field_name="status", old_value="off", new_value="on",
                            change_type="update", audit_log_id=1)

        q2.filter.return_value = q2
        q2.all.return_value = [change1, change2]

        history = AuditEnhancementService.get_change_history(db, "project", "1")

        assert len(history) == 2
        assert history[0]["username"] == "admin"
        assert len(history[0]["changes"]) == 2
        assert history[0]["changes"][0]["field"] == "name"
        assert history[0]["changes"][0]["old_value"] == "O"
        assert history[0]["changes"][0]["new_value"] == "N"
        assert history[1]["username"] == "editor"
        assert history[1]["changes"] == []

    def test_created_at_none(self):
        db = MagicMock()
        log1 = MagicMock(id=1, user_id=1, username="admin", action="update",
                         created_at=None)

        q1 = MagicMock(name="audit_log_query")
        q2 = MagicMock(name="audit_change_query")
        db.query.side_effect = [q1, q2]

        q1.filter.return_value = q1
        q1.order_by.return_value = q1
        q1.limit.return_value = q1
        q1.all.return_value = [log1]

        q2.filter.return_value = q2
        q2.all.return_value = []

        history = AuditEnhancementService.get_change_history(db, "project", "1")
        assert len(history) == 1
        assert history[0]["timestamp"] is None

    def test_logs_without_changes(self):
        db = MagicMock()
        log1 = MagicMock(id=1, user_id=1, username="admin", action="update",
                         created_at=datetime(2024, 1, 1, tzinfo=timezone.utc))

        q1 = MagicMock(name="audit_log_query")
        q2 = MagicMock(name="audit_change_query")
        db.query.side_effect = [q1, q2]

        q1.filter.return_value = q1
        q1.order_by.return_value = q1
        q1.limit.return_value = q1
        q1.all.return_value = [log1]

        q2.filter.return_value = q2
        q2.all.return_value = []

        history = AuditEnhancementService.get_change_history(db, "project", "1")
        assert len(history) == 1
        assert history[0]["changes"] == []
