"""app.api.v1.system.audit 覆盖率攻坚测试（补充 test_system_audit_api.py 未覆盖分支）

覆盖点：
- get_audit_service / get_security_service DI 提供器
- export_audit_logs：excel 格式全路径（样式/数据行/列宽）
- excel 因 ImportError 回退 CSV、csv 格式直出
"""

import sys
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import app.api.v1.system.audit as au


def _user(role="admin"):
    return SimpleNamespace(id=1, username="admin", role=role)


def _log(**kw):
    defaults = dict(
        id=1, created_at=datetime(2026, 7, 1, 12, 0, 0), username="admin",
        action="login", resource_type="auth", metadata_={"remark": "备注"},
        status="success", user_ip="127.0.0.1",
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _db_with_logs(logs):
    q = MagicMock()
    q.order_by.return_value = q
    q.filter.return_value = q
    q.limit.return_value = q
    q.all.return_value = logs
    db = MagicMock()
    db.query = MagicMock(return_value=q)
    return db


class TestServiceProviders:
    def test_get_audit_service(self):
        svc = au.get_audit_service(MagicMock())
        assert svc is not None

    def test_get_security_service(self):
        svc = au.get_security_service(MagicMock())
        assert svc is not None


class TestExportAuditLogs:
    async def test_excel_format_full_path(self):
        db = _db_with_logs([_log(), _log(id=2, created_at=None, metadata_="not-a-dict")])
        resp = await au.export_audit_logs(
            action="login", start_date=datetime(2026, 1, 1), end_date=datetime(2026, 12, 31),
            format="excel", current_user=_user(), db=db,
        )
        assert "spreadsheetml" in resp.media_type

    async def test_excel_import_error_falls_back_csv(self):
        db = _db_with_logs([_log()])
        with patch.dict(sys.modules, {"openpyxl": None, "openpyxl.styles": None}):
            resp = await au.export_audit_logs(
                action=None, start_date=None, end_date=None,
                format="excel", current_user=_user(), db=db,
            )
        assert resp.media_type == "text/csv"

    async def test_csv_format(self):
        db = _db_with_logs([_log()])
        resp = await au.export_audit_logs(
            action=None, start_date=None, end_date=None,
            format="csv", current_user=_user(), db=db,
        )
        assert resp.media_type == "text/csv"
