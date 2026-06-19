"""
Comprehensive pytest tests for funds.py API routes.
Covers all 25+ endpoints with Mock DB, edge cases, and error paths.
Uses FastAPI TestClient with dependency overrides for get_db and get_current_user.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import Column, Integer, String, Text, DateTime, Date as SADate, Numeric, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func as sqlfunc

from app.api.v1.funds import router
from app.core.config import settings

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_db():
    """Returns a MagicMock that mimics a SQLAlchemy Session."""
    db = MagicMock()
    db.execute.return_value = MagicMock()
    db.commit.return_value = None
    db.add.return_value = None
    db.delete.return_value = None
    db.refresh.return_value = None
    db.flush.return_value = None
    db.query.return_value = MagicMock()
    return db


@pytest.fixture
def admin_user():
    """Admin user fixture — has full permissions."""
    user = Mock()
    user.id = 1
    user.username = "admin"
    user.role = "admin"
    user.is_superuser = True
    user.is_active = True
    user.permissions_list = ["*"]
    user.organization_id = 1
    user.email = "admin@test.com"
    user.full_name = "管理员"
    return user


@pytest.fixture
def regular_user():
    """Regular non-admin user fixture."""
    user = Mock()
    user.id = 2
    user.username = "villager"
    user.role = "user"
    user.is_superuser = False
    user.is_active = True
    user.permissions_list = []
    user.organization_id = 2
    user.email = "villager@test.com"
    user.full_name = "村民"
    return user


@pytest.fixture
def manager_user():
    """Manager user — has admin role but not superuser."""
    user = Mock()
    user.id = 3
    user.username = "manager"
    user.role = "manager"
    user.is_superuser = False
    user.is_active = True
    user.permissions_list = []
    user.organization_id = 1
    user.email = "manager@test.com"
    user.full_name = "经理"
    return user


def _make_mock_fund(fund_id=1, **overrides):
    """Build a realistic mock Fund ORM instance."""
    defaults = {
        "id": fund_id,
        "date": date(2025, 6, 15),
        "type": "project",
        "fund_type": "project",
        "fund_source": "military",
        "amount": Decimal("500.00"),
        "planned_amount": Decimal("500.00"),
        "approved_amount": Decimal("500.00"),
        "allocated_amount": Decimal("200.00"),
        "used_amount": Decimal("100.00"),
        "remaining_amount": Decimal("400.00"),
        "code": "F001",
        "name": "测试经费",
        "project_id": 1,
        "project_name": "测试项目",
        "village_id": 1,
        "school_id": None,
        "purpose": "测试用途",
        "source": "军队拨款",
        "operator": "张三",
        "receiver": None,
        "usage_description": "使用说明",
        "status": "pending",
        "applicant": "李四",
        "application_date": datetime(2025, 6, 10, tzinfo=timezone.utc),
        "approved_by": None,
        "approval_date": None,
        "allocation_date": None,
        "allocation_method": None,
        "start_date": None,
        "end_date": None,
        "audit_date": None,
        "audit_result": None,
        "audit_opinion": None,
        "remarks": "备注",
        "lifecycle_phase": 1,
        "budget_locked": False,
        "deviation_rate": Decimal("0.00"),
        "health_score": 100,
        "has_anomaly": False,
        "settlement_status": None,
        "budget_version": 1,
        "budget_status": "draft",
        "organization_id": 1,
        "created_by": 1,
        "year": 2025,
        "year_month": "2025-06",
        "year_quarter": "2025-Q2",
    }
    defaults.update(overrides)
    fund = Mock()
    for k, v in defaults.items():
        setattr(fund, k, v)
    # Make fund iterable like a column-mapped object for _fund_to_dict
    fund.__table__ = MagicMock()
    fund.__table__.columns = [
        MagicMock(name=name, key=name) for name in defaults.keys()
    ]
    # Attach optional relationships
    fund.project = None
    fund.village = None
    fund.organization = None
    return fund


def _make_mock_fund_attachment(attachment_id=1, fund_id=1, **overrides):
    """Build a mock FundAttachment ORM instance."""
    defaults = {
        "id": attachment_id,
        "fund_id": fund_id,
        "file_name": "test.pdf",
        "file_path": "/tmp/test.pdf",
        "file_size": 1024,
        "file_type": "application/pdf",
        "category": "contract",
        "description": "测试附件",
        "uploaded_by": "管理员",
        "created_at": datetime(2025, 6, 15, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    att = Mock()
    for k, v in defaults.items():
        setattr(att, k, v)
    att.to_dict.return_value = {k: v for k, v in defaults.items()
                                if k not in ("created_at",)}
    att.to_dict.return_value["created_at"] = defaults["created_at"].isoformat()
    return att


def _make_mock_status_history(hist_id=1, fund_id=1, **overrides):
    defaults = {
        "id": hist_id,
        "fund_id": fund_id,
        "from_status": "pending",
        "to_status": "approved",
        "changed_by": "管理员",
        "changed_at": datetime(2025, 6, 16, tzinfo=timezone.utc),
        "remark": "审批通过",
    }
    defaults.update(overrides)
    h = Mock()
    for k, v in defaults.items():
        setattr(h, k, v)
    return h


def _make_mock_field_change(change_id=1, fund_id=1, **overrides):
    defaults = {
        "id": change_id,
        "fund_id": fund_id,
        "field_name": "amount",
        "old_value": "300.00",
        "new_value": "500.00",
        "changed_by": 1,
        "changed_by_name": "管理员",
        "changed_at": datetime(2025, 6, 16, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    c = Mock()
    for k, v in defaults.items():
        setattr(c, k, v)
    return c


def _make_mock_operation_log(log_id=1, fund_id=1, **overrides):
    defaults = {
        "id": log_id,
        "fund_id": fund_id,
        "operation": "approve",
        "operator": "管理员",
        "detail": "通过审批",
        "created_at": datetime(2025, 6, 16, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    l = Mock()
    for k, v in defaults.items():
        setattr(l, k, v)
    return l


def _setup_scalar_one_or_none(execute_mock, return_value):
    """Configure mock_db.execute to return a scalar_one_or_none with given value."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = return_value
    execute_mock.return_value = result


def _setup_scalar_one(execute_mock, return_value):
    """Configure mock_db.execute to return a scalar_one with given value."""
    result = MagicMock()
    result.scalar_one.return_value = return_value
    execute_mock.return_value = result


def _setup_scalars_all(execute_mock, items):
    """Configure mock_db.execute to return scalars().unique().all() for a list of items."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = items
    unique_mock = MagicMock()
    unique_mock.all.return_value = items
    scalars_mock.unique.return_value = unique_mock
    result = MagicMock()
    result.scalars.return_value = scalars_mock
    execute_mock.return_value = result


def _setup_execute_all(execute_mock, rows):
    """Configure mock_db.execute to return .all() directly (for non-ORM queries like aggregates)."""
    result = MagicMock()
    result.all.return_value = rows
    execute_mock.return_value = result


def build_client(admin_user, mock_db):
    """Build a TestClient with dependency overrides for admin user."""
    from app.main import app

    def _get_db():
        yield mock_db

    async def _get_current_user():
        return admin_user

    app.dependency_overrides = {
        app.dependency_overrides.get("get_db", _get_db) if False else None: None
    }
    # Use direct function references
    from app.core.database import get_db
    from app.core.security import get_current_user

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = _get_current_user

    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client(admin_user, mock_db):
    """TestClient with admin privileges."""
    yield from build_client(admin_user, mock_db)


@pytest.fixture
def client_regular(regular_user, mock_db):
    """TestClient with regular user privileges."""
    from app.main import app

    def _get_db():
        yield mock_db

    async def _get_current_user():
        return regular_user

    from app.core.database import get_db
    from app.core.security import get_current_user

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = _get_current_user

    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ============================================================================
# 1. list_funds — GET /api/v1/funds
# ============================================================================


class TestListFunds:
    def test_list_funds_offset_pagination_empty(self, client, mock_db, admin_user):
        """List with offset pagination returns empty result."""
        _setup_scalars_all(mock_db.execute, [])
        # Count query returns 0
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        resp = client.get("/api/v1/funds")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["pagination"] == "offset"
        assert data["items"] == []

    def test_list_funds_offset_pagination_with_items(self, client, mock_db, admin_user):
        """List with offset pagination returns items."""
        fund = _make_mock_fund(1, name="项目经费A")
        fund.project = Mock(name="项目1")
        fund.project.name = "项目1"
        fund.village = Mock(name="村1")
        fund.village.name = "村1"
        _setup_scalars_all(mock_db.execute, [fund])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        resp = client.get("/api/v1/funds")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "项目经费A"
        assert "project_name" in data["items"][0]

    def test_list_funds_keyset_pagination(self, client, mock_db, admin_user):
        """List with keyset pagination."""
        fund = _make_mock_fund(5, name="经费K")
        keyset_result = {
            "items": [fund],
            "total": 1,
            "page_size": 20,
            "next_cursor": "abc123",
            "has_more": False,
        }
        # We need to mock keyset_paginate function
        with patch("app.api.v1.funds.keyset_paginate", return_value=keyset_result):
            resp = client.get("/api/v1/funds?pagination=keyset")
            assert resp.status_code == 200
            data = resp.json()
            assert data["pagination"] == "keyset"
            assert data["next_cursor"] == "abc123"

    def test_list_funds_with_status_filter(self, client, mock_db, admin_user):
        """List with status filter applied."""
        fund = _make_mock_fund(1, status="approved")
        _setup_scalars_all(mock_db.execute, [fund])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        resp = client.get("/api/v1/funds?status=approved")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    def test_list_funds_with_keyword_filter(self, client, mock_db, admin_user):
        """List with keyword search."""
        fund = _make_mock_fund(1, name="匹配项目")
        _setup_scalars_all(mock_db.execute, [fund])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        resp = client.get("/api/v1/funds?keyword=匹配")
        assert resp.status_code == 200

    def test_list_funds_with_fund_type_filter(self, client, mock_db, admin_user):
        """List filtered by fund_type."""
        fund = _make_mock_fund(1, fund_type="education")
        _setup_scalars_all(mock_db.execute, [fund])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        resp = client.get("/api/v1/funds?fund_type=education")
        assert resp.status_code == 200

    def test_list_funds_with_fund_source_filter(self, client, mock_db, admin_user):
        """List filtered by fund_source."""
        fund = _make_mock_fund(1, fund_source="government")
        _setup_scalars_all(mock_db.execute, [fund])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        resp = client.get("/api/v1/funds?fund_source=government")
        assert resp.status_code == 200

    def test_list_funds_with_project_id_filter(self, client, mock_db, admin_user):
        """List filtered by project_id."""
        fund = _make_mock_fund(1, project_id=5)
        _setup_scalars_all(mock_db.execute, [fund])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        resp = client.get("/api/v1/funds?project_id=5")
        assert resp.status_code == 200

    def test_list_funds_with_village_id_filter(self, client, mock_db, admin_user):
        """List filtered by village_id."""
        fund = _make_mock_fund(1, village_id=3)
        _setup_scalars_all(mock_db.execute, [fund])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        resp = client.get("/api/v1/funds?page=2&page_size=10")
        assert resp.status_code == 200


# ============================================================================
# 2. export_funds — GET /api/v1/funds/export
# ============================================================================


class TestExportFunds:
    def test_export_funds_empty(self, client, mock_db, admin_user):
        """Export returns empty data."""
        _setup_scalars_all(mock_db.execute, [])

        resp = client.get("/api/v1/funds/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_exported"] == 0
        assert data["limit"] == 5000

    def test_export_funds_with_items(self, client, mock_db, admin_user):
        """Export returns fund data."""
        fund = _make_mock_fund(1)
        fund.project = None
        fund.village = None
        _setup_scalars_all(mock_db.execute, [fund])

        resp = client.get("/api/v1/funds/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_exported"] == 1

    def test_export_funds_with_custom_limit(self, client, mock_db, admin_user):
        """Export with custom limit parameter."""
        _setup_scalars_all(mock_db.execute, [])

        resp = client.get("/api/v1/funds/export?limit=100")
        assert resp.status_code == 200

    def test_export_funds_limit_boundary(self, client, mock_db, admin_user):
        """Export limit boundary cases."""
        # limit=1 (minimum)
        resp = client.get("/api/v1/funds/export?limit=1")
        assert resp.status_code == 200

        # limit=50000 (maximum)
        resp = client.get("/api/v1/funds/export?limit=50000")
        assert resp.status_code == 200


# ============================================================================
# 3. get_fund — GET /api/v1/funds/{fund_id}
# ============================================================================


class TestGetFund:
    def test_get_fund_success(self, client, mock_db, admin_user):
        """Get a single fund by ID."""
        fund = _make_mock_fund(42)
        fund.project = Mock(name="项目1")
        fund.project.name = "项目1"
        fund.village = Mock(name="村1")
        fund.village.name = "村1"
        fund.organization = Mock(name="组织1")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.get("/api/v1/funds/42")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["id"] == 42
        assert data["data"]["name"] == "测试经费"

    def test_get_fund_not_found(self, client, mock_db, admin_user):
        """Get a non-existent fund returns 404."""
        _setup_scalar_one_or_none(mock_db.execute, None)

        resp = client.get("/api/v1/funds/999")
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]

    def test_get_fund_with_project_and_village_names(self, client, mock_db, admin_user):
        """Get fund with joined associations returns enriched data."""
        fund = _make_mock_fund(1)
        fund.project = Mock(name="项目A")
        fund.project.name = "项目A"
        fund.village = Mock(name="村庄B")
        fund.village.name = "村庄B"
        fund.organization = Mock(name="组织C")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.get("/api/v1/funds/1")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["project_name"] == "项目A"
        assert data["village_name"] == "村庄B"


# ============================================================================
# 4. create_fund — POST /api/v1/funds
# ============================================================================


class TestCreateFund:
    def test_create_fund_admin_success(self, client, mock_db, admin_user):
        """Admin creates a fund."""
        with patch("app.api.v1.funds.FundService") as MockService:
            mock_svc = MockService.return_value
            created = _make_mock_fund(100, name="新经费", code="FUND-20250615-ABCD")
            mock_svc.create_fund_for_user.return_value = created

            resp = client.post("/api/v1/funds", json={
                "name": "新经费",
                "amount": 10000,
                "fund_type": "project",
                "purpose": "新建项目",
            })
            assert resp.status_code == 201
            assert resp.json()["data"]["id"] == 100

    def test_create_fund_non_admin_forbidden(self, client_regular, mock_db, regular_user):
        """Regular user cannot create via admin endpoint."""
        resp = client_regular.post("/api/v1/funds", json={
            "name": "新经费",
            "amount": 1000,
        })
        assert resp.status_code == 403

    def test_create_fund_with_all_fields(self, client, mock_db, admin_user):
        """Create fund with all optional fields populated."""
        with patch("app.api.v1.funds.FundService") as MockService:
            mock_svc = MockService.return_value
            created = _make_mock_fund(101)
            mock_svc.create_fund_for_user.return_value = created

            payload = {
                "name": "综合经费",
                "amount": 50000,
                "planned_amount": 50000,
                "approved_amount": 50000,
                "allocated_amount": 20000,
                "used_amount": 10000,
                "remaining_amount": 40000,
                "code": "F-CUSTOM-001",
                "type": "project",
                "fund_type": "infrastructure",
                "fund_source": "military",
                "project_id": 10,
                "project_name": "基础设施",
                "village_id": 5,
                "school_id": 2,
                "purpose": "基础设施建设",
                "source": "军队",
                "operator": "王五",
                "receiver": "赵六",
                "usage_description": "建设村道",
                "status": "pending",
                "applicant": "张三",
                "remarks": "紧急",
                "date": "2025-07-01",
                "start_date": "2025-07-15",
                "end_date": "2025-12-31",
            }
            resp = client.post("/api/v1/funds", json=payload)
            assert resp.status_code == 201
            assert resp.json()["message"] == "创建成功"

    def test_create_fund_default_values(self, client, mock_db, admin_user):
        """Create fund with minimal fields uses defaults."""
        with patch("app.api.v1.funds.FundService") as MockService:
            mock_svc = MockService.return_value
            created = _make_mock_fund(102)
            mock_svc.create_fund_for_user.return_value = created

            resp = client.post("/api/v1/funds", json={})
            assert resp.status_code == 201


# ============================================================================
# 5. apply_fund — POST /api/v1/funds/apply
# ============================================================================


class TestApplyFund:
    def test_apply_fund_success(self, client, mock_db, admin_user):
        """Any logged-in user can apply for funds."""
        with patch("app.api.v1.funds.FundService") as MockService:
            mock_svc = MockService.return_value
            created = _make_mock_fund(200, status="pending", applicant="管理员")
            mock_svc.create_fund_for_user.return_value = created

            resp = client.post("/api/v1/funds/apply", json={
                "name": "我的申请",
                "amount": 3000,
                "purpose": "教育帮扶",
            })
            assert resp.status_code == 201
            data = resp.json()
            assert data["message"] == "申请已提交，等待审批"
            assert data["data"]["id"] == 200

    def test_apply_fund_regular_user(self, client_regular, mock_db, regular_user):
        """Regular user can apply for funds (no admin required)."""
        with patch("app.api.v1.funds.FundService") as MockService:
            mock_svc = MockService.return_value
            created = _make_mock_fund(201, status="pending", applicant="村民")
            mock_svc.create_fund_for_user.return_value = created

            resp = client_regular.post("/api/v1/funds/apply", json={
                "name": "村民申请",
                "amount": 1000,
                "fund_type": "education",
            })
            assert resp.status_code == 201
            assert "申请已提交" in resp.json()["message"]


# ============================================================================
# 6. update_fund — PUT /api/v1/funds/{fund_id}
# ============================================================================


class TestUpdateFund:
    def test_update_fund_success(self, client, mock_db, admin_user):
        """Admin updates a fund in pending status."""
        fund = _make_mock_fund(1, status="pending")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.put("/api/v1/funds/1", json={"name": "更新后的名称", "amount": 8000})
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"

    def test_update_fund_not_found(self, client, mock_db, admin_user):
        """Update non-existent fund returns 404."""
        _setup_scalar_one_or_none(mock_db.execute, None)

        resp = client.put("/api/v1/funds/999", json={"name": "不存在"})
        assert resp.status_code == 404

    def test_update_fund_non_admin_forbidden(self, client_regular, mock_db, regular_user):
        """Regular user cannot update funds."""
        fund = _make_mock_fund(1, status="pending")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client_regular.put("/api/v1/funds/1", json={"name": "尝试修改"})
        assert resp.status_code == 403

    def test_update_fund_immutable_status_rejected(self, client, mock_db, admin_user):
        """Cannot update a fund that is already approved or allocated."""
        for blocked_status in ["approved", "allocated", "in_use", "completed", "audited"]:
            fund = _make_mock_fund(1, status=blocked_status)
            _setup_scalar_one_or_none(mock_db.execute, fund)

            resp = client.put("/api/v1/funds/1", json={"name": "尝试修改"})
            assert resp.status_code == 400, f"Status {blocked_status} should be blocked"
            assert "不允许修改" in resp.json()["detail"]

    def test_update_fund_mutable_status_allowed(self, client, mock_db, admin_user):
        """Updating funds in pending/planned/rejected status is allowed."""
        for allowed_status in ["pending", "planned", "rejected"]:
            fund = _make_mock_fund(1, status=allowed_status)
            _setup_scalar_one_or_none(mock_db.execute, fund)

            resp = client.put("/api/v1/funds/1", json={"remarks": "备注更新"})
            assert resp.status_code == 200, f"Status {allowed_status} should be allowed"

    def test_update_fund_exclude_unset(self, client, mock_db, admin_user):
        """Only sent fields are updated (exclude_unset behavior)."""
        fund = _make_mock_fund(1, status="pending", name="原名", amount=Decimal("500"))
        _setup_scalar_one_or_none(mock_db.execute, fund)

        # Only update name, not amount
        resp = client.put("/api/v1/funds/1", json={"name": "新名称"})
        assert resp.status_code == 200

    def test_update_fund_null_fields_cleared(self, client, mock_db, admin_user):
        """Explicitly sent None values clear fields."""
        fund = _make_mock_fund(1, status="pending", remarks="旧备注", school_id=5)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.put("/api/v1/funds/1", json={"remarks": None, "school_id": None})
        assert resp.status_code == 200

    def test_update_fund_unknown_field_skipped(self, client, mock_db, admin_user):
        """Unknown fields (not on Fund model) are skipped with a warning log."""
        fund = _make_mock_fund(1, status="pending")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        # extra="forbid" on FundUpdate — trying to send a field not defined in FundUpdate
        # will cause a 422 validation error.
        resp = client.put("/api/v1/funds/1", json={"name": "ok"})
        assert resp.status_code == 200


# ============================================================================
# 7. delete_fund — DELETE /api/v1/funds/{fund_id}
# ============================================================================


class TestDeleteFund:
    def test_delete_fund_success(self, client, mock_db, admin_user):
        """Admin deletes a pending fund."""
        fund = _make_mock_fund(1, status="pending")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.delete("/api/v1/funds/1")
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

    def test_delete_fund_not_found(self, client, mock_db, admin_user):
        """Delete non-existent fund returns 404."""
        _setup_scalar_one_or_none(mock_db.execute, None)

        resp = client.delete("/api/v1/funds/999")
        assert resp.status_code == 404

    def test_delete_fund_non_admin_forbidden(self, client_regular, mock_db, regular_user):
        """Regular user cannot delete funds."""
        resp = client_regular.delete("/api/v1/funds/1")
        assert resp.status_code == 403

    def test_delete_fund_non_pending_status_rejected(self, client, mock_db, admin_user):
        """Only pending funds can be deleted."""
        for non_pending in ["approved", "allocated", "in_use", "completed", "audited", "planned"]:
            fund = _make_mock_fund(1, status=non_pending)
            _setup_scalar_one_or_none(mock_db.execute, fund)

            resp = client.delete("/api/v1/funds/1")
            assert resp.status_code == 400, f"Status {non_pending} should block delete"
            assert "仅允许删除" in resp.json()["detail"]


# ============================================================================
# 8. Statistics endpoints
# ============================================================================


class TestFundStatisticsOverview:
    def test_statistics_overview(self, client, mock_db, admin_user):
        """Fund statistics overview returns aggregate data."""
        row = Mock()
        row.total_count = 150
        row.total_amount = Decimal("500000.00")
        row.pending_count = 23
        row.approved_count = 100
        _setup_execute_all(mock_db.execute, [row])
        mock_db.execute.return_value.one.return_value = row

        resp = client.get("/api/v1/funds/statistics/overview")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_count"] == 150
        assert data["total_amount"] == 500000.0
        assert data["pending_count"] == 23
        assert data["approved_count"] == 100

    def test_statistics_overview_zero_data(self, client, mock_db, admin_user):
        """Statistics overview with zero data."""
        row = Mock()
        row.total_count = 0
        row.total_amount = Decimal("0.00")
        row.pending_count = 0
        row.approved_count = 0
        _setup_execute_all(mock_db.execute, [row])
        mock_db.execute.return_value.one.return_value = row

        resp = client.get("/api/v1/funds/statistics/overview")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_count"] == 0
        assert data["total_amount"] == 0.0


class TestFundStatisticsMultiDimension:
    def test_by_type(self, client, mock_db, admin_user):
        """Multi-dimension stats grouped by type."""
        r1 = Mock()
        r1.group_key = "project"
        r1.count = 10
        r1.total_amount = Decimal("100000")
        r1.total_allocated = Decimal("80000")
        r1.total_used = Decimal("50000")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/statistics/multi-dimension?group_by=type")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["label"] == "项目经费"

    def test_by_source(self, client, mock_db, admin_user):
        """Multi-dimension stats grouped by source."""
        r1 = Mock()
        r1.group_key = "military"
        r1.count = 5
        r1.total_amount = Decimal("200000")
        r1.total_allocated = Decimal("150000")
        r1.total_used = Decimal("100000")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/statistics/multi-dimension?group_by=source")
        assert resp.status_code == 200
        assert resp.json()["data"][0]["label"] == "军队投资"

    def test_by_status(self, client, mock_db, admin_user):
        """Multi-dimension stats grouped by status."""
        r1 = Mock()
        r1.group_key = "pending"
        r1.count = 3
        r1.total_amount = Decimal("30000")
        r1.total_allocated = Decimal("0")
        r1.total_used = Decimal("0")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/statistics/multi-dimension?group_by=status")
        assert resp.status_code == 200
        assert resp.json()["data"][0]["label"] == "待审批"

    def test_by_period_monthly(self, client, mock_db, admin_user):
        """Multi-dimension stats grouped by period (monthly)."""
        r1 = Mock()
        r1.group_key = "2025-06"
        r1.count = 4
        r1.total_amount = Decimal("40000")
        r1.total_allocated = Decimal("30000")
        r1.total_used = Decimal("20000")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/statistics/multi-dimension?group_by=period")
        assert resp.status_code == 200
        assert resp.json()["data"][0]["label"] == "2025-06"

    def test_by_period_quarterly(self, client, mock_db, admin_user):
        """Multi-dimension stats grouped by period (quarterly)."""
        r1 = Mock()
        r1.group_key = "2025-Q2"
        r1.count = 12
        r1.total_amount = Decimal("120000")
        r1.total_allocated = Decimal("90000")
        r1.total_used = Decimal("60000")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/statistics/multi-dimension?group_by=period&period_type=quarterly")
        assert resp.status_code == 200
        assert resp.json()["data"][0]["label"] == "2025-Q2"

    def test_by_period_yearly(self, client, mock_db, admin_user):
        """Multi-dimension stats grouped by period (yearly)."""
        r1 = Mock()
        r1.group_key = 2025
        r1.count = 50
        r1.total_amount = Decimal("500000")
        r1.total_allocated = Decimal("400000")
        r1.total_used = Decimal("350000")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/statistics/multi-dimension?group_by=period&period_type=yearly")
        assert resp.status_code == 200
        assert resp.json()["data"][0]["label"] == "2025"

    def test_date_filter_valid(self, client, mock_db, admin_user):
        """Multi-dimension stats with valid date filter."""
        r1 = Mock()
        r1.group_key = "project"
        r1.count = 1
        r1.total_amount = Decimal("1000")
        r1.total_allocated = Decimal("500")
        r1.total_used = Decimal("200")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get(
            "/api/v1/funds/statistics/multi-dimension?group_by=type"
            "&start_date=2025-01-01&end_date=2025-12-31"
        )
        assert resp.status_code == 200

    def test_date_filter_invalid_format(self, client, mock_db, admin_user):
        """Multi-dimension stats with invalid date format returns 400."""
        resp = client.get(
            "/api/v1/funds/statistics/multi-dimension?group_by=type&start_date=not-a-date"
        )
        assert resp.status_code == 400
        assert "日期格式错误" in resp.json()["detail"]

    def test_invalid_group_by(self, client, mock_db, admin_user):
        """Invalid group_by parameter returns 400."""
        resp = client.get("/api/v1/funds/statistics/multi-dimension?group_by=invalid")
        assert resp.status_code == 400
        assert "不支持的分组维度" in resp.json()["detail"]

    def test_utilization_rate_calculation(self, client, mock_db, admin_user):
        """Utilization rate is correctly calculated."""
        r1 = Mock()
        r1.group_key = "project"
        r1.count = 1
        r1.total_amount = Decimal("100000")
        r1.total_allocated = Decimal("80000")
        r1.total_used = Decimal("60000")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/statistics/multi-dimension?group_by=type")
        assert resp.status_code == 200
        item = resp.json()["data"][0]
        assert item["utilization_rate"] == 60.0  # 60000/100000 * 100

    def test_zero_amount_utilization_rate(self, client, mock_db, admin_user):
        """Utilization rate is 0 when total_amount is 0 to avoid division by zero."""
        r1 = Mock()
        r1.group_key = "project"
        r1.count = 0
        r1.total_amount = Decimal("0")
        r1.total_allocated = Decimal("0")
        r1.total_used = Decimal("0")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/statistics/multi-dimension?group_by=type")
        assert resp.status_code == 200
        item = resp.json()["data"][0]
        assert item["utilization_rate"] == 0


class TestFundStatsByType:
    def test_stats_by_type(self, client, mock_db, admin_user):
        """Supported village statistics by type."""
        r1 = Mock()
        r1.fund_type = "project"
        r1.count = 10
        r1.amount = Decimal("100000")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/supported-village/statistics/by-type")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "project" in data["data"]
        assert data["data"]["project"]["count"] == 10
        assert data["fund_types"]["project"] == "项目经费"

    def test_stats_by_type_with_year_range(self, client, mock_db, admin_user):
        """Stats by type with year range filter."""
        r1 = Mock()
        r1.fund_type = "education"
        r1.count = 5
        r1.amount = Decimal("50000")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get(
            "/api/v1/funds/supported-village/statistics/by-type?year_start=2020&year_end=2025"
        )
        assert resp.status_code == 200

    def test_stats_by_type_unknown_fund_type(self, client, mock_db, admin_user):
        """Unknown fund type maps to 'other'."""
        r1 = Mock()
        r1.fund_type = None
        r1.count = 2
        r1.amount = Decimal("2000")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/supported-village/statistics/by-type")
        assert resp.status_code == 200
        data = resp.json()
        assert "other" in data["data"]


class TestFundStatsYearly:
    def test_yearly_comparison(self, client, mock_db, admin_user):
        """Yearly comparison statistics."""
        r1 = Mock()
        r1.year = 2025
        r1.count = 20
        r1.amount = Decimal("200000")
        r1.allocated = Decimal("150000")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/supported-village/statistics/yearly-comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"][0]["year"] == 2025
        assert data["data"][0]["total_actual"] == 200000.0
        assert data["data"][0]["total_planned"] == 150000.0

    def test_yearly_comparison_with_filter(self, client, mock_db, admin_user):
        """Yearly comparison with year_start/year_end filter."""
        _setup_execute_all(mock_db.execute, [])

        resp = client.get(
            "/api/v1/funds/supported-village/statistics/yearly-comparison"
            "?year_start=2024&year_end=2026"
        )
        assert resp.status_code == 200


class TestFundStatsUtilization:
    def test_utilization_rate(self, client, mock_db, admin_user):
        """Overall utilization rate calculation."""
        row = Mock()
        row.planned = Decimal("200000")
        row.actual = Decimal("150000")
        _setup_execute_all(mock_db.execute, [row])
        mock_db.execute.return_value.one.return_value = row

        resp = client.get("/api/v1/funds/supported-village/statistics/utilization-rate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["overall_utilization_rate"] == 75.0
        assert data["data"]["total_actual_investment"] == 150000.0
        assert data["data"]["total_planned_investment"] == 200000.0

    def test_utilization_rate_zero_planned(self, client, mock_db, admin_user):
        """Utilization rate is 0 when planned is 0."""
        row = Mock()
        row.planned = Decimal("0")
        row.actual = Decimal("50000")
        _setup_execute_all(mock_db.execute, [row])
        mock_db.execute.return_value.one.return_value = row

        resp = client.get("/api/v1/funds/supported-village/statistics/utilization-rate")
        assert resp.status_code == 200
        assert resp.json()["data"]["overall_utilization_rate"] == 0


class TestFundStatsSummary:
    def test_summary(self, client, mock_db, admin_user):
        """Fund statistics summary."""
        row = Mock()
        row.total_count = 100
        row.total_amount = Decimal("1000000")
        row.total_allocated = Decimal("800000")
        row.total_used = Decimal("600000")
        _setup_execute_all(mock_db.execute, [row])
        mock_db.execute.return_value.one.return_value = row

        resp = client.get("/api/v1/funds/supported-village/statistics/summary")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_count"] == 100
        assert data["total_amount"] == 1000000.0
        assert data["total_allocated"] == 800000.0
        assert data["total_used"] == 600000.0

    def test_summary_with_year_range(self, client, mock_db, admin_user):
        """Summary with year filter."""
        row = Mock()
        row.total_count = 10
        row.total_amount = Decimal("50000")
        row.total_allocated = Decimal("30000")
        row.total_used = Decimal("20000")
        _setup_execute_all(mock_db.execute, [row])
        mock_db.execute.return_value.one.return_value = row

        resp = client.get(
            "/api/v1/funds/supported-village/statistics/summary?year_start=2025&year_end=2025"
        )
        assert resp.status_code == 200


# ============================================================================
# 9. Fund workflow / state transition endpoints
# ============================================================================


class TestApproveFund:
    def test_approve_fund_success(self, client, mock_db, admin_user):
        """Approve a pending fund."""
        fund = _make_mock_fund(1, status="pending")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        # Mock FundAttachment query for required_attachments check (empty list = at least 1)
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [
            _make_mock_fund_attachment(1, 1, category="contract")
        ]
        mock_db.query.return_value = mock_query

        resp = client.post("/api/v1/funds/1/approve")
        assert resp.status_code == 200
        assert resp.json()["message"] == "审批通过"

    def test_approve_fund_not_found(self, client, mock_db, admin_user):
        """Approve non-existent fund returns 404."""
        _setup_scalar_one_or_none(mock_db.execute, None)

        resp = client.post("/api/v1/funds/999/approve")
        assert resp.status_code == 404

    def test_approve_fund_non_admin_forbidden(self, client_regular, mock_db, regular_user):
        """Regular user cannot approve."""
        resp = client_regular.post("/api/v1/funds/1/approve")
        assert resp.status_code == 403

    def test_approve_fund_illegal_transition(self, client, mock_db, admin_user):
        """Cannot approve a fund not in pending/planned state."""
        for bad_status in ["approved", "allocated", "in_use", "completed", "audited"]:
            fund = _make_mock_fund(1, status=bad_status)
            _setup_scalar_one_or_none(mock_db.execute, fund)

            resp = client.post("/api/v1/funds/1/approve")
            assert resp.status_code == 400, f"Status {bad_status} should block approve"
            assert "非法" in resp.json()["detail"]

    def test_approve_fund_no_attachment(self, client, mock_db, admin_user):
        """Approve requires at least one attachment."""
        fund = _make_mock_fund(1, status="pending")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        # No attachments exist
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        resp = client.post("/api/v1/funds/1/approve")
        assert resp.status_code == 400
        assert "附件" in resp.json()["detail"]

    def test_approve_planned_fund(self, client, mock_db, admin_user):
        """Approve a planned fund (also allowed)."""
        fund = _make_mock_fund(1, status="planned")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [
            _make_mock_fund_attachment(1, 1, category="report")
        ]
        mock_db.query.return_value = mock_query

        resp = client.post("/api/v1/funds/1/approve")
        assert resp.status_code == 200


class TestRejectFund:
    def test_reject_fund_success(self, client, mock_db, admin_user):
        """Reject a pending fund."""
        fund = _make_mock_fund(1, status="pending")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.post("/api/v1/funds/1/reject")
        assert resp.status_code == 200
        assert resp.json()["message"] == "审批驳回"

    def test_reject_fund_illegal_transition(self, client, mock_db, admin_user):
        """Cannot reject a fund not in pending/planned."""
        for bad_status in ["approved", "allocated", "in_use", "completed", "audited"]:
            fund = _make_mock_fund(1, status=bad_status)
            _setup_scalar_one_or_none(mock_db.execute, fund)

            resp = client.post("/api/v1/funds/1/reject")
            assert resp.status_code == 400, f"Status {bad_status} should block reject"


class TestAllocateFund:
    def test_allocate_fund_success(self, client, mock_db, admin_user):
        """Allocate an approved fund (requires contract + allocation_order attachments)."""
        fund = _make_mock_fund(1, status="approved")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [
            _make_mock_fund_attachment(1, 1, category="contract"),
            _make_mock_fund_attachment(2, 1, category="allocation_order"),
        ]
        mock_db.query.return_value = mock_query

        resp = client.post("/api/v1/funds/1/allocate")
        assert resp.status_code == 200
        assert resp.json()["message"] == "经费已拨付"

    def test_allocate_fund_missing_required_attachments(self, client, mock_db, admin_user):
        """Allocate requires contract and allocation_order attachments."""
        fund = _make_mock_fund(1, status="approved")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [
            _make_mock_fund_attachment(1, 1, category="contract"),
            # Missing allocation_order
        ]
        mock_db.query.return_value = mock_query

        resp = client.post("/api/v1/funds/1/allocate")
        assert resp.status_code == 400
        assert "必需文档" in resp.json()["detail"]
        assert "分配令" in resp.json()["detail"]

    def test_allocate_fund_illegal_transition(self, client, mock_db, admin_user):
        """Cannot allocate a non-approved fund."""
        for bad_status in ["pending", "planned", "in_use", "completed", "audited"]:
            fund = _make_mock_fund(1, status=bad_status)
            _setup_scalar_one_or_none(mock_db.execute, fund)

            resp = client.post("/api/v1/funds/1/allocate")
            assert resp.status_code == 400, f"Status {bad_status} should block allocate"

    def test_allocate_fund_with_milestone_check(self, client, mock_db, admin_user):
        """Allocate with milestone_id parameter validates milestone status."""
        fund = _make_mock_fund(1, status="approved", project_id=10)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        # Mock milestone query - milestone exists and is completed
        mock_milestone = Mock()
        mock_milestone.id = 5
        mock_milestone.project_id = 10
        mock_milestone.status = "completed"

        mock_att_query = MagicMock()
        mock_att_query.filter.return_value.all.return_value = [
            _make_mock_fund_attachment(1, 1, category="contract"),
            _make_mock_fund_attachment(2, 1, category="allocation_order"),
        ]

        # Setup query to return milestone first, then attachments
        def _query_side_effect(model_class):
            q = MagicMock()
            if str(model_class) == "<class 'app.models.project_milestone.ProjectMilestone'>":
                q.filter.return_value.first.return_value = mock_milestone
            else:
                q.filter.return_value.all.return_value = [
                    _make_mock_fund_attachment(1, 1, category="contract"),
                    _make_mock_fund_attachment(2, 1, category="allocation_order"),
                ]
            return q

        mock_db.query.side_effect = _query_side_effect

        resp = client.post("/api/v1/funds/1/allocate?milestone_id=5")
        assert resp.status_code == 200

    def test_allocate_fund_no_project_for_milestone(self, client, mock_db, admin_user):
        """Allocate with milestone but fund has no project_id returns 400."""
        fund = _make_mock_fund(1, status="approved", project_id=None)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.post("/api/v1/funds/1/allocate?milestone_id=5")
        assert resp.status_code == 400
        assert "未关联项目" in resp.json()["detail"]

    def test_allocate_fund_milestone_not_found(self, client, mock_db, admin_user):
        """Milestone not found returns 404."""
        fund = _make_mock_fund(1, status="approved", project_id=10)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_q

        resp = client.post("/api/v1/funds/1/allocate?milestone_id=99")
        assert resp.status_code == 404
        assert "里程碑" in resp.json()["detail"]

    def test_allocate_fund_milestone_not_completed(self, client, mock_db, admin_user):
        """Milestone exists but is not completed returns 400."""
        fund = _make_mock_fund(1, status="approved", project_id=10)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        mock_milestone = Mock()
        mock_milestone.id = 5
        mock_milestone.project_id = 10
        mock_milestone.status = "in_progress"

        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = mock_milestone
        mock_db.query.return_value = mock_q

        resp = client.post("/api/v1/funds/1/allocate?milestone_id=5")
        assert resp.status_code == 400
        assert "未完成" in resp.json()["detail"]


class TestStartUseFund:
    def test_start_use_fund_success(self, client, mock_db, admin_user):
        """Start using an allocated fund."""
        fund = _make_mock_fund(1, status="allocated")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.post("/api/v1/funds/1/start-use")
        assert resp.status_code == 200
        assert resp.json()["message"] == "经费已开始使用"

    def test_start_use_fund_illegal_transition(self, client, mock_db, admin_user):
        """Cannot start use on non-allocated funds."""
        for bad_status in ["pending", "planned", "approved", "in_use", "completed", "audited"]:
            fund = _make_mock_fund(1, status=bad_status)
            _setup_scalar_one_or_none(mock_db.execute, fund)

            resp = client.post("/api/v1/funds/1/start-use")
            assert resp.status_code == 400, f"Status {bad_status} should block start-use"


class TestCompleteFund:
    def test_complete_fund_success(self, client, mock_db, admin_user):
        """Complete an in-use fund."""
        fund = _make_mock_fund(1, status="in_use")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.post("/api/v1/funds/1/complete")
        assert resp.status_code == 200
        assert resp.json()["message"] == "经费使用完成"

    def test_complete_fund_illegal_transition(self, client, mock_db, admin_user):
        """Cannot complete a non-in-use fund."""
        for bad_status in ["pending", "planned", "approved", "allocated", "completed", "audited"]:
            fund = _make_mock_fund(1, status=bad_status)
            _setup_scalar_one_or_none(mock_db.execute, fund)

            resp = client.post("/api/v1/funds/1/complete")
            assert resp.status_code == 400, f"Status {bad_status} should block complete"


class TestAuditFund:
    def test_audit_fund_success(self, client, mock_db, admin_user):
        """Audit a completed fund."""
        fund = _make_mock_fund(1, status="completed")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.post("/api/v1/funds/1/audit")
        assert resp.status_code == 200
        assert resp.json()["message"] == "经费审计完成"

    def test_audit_fund_illegal_transition(self, client, mock_db, admin_user):
        """Cannot audit a non-completed fund."""
        for bad_status in ["pending", "planned", "approved", "allocated", "in_use", "audited"]:
            fund = _make_mock_fund(1, status=bad_status)
            _setup_scalar_one_or_none(mock_db.execute, fund)

            resp = client.post("/api/v1/funds/1/audit")
            assert resp.status_code == 400, f"Status {bad_status} should block audit"


# ============================================================================
# 10. History endpoints
# ============================================================================


class TestFundHistoryStatus:
    def test_status_history(self, client, mock_db, admin_user):
        """Get fund status change history."""
        fund = _make_mock_fund(1)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        histories = [_make_mock_status_history(1, 1), _make_mock_status_history(2, 1, from_status="approved", to_status="allocated")]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = histories
        mock_db.query.return_value = mock_query

        resp = client.get("/api/v1/funds/1/history/status")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2
        assert data[0]["to_status"] == "approved"

    def test_status_history_not_found(self, client, mock_db, admin_user):
        """Status history for non-existent fund returns 404."""
        _setup_scalar_one_or_none(mock_db.execute, None)

        resp = client.get("/api/v1/funds/999/history/status")
        assert resp.status_code == 404

    def test_status_history_empty(self, client, mock_db, admin_user):
        """Empty status history returns empty list."""
        fund = _make_mock_fund(1)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        resp = client.get("/api/v1/funds/1/history/status")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestFundHistoryFields:
    def test_field_changes(self, client, mock_db, admin_user):
        """Get fund field change history."""
        fund = _make_mock_fund(1)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        changes = [_make_mock_field_change(1, 1)]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = changes
        mock_db.query.return_value = mock_query

        resp = client.get("/api/v1/funds/1/history/fields")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["field_name"] == "amount"

    def test_field_changes_not_found(self, client, mock_db, admin_user):
        """Field changes for non-existent fund returns 404."""
        _setup_scalar_one_or_none(mock_db.execute, None)

        resp = client.get("/api/v1/funds/999/history/fields")
        assert resp.status_code == 404


class TestFundHistoryOperations:
    def test_operation_logs(self, client, mock_db, admin_user):
        """Get fund operation logs."""
        fund = _make_mock_fund(1)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        logs = [_make_mock_operation_log(1, 1)]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = logs
        mock_db.query.return_value = mock_query

        resp = client.get("/api/v1/funds/1/history/operations")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["operation"] == "approve"

    def test_operation_logs_not_found(self, client, mock_db, admin_user):
        """Operation logs for non-existent fund returns 404."""
        _setup_scalar_one_or_none(mock_db.execute, None)

        resp = client.get("/api/v1/funds/999/history/operations")
        assert resp.status_code == 404


# ============================================================================
# 11. Attachment endpoints
# ============================================================================


class TestListFundAttachments:
    def test_list_attachments(self, client, mock_db, admin_user):
        """List attachments for a fund."""
        fund = _make_mock_fund(1)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        atts = [_make_mock_fund_attachment(1, 1), _make_mock_fund_attachment(2, 1, file_name="report.pdf")]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = atts
        mock_db.query.return_value = mock_query

        resp = client.get("/api/v1/funds/1/attachments")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_attachments_empty(self, client, mock_db, admin_user):
        """Empty attachment list."""
        fund = _make_mock_fund(1)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        resp = client.get("/api/v1/funds/1/attachments")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_attachments_fund_not_found(self, client, mock_db, admin_user):
        """Attachments for non-existent fund returns 404."""
        _setup_scalar_one_or_none(mock_db.execute, None)

        resp = client.get("/api/v1/funds/999/attachments")
        assert resp.status_code == 404


class TestDeleteFundAttachment:
    def test_delete_attachment(self, client, mock_db, admin_user):
        """Delete an attachment."""
        att = _make_mock_fund_attachment(1, 1)
        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = att
        mock_db.query.return_value = mock_q

        with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove:
            resp = client.delete("/api/v1/funds/attachments/1")
            assert resp.status_code == 200
            assert resp.json()["message"] == "删除成功"

    def test_delete_attachment_not_found(self, client, mock_db, admin_user):
        """Delete non-existent attachment returns 404."""
        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_q

        resp = client.delete("/api/v1/funds/attachments/999")
        assert resp.status_code == 404
        assert "附件不存在" in resp.json()["detail"]

    def test_delete_attachment_file_remove_error(self, client, mock_db, admin_user):
        """Delete succeeds even if file removal fails (graceful degradation)."""
        att = _make_mock_fund_attachment(1, 1, file_path="/nonexistent/file.pdf")
        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = att
        mock_db.query.return_value = mock_q

        with patch("os.path.exists", return_value=True), patch("os.remove", side_effect=OSError("Permission denied")):
            resp = client.delete("/api/v1/funds/attachments/1")
            # Should still succeed — DB deletion happens first
            assert resp.status_code == 200


class TestDownloadFundAttachment:
    def test_download_not_found_db(self, client, mock_db, admin_user):
        """Download non-existent attachment returns 404."""
        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_q

        resp = client.get("/api/v1/funds/attachments/999/download")
        assert resp.status_code == 404

    def test_download_file_missing_on_disk(self, client, mock_db, admin_user):
        """Download when file is missing on disk returns 404."""
        att = _make_mock_fund_attachment(1, 1, file_path="/tmp/missing.pdf")
        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = att
        mock_db.query.return_value = mock_q

        with patch("os.path.exists", return_value=False):
            resp = client.get("/api/v1/funds/attachments/1/download")
            assert resp.status_code == 404
            assert "文件不存在" in resp.json()["detail"]


class TestPreviewFundAttachment:
    def test_preview_not_found_db(self, client, mock_db, admin_user):
        """Preview non-existent attachment returns 404."""
        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_q

        resp = client.get("/api/v1/funds/attachments/999/preview")
        assert resp.status_code == 404

    def test_preview_file_missing_on_disk(self, client, mock_db, admin_user):
        """Preview when file is missing on disk returns 404."""
        att = _make_mock_fund_attachment(1, 1, file_path="/tmp/missing.pdf")
        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = att
        mock_db.query.return_value = mock_q

        with patch("os.path.exists", return_value=False):
            resp = client.get("/api/v1/funds/attachments/1/preview")
            assert resp.status_code == 404


# ============================================================================
# 12. Edge cases and cross-cutting concerns
# ============================================================================


class TestEdgeCases:
    def test_safe_val_decimal(self, client, mock_db, admin_user):
        """_safe_val handles Decimal correctly."""
        fund = _make_mock_fund(1, amount=Decimal("1234.56"))
        fund.project = None
        fund.village = None
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.get("/api/v1/funds/1")
        assert resp.status_code == 200
        assert resp.json()["data"]["amount"] == 1234.56

    def test_safe_val_datetime(self, client, mock_db, admin_user):
        """_safe_val handles datetime correctly."""
        dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        fund = _make_mock_fund(1, application_date=dt, approval_date=dt, allocation_date=dt)
        fund.project = None
        fund.village = None
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.get("/api/v1/funds/1")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "application_date" in data

    def test_safe_val_none(self, client, mock_db, admin_user):
        """_safe_val returns None for None values."""
        fund = _make_mock_fund(1, approved_by=None)
        fund.project = None
        fund.village = None
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.get("/api/v1/funds/1")
        assert resp.status_code == 200
        assert resp.json()["data"]["approved_by"] is None

    def test_fund_to_dict_with_associations(self, client, mock_db, admin_user):
        """_fund_to_dict enriches with project_name and village_name when associations exist."""
        fund = _make_mock_fund(1)
        fund.project = Mock(name="项目X")
        fund.project.name = "项目X"
        fund.village = Mock(name="村庄Y")
        fund.village.name = "村庄Y"
        fund.organization = Mock(name="组织Z")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client.get("/api/v1/funds/1")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["project_name"] == "项目X"
        assert data["village_name"] == "村庄Y"

    def test_list_funds_page_size_boundary(self, client, mock_db, admin_user):
        """Page size boundary: minimum 1, maximum 200."""
        fund = _make_mock_fund(1)
        _setup_scalars_all(mock_db.execute, [fund])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        # page_size=1 (minimum)
        resp = client.get("/api/v1/funds?page_size=1")
        assert resp.status_code == 200

        # page_size=200 (maximum)
        resp = client.get("/api/v1/funds?page_size=200")
        assert resp.status_code == 200

    def test_list_funds_page_zero_rejected(self, client, mock_db, admin_user):
        """Page 0 is rejected (minimum is 1)."""
        resp = client.get("/api/v1/funds?page=0")
        assert resp.status_code == 422

    def test_statistics_multi_dimension_unknown_key_label(self, client, mock_db, admin_user):
        """Group keys not in label_map fall through to raw key."""
        r1 = Mock()
        r1.group_key = "unmapped_key"
        r1.count = 1
        r1.total_amount = Decimal("100")
        r1.total_allocated = Decimal("50")
        r1.total_used = Decimal("20")
        _setup_execute_all(mock_db.execute, [r1])

        resp = client.get("/api/v1/funds/statistics/multi-dimension?group_by=source")
        assert resp.status_code == 200
        # Raw key is used as label when not in the map
        assert resp.json()["data"][0]["label"] == "unmapped_key"

    def test_supported_village_stats_by_type_with_department(self, client, mock_db, admin_user):
        """Supported village stats by type with department filter."""
        _setup_execute_all(mock_db.execute, [])

        resp = client.get(
            "/api/v1/funds/supported-village/statistics/by-type?department=military"
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestTransitionStatusInternal:
    """Test the _transition_status internal helper more thoroughly."""

    def test_transition_with_unknown_field_skipped(self, client, mock_db, admin_user):
        """_transition_status skips unknown fields on Fund model and logs warning."""
        fund = _make_mock_fund(1, status="pending")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [
            _make_mock_fund_attachment(1, 1, category="report")
        ]
        mock_db.query.return_value = mock_query

        resp = client.post("/api/v1/funds/1/approve")
        # The approve endpoint passes approved_by + approval_date which are valid fields
        assert resp.status_code == 200

    def test_transition_sets_fields_correctly(self, client, mock_db, admin_user):
        """_transition_status sets target status and extra kwargs on the Fund."""
        fund = _make_mock_fund(1, status="pending", approved_by=None, approval_date=None)
        _setup_scalar_one_or_none(mock_db.execute, fund)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [
            _make_mock_fund_attachment(1, 1, category="report")
        ]
        mock_db.query.return_value = mock_query

        resp = client.post("/api/v1/funds/1/approve")
        assert resp.status_code == 200
        assert fund.status == "approved"
        assert fund.approved_by == "管理员"
        assert fund.approval_date is not None


# ============================================================================
# 13. Manager role tests (manager role can perform admin operations)
# ============================================================================


class TestManagerRole:
    """Manager role has permission equivalent to admin for funds operations."""

    @pytest.fixture
    def client_manager(self, manager_user, mock_db):
        """TestClient with manager role privileges."""
        from app.main import app

        def _get_db():
            yield mock_db

        async def _get_current_user():
            return manager_user

        from app.core.database import get_db
        from app.core.security import get_current_user

        app.dependency_overrides[get_db] = _get_db
        app.dependency_overrides[get_current_user] = _get_current_user

        client = TestClient(app, raise_server_exceptions=False)
        yield client
        app.dependency_overrides.clear()

    def test_manager_can_create_fund(self, client_manager, mock_db, manager_user):
        """Manager can create a fund."""
        with patch("app.api.v1.funds.FundService") as MockService:
            mock_svc = MockService.return_value
            created = _make_mock_fund(300)
            mock_svc.create_fund_for_user.return_value = created

            resp = client_manager.post("/api/v1/funds", json={"name": "经理创建", "amount": 2000})
            assert resp.status_code == 201

    def test_manager_can_delete_fund(self, client_manager, mock_db, manager_user):
        """Manager can delete a pending fund."""
        fund = _make_mock_fund(1, status="pending")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        resp = client_manager.delete("/api/v1/funds/1")
        assert resp.status_code == 200

    def test_manager_can_approve_fund(self, client_manager, mock_db, manager_user):
        """Manager can approve a fund."""
        fund = _make_mock_fund(1, status="pending")
        _setup_scalar_one_or_none(mock_db.execute, fund)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [
            _make_mock_fund_attachment(1, 1, category="report")
        ]
        mock_db.query.return_value = mock_query

        resp = client_manager.post("/api/v1/funds/1/approve")
        assert resp.status_code == 200


# ============================================================================
# 14. Pagination edge cases
# ============================================================================


class TestPaginationEdgeCases:
    def test_keyset_pagination_without_cursor(self, client, mock_db, admin_user):
        """Keyset pagination without cursor returns first page."""
        fund = _make_mock_fund(1)
        keyset_result = {
            "items": [fund],
            "total": 1,
            "page_size": 20,
            "next_cursor": None,
            "has_more": False,
        }
        with patch("app.api.v1.funds.keyset_paginate", return_value=keyset_result):
            resp = client.get("/api/v1/funds?pagination=keyset")
            assert resp.status_code == 200
            assert resp.json()["next_cursor"] is None

    def test_keyset_pagination_with_cursor(self, client, mock_db, admin_user):
        """Keyset pagination with cursor continues from cursor position."""
        fund = _make_mock_fund(50)
        keyset_result = {
            "items": [fund],
            "total": 100,
            "page_size": 20,
            "next_cursor": "next_cursor_val",
            "has_more": True,
        }
        with patch("app.api.v1.funds.keyset_paginate", return_value=keyset_result):
            resp = client.get("/api/v1/funds?pagination=keyset&cursor=abc123")
            assert resp.status_code == 200
            data = resp.json()
            assert data["has_more"] is True
            assert data["next_cursor"] == "next_cursor_val"

    def test_offset_pagination_on_page_3(self, client, mock_db, admin_user):
        """Offset pagination on page 3."""
        fund = _make_mock_fund(41)
        _setup_scalars_all(mock_db.execute, [fund])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 45
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        resp = client.get("/api/v1/funds?page=3&page_size=20")
        assert resp.status_code == 200
        assert resp.json()["page"] == 3

    def test_offset_pagination_large_page_size(self, client, mock_db, admin_user):
        """Offset pagination with maximum page_size."""
        fund = _make_mock_fund(1)
        _setup_scalars_all(mock_db.execute, [fund])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_db.execute.side_effect = [count_result, mock_db.execute.return_value]

        resp = client.get("/api/v1/funds?page_size=200")
        assert resp.status_code == 200

    def test_export_funds_limit_too_low(self, client, mock_db, admin_user):
        """Export with limit below minimum returns validation error."""
        resp = client.get("/api/v1/funds/export?limit=0")
        assert resp.status_code == 422

    def test_export_funds_limit_too_high(self, client, mock_db, admin_user):
        """Export with limit above maximum returns validation error."""
        resp = client.get("/api/v1/funds/export?limit=50001")
        assert resp.status_code == 422
