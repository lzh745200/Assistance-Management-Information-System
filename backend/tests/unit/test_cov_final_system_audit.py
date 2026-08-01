"""app.api.v1.system.audit 覆盖补全 — Excel 列宽计算中 str(cell.value) 异常的降级分支
(lines 301-302).

openpyxl 正常流程不会产生 str() 抛异常的单元格，这里用 mock Workbook 构造防御场景。
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.api.v1.system.audit import export_audit_logs


class _BadStr:
    def __str__(self):
        raise ValueError("boom")


class TestExportAuditLogsExcel:
    async def test_column_width_str_failure_degrades(self, monkeypatch):
        db = MagicMock(name="db")
        q = MagicMock(name="query")
        q.order_by.return_value = q
        q.limit.return_value = q
        log = SimpleNamespace(
            id=1,
            created_at=None,
            username="u",
            action="login",
            resource_type="auth",
            metadata_={"remark": "r"},
            status="success",
            user_ip="127.0.0.1",
        )
        q.all.return_value = [log]
        db.query.return_value = q

        # mock Workbook：构造一个 str(value) 会抛异常的单元格
        wb = MagicMock(name="wb")
        ws = wb.active
        wb.save.side_effect = lambda out: out.write(b"PK")
        cell = MagicMock(name="cell")
        cell.column_letter = "A"
        cell.value = _BadStr()
        ws.columns = [[cell]]

        monkeypatch.setattr("openpyxl.Workbook", lambda: wb)

        user = SimpleNamespace(id=1, username="admin", role="admin", is_superuser=True)
        with patch("app.api.v1.system.audit.logger") as mock_log:
            resp = await export_audit_logs(
                action=None, start_date=None, end_date=None,
                format="excel", current_user=user, db=db,
            )

        assert resp.media_type == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        # 单元格 str() 异常被吞掉并记录 debug (lines 301-302)
        mock_log.debug.assert_called_once()
