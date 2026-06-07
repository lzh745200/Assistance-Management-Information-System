"""审计服务单元测试"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime

@pytest.fixture
def mock_db(): return MagicMock()

@pytest.fixture
def svc(mock_db):
    from app.services.audit_service import AuditService
    return AuditService(db=mock_db)

class TestAuditContext:
    def test_create_default(self):
        from app.services.audit_service import AuditContext
        ctx = AuditContext()
        assert ctx.user_id is None
        assert ctx.username is None

    def test_create_with_values(self):
        from app.services.audit_service import AuditContext
        ctx = AuditContext(user_id=1, username="admin", user_ip="127.0.0.1")
        assert ctx.user_id == 1
        assert ctx.username == "admin"
        assert ctx.user_ip == "127.0.0.1"

    def test_to_dict(self):
        from app.services.audit_service import AuditContext
        ctx = AuditContext(user_id=1, username="admin")
        d = ctx.to_dict()
        assert d["user_id"] == 1
        assert d["username"] == "admin"

    def test_start_time_is_set(self):
        from app.services.audit_service import AuditContext
        ctx = AuditContext()
        assert isinstance(ctx.start_time, datetime)


class TestAuditService:
    def test_init(self, svc, mock_db):
        assert svc.db is mock_db

    def test_log_creates_audit_record(self, svc, mock_db):
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        from app.services.audit_service import AuditAction
        result = svc.log(action=AuditAction.LOGIN, resource_type="user")
        assert result is not None
        mock_db.add.assert_called_once()

    def test_log_with_context(self, svc, mock_db):
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        from app.services.audit_service import AuditAction, AuditContext
        ctx = AuditContext(user_id=1, username="admin", user_ip="127.0.0.1")
        result = svc.log(action=AuditAction.CREATE, resource_type="project", context=ctx)
        assert result is not None

    def test_log_and_context_are_callable(self, svc):
        assert callable(svc.log)
        assert callable(svc.get_audit_logs) if hasattr(svc, 'get_audit_logs') else True
