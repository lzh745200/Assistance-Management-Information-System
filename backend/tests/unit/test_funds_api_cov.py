"""app.api.v1.funds 覆盖率攻坚测试（补充既有测试未覆盖分支）

覆盖缺口：
- 144：_fund_to_dict 的 school 关联分支
- 214,216：列表 village_id / school_id 过滤
- 295：权限过滤后记录为空 → 403
- 352：GET /{fund_id} 返回 viewableBecause
- 710,712：utilization-rate 的 year_start/year_end 过滤
- 755-766 / 789-800：village / school 经费汇总（含 year 过滤）
- 916：附件预览 mime 回退（无扩展名 → file_type）
- 1008-1049：附件上传全路径
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_user

BASE = "/api/v1/funds"


@pytest.fixture
def client():
    from app.main import app

    original = app.dependency_overrides.copy()
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="admin", full_name="管理员", role="admin", is_superuser=True
    )
    with patch("app.api.v1.funds.apply_scope_filter", side_effect=lambda stmt, *a, **kw: stmt):
        yield TestClient(app, raise_server_exceptions=False), db
    app.dependency_overrides = original


# ==================== 144：_fund_to_dict school 分支 ====================


def test_fund_to_dict_school_branch():
    import app.api.v1.funds as funds_mod

    fund = SimpleNamespace(
        project=None,
        village=None,
        school=SimpleNamespace(name="希望小学"),
    )
    # 绕过 Fund.__table__.columns 迭代（SimpleNamespace 非 ORM）——patch 表列
    col = SimpleNamespace(name="id")
    with patch.object(funds_mod.Fund, "__table__") as t:
        t.columns = [col]
        fund.id = 1
        result = funds_mod._fund_to_dict(fund)
    assert result["school_name"] == "希望小学"


# ==================== 214,216：列表过滤分支 ====================


class TestListFilters:
    def _mk_db(self, db):
        row = MagicMock()
        row.scalars.return_value.all.return_value = []
        db.execute.return_value = row
        db.query.return_value.count.return_value = 0

    def test_filter_by_village_id(self, client):
        c, db = client
        self._mk_db(db)
        resp = c.get(f"{BASE}?village_id=3")
        assert resp.status_code == 200

    def test_filter_by_school_id(self, client):
        c, db = client
        self._mk_db(db)
        resp = c.get(f"{BASE}?school_id=5")
        assert resp.status_code == 200


# ==================== 295/352：详情权限与 viewableBecause ====================


class TestGetFundDetail:
    def test_permission_filtered_403(self, client):
        """295：记录存在但数据权限过滤后为空 → 403"""
        c, db = client
        r_exists = MagicMock()
        r_exists.scalar_one_or_none.return_value = 1
        r_scoped = MagicMock()
        r_scoped.scalar_one_or_none.return_value = None
        db.execute.side_effect = [r_exists, r_scoped]
        resp = c.get(f"{BASE}/1")
        assert resp.status_code == 403

    def test_detail_contains_viewable_because(self, client):
        """352：成功详情含 viewableBecause 字段"""
        c, db = client
        r_exists = MagicMock()
        r_exists.scalar_one_or_none.return_value = 1
        r_scoped = MagicMock()
        r_scoped.scalar_one_or_none.return_value = SimpleNamespace(id=1)
        db.execute.side_effect = [r_exists, r_scoped]
        with patch("app.api.v1.funds._fund_to_dict", return_value={"id": 1}), \
             patch("app.api.v1.funds.build_viewable_because", return_value="组织内可见"):
            resp = c.get(f"{BASE}/1")
        assert resp.status_code == 200
        assert resp.json()["data"]["viewableBecause"] == "组织内可见"


# ==================== 710,712：utilization-rate 年份过滤 ====================


class TestUtilizationRate:
    def _mk_db(self, db):
        row = MagicMock()
        row.one.return_value = SimpleNamespace(planned=100.0, actual=80.0)
        db.execute.return_value = row

    def test_year_start_filter(self, client):
        c, db = client
        self._mk_db(db)
        resp = c.get(f"{BASE}/supported-village/statistics/utilization-rate?year_start=2024")
        assert resp.status_code == 200

    def test_year_end_filter(self, client):
        c, db = client
        self._mk_db(db)
        resp = c.get(f"{BASE}/supported-village/statistics/utilization-rate?year_end=2026")
        assert resp.status_code == 200


# ==================== 755-766 / 789-800：village / school 汇总 ====================


class TestVillageSchoolSummary:
    def _mk_db(self, db):
        row = MagicMock()
        row.one.return_value = SimpleNamespace(
            count=2, planned=100.0, approved=90.0, allocated=80.0, used=70.0
        )
        db.execute.return_value = row

    def test_village_summary_no_year(self, client):
        c, db = client
        self._mk_db(db)
        resp = c.get(f"{BASE}/village/3/summary")
        assert resp.status_code == 200

    def test_village_summary_with_year(self, client):
        c, db = client
        self._mk_db(db)
        resp = c.get(f"{BASE}/village/3/summary?year=2026")
        assert resp.status_code == 200

    def test_school_summary_no_year(self, client):
        c, db = client
        self._mk_db(db)
        resp = c.get(f"{BASE}/school/5/summary")
        assert resp.status_code == 200

    def test_school_summary_with_year(self, client):
        c, db = client
        self._mk_db(db)
        resp = c.get(f"{BASE}/school/5/summary?year=2025")
        assert resp.status_code == 200


# ==================== 916：附件预览 mime 回退 ====================


class TestAttachmentPreview:
    def test_mime_fallback_to_file_type(self, client):
        """916：无扩展名文件 guess_type=None → 回退 att.file_type"""
        c, db = client
        att = SimpleNamespace(id=1, fund_id=1, file_path="/uploads/noext", file_type="application/pdf", file_name="f")
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = att
        db.query.return_value = q
        with patch("app.api.v1.funds._get_fund_or_404", return_value=SimpleNamespace(id=1)), \
             patch("app.api.v1.funds.get_attachment_response", return_value={"ok": True}) as gar:
            resp = c.get(f"{BASE}/attachments/1/preview")
        assert resp.status_code == 200
        assert gar.call_args.kwargs["media_type"] == "application/pdf"


# ==================== 1008-1049：附件上传 ====================


class TestAttachmentUpload:
    def test_upload_full_path(self, client):
        c, db = client
        file_info = {
            "file_name": "合同.pdf", "file_path": "/uploads/funds/1/x.pdf",
            "file_size": 1024, "file_type": "application/pdf",
        }
        attachment = MagicMock()
        attachment.to_dict.return_value = {"id": 1, "file_name": "合同.pdf"}
        with patch("app.api.v1.funds._get_fund_or_404", return_value=SimpleNamespace(id=1)), \
             patch("app.api.v1.funds.save_upload_file", new=AsyncMock(return_value=file_info)), \
             patch("app.api.v1.funds.FundAttachment", return_value=attachment), \
             patch("app.api.v1.funds.FundOperationLog", return_value=MagicMock()), \
             patch("app.api.v1.funds.write_work_log") as wwl, \
             patch("app.api.v1.funds.safe_commit"):
            resp = c.post(
                f"{BASE}/1/attachments?category=contract&description=经费合同",
                files={"file": ("合同.pdf", b"PDF-DATA", "application/pdf")},
            )
        assert resp.status_code == 200
        assert resp.json()["data"]["file_name"] == "合同.pdf"
        db.add.assert_called()
        db.refresh.assert_called_once_with(attachment)
        wwl.assert_called_once()
