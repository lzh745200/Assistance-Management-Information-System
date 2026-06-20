"""Service contract smoke test — verifies the production crash fix.

Regression verification for the 5 engineer fixes:
1. RuralWorkService.create_rural_work + missing methods (production AttributeError root cause)
2. rural_works route return-value contract (dict, not .model_dump())
3. AuditLogService.log now persists (db= + details=)
4. UserCascadeDeleteService.delete_user_cascade
5. ExcelExportService.export_organization_pass_codes

Uses TestClient + in-memory SQLite (same fixture pattern as test_data_reports_api_2.py).
This file is TEMPORARY — deleted after verification, never committed.
"""

import os
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_settings():
    os.environ["SECRET_KEY"] = "test-secret-key-32-chars-long!!!!!"
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    from app.core.config import settings

    settings.SECRET_KEY = "test-secret-key-32-chars-long!!!!!"
    settings.ENVIRONMENT = "testing"
    settings.DEBUG = True
    settings.DATABASE_URL = "sqlite:///./test.db"
    yield
    for k in ["SECRET_KEY", "ENVIRONMENT", "DEBUG", "DATABASE_URL"]:
        os.environ.pop(k, None)


@pytest.fixture
def client():
    from app.main import app
    from app.core.database import get_db
    from app.core.security import get_current_user
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.models import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    app.dependency_overrides[get_db] = lambda: db

    _mock_user = Mock(
        id=1,
        username="admin",
        role="admin",
        is_superuser=True,
        is_active=True,
        permissions_list=["*"],
        organization_id=1,
        email="admin@test.com",
    )
    app.dependency_overrides[get_current_user] = lambda: _mock_user

    yield TestClient(app, raise_server_exceptions=False), db

    app.dependency_overrides.clear()
    db.close()
    engine.dispose()


# ──────────────────────────────────────────────────────────────
# Fix 1 + Fix 2: RuralWorkService contract + route return values
# ──────────────────────────────────────────────────────────────


class TestRuralWorkServiceContract:
    """Verify the production AttributeError crash is fixed end-to-end."""

    def test_create_rural_work_no_attribute_error(self, client):
        """POST /api/v1/rural-works — original crash point."""
        test_client, db = client
        resp = test_client.post(
            "/api/v1/rural-works",
            json={
                "name": "测试乡村工作",
                "type": "infrastructure",
                "status": "planned",
                "responsible_person": "张三",
                "progress": 0,
            },
        )
        assert resp.status_code == 200, f"创建失败: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["name"] == "测试乡村工作"
        assert data["data"]["id"] is not None
        assert data["data"]["code"] is not None  # auto-generated code
        assert data["data"]["created_by"] == 1  # audit field populated

    def test_list_rural_works(self, client):
        """GET /api/v1/rural-works — list."""
        test_client, db = client
        # seed one record directly via service (already verified create works)
        from app.services.rural_work_service import RuralWorkService

        svc = RuralWorkService(db)
        svc.create_rural_work(
            {"name": "种子工作", "type": "education", "status": "planned"},
            user_id=1,
        )

        resp = test_client.get("/api/v1/rural-works?skip=0&limit=10")
        assert resp.status_code == 200, f"列表失败: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        # items should be dicts (route returns service dict directly, not .model_dump())
        assert isinstance(data["items"][0], dict)
        assert "name" in data["items"][0]

    def test_list_rural_works_includes_village_name(self, client):
        """Fix 7: _to_dict must include village_name (was missing → list didn't display)."""
        test_client, db = client
        from app.services.rural_work_service import RuralWorkService
        from app.models.village import Village

        # Create a village to link
        village = Village(name="幸福村", code="VL-001")
        db.add(village)
        db.commit()
        db.refresh(village)

        svc = RuralWorkService(db)
        svc.create_rural_work(
            {"name": "带村庄工作", "type": "infrastructure", "status": "planned",
             "village_id": village.id},
            user_id=1,
        )

        resp = test_client.get("/api/v1/rural-works?skip=0&limit=10")
        assert resp.status_code == 200, f"列表失败: {resp.status_code} {resp.text}"
        items = resp.json()["items"]
        target = [it for it in items if it["name"] == "带村庄工作"]
        assert len(target) == 1, "应能查到刚创建的工作"
        # Fix 7: village_name field must be present and populated
        assert "village_name" in target[0], "_to_dict 应包含 village_name 字段"
        assert target[0]["village_name"] == "幸福村", (
            f"village_name 应为 '幸福村'，实际: {target[0].get('village_name')!r}"
        )

    def test_list_rural_works_village_name_null_when_no_village(self, client):
        """village_name should be null when village_id is None (no crash)."""
        test_client, db = client
        from app.services.rural_work_service import RuralWorkService

        svc = RuralWorkService(db)
        svc.create_rural_work(
            {"name": "无村庄工作", "type": "education", "status": "planned"},
            user_id=1,
        )

        resp = test_client.get("/api/v1/rural-works?skip=0&limit=10")
        assert resp.status_code == 200
        items = resp.json()["items"]
        target = [it for it in items if it["name"] == "无村庄工作"]
        assert len(target) == 1
        assert "village_name" in target[0]
        assert target[0]["village_name"] is None

    def test_update_rural_work(self, client):
        """PUT /api/v1/rural-works/{id} — update via three-param route call."""
        test_client, db = client
        from app.services.rural_work_service import RuralWorkService

        svc = RuralWorkService(db)
        created = svc.create_rural_work(
            {"name": "待更新工作", "type": "infrastructure", "status": "planned"},
            user_id=1,
        )
        work_id = created["id"]

        resp = test_client.put(
            f"/api/v1/rural-works/{work_id}",
            json={"name": "已更新工作", "status": "in_progress", "progress": 50},
        )
        assert resp.status_code == 200, f"更新失败: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data["data"]["name"] == "已更新工作"
        assert data["data"]["status"] == "in_progress"
        assert data["data"]["progress"] == 50
        assert data["data"]["updated_by"] == 1

    def test_get_rural_work_by_id(self, client):
        """GET /api/v1/rural-works/{id} — get detail (returns dict, not .model_dump())."""
        test_client, db = client
        from app.services.rural_work_service import RuralWorkService

        svc = RuralWorkService(db)
        created = svc.create_rural_work(
            {"name": "详情工作", "type": "healthcare", "status": "planned"},
            user_id=1,
        )
        work_id = created["id"]

        resp = test_client.get(f"/api/v1/rural-works/{work_id}")
        assert resp.status_code == 200, f"详情失败: {resp.status_code} {resp.text}"
        assert resp.json()["data"]["name"] == "详情工作"

    def test_get_statistics(self, client):
        """GET /api/v1/rural-works/statistics/summary — get_statistics method exists."""
        test_client, db = client
        resp = test_client.get("/api/v1/rural-works/statistics/summary")
        assert resp.status_code == 200, f"统计失败: {resp.status_code} {resp.text}"
        data = resp.json()["data"]
        assert "total" in data
        assert "planned" in data
        assert "completion_rate" in data

    def test_get_available_years(self, client):
        """GET /api/v1/rural-works/years — get_available_years method exists."""
        test_client, db = client
        resp = test_client.get("/api/v1/rural-works/years")
        assert resp.status_code == 200, f"年份失败: {resp.status_code} {resp.text}"
        assert isinstance(resp.json()["data"], list)

    def test_batch_delete_with_ids_body(self, client):
        """Fix 9: batch-delete accepts {ids: [...]} body (frontend contract)."""
        test_client, db = client
        from app.services.rural_work_service import RuralWorkService

        svc = RuralWorkService(db)
        w1 = svc.create_rural_work({"name": "批删1", "type": "environment"}, user_id=1)
        w2 = svc.create_rural_work({"name": "批删2", "type": "environment"}, user_id=1)

        # Frontend sends {"ids": [1, 2]} — must NOT 422
        resp = test_client.post(
            "/api/v1/rural-works/batch-delete",
            json={"ids": [w1["id"], w2["id"]]},
        )
        assert resp.status_code == 200, f"批删失败: {resp.status_code} {resp.text}"
        assert resp.json()["data"]["deleted"] == 2

    def test_batch_delete_empty_ids(self, client):
        """Fix 9: empty ids list returns deleted=0 gracefully."""
        test_client, _ = client
        resp = test_client.post(
            "/api/v1/rural-works/batch-delete",
            json={"ids": []},
        )
        assert resp.status_code == 200, f"空批删失败: {resp.status_code} {resp.text}"
        assert resp.json()["data"]["deleted"] == 0

    def test_delete_single_rural_work_with_audit(self, client):
        """DELETE /api/v1/rural-works/{id} — passes current_user.id for audit log."""
        test_client, db = client
        from app.services.rural_work_service import RuralWorkService

        svc = RuralWorkService(db)
        created = svc.create_rural_work(
            {"name": "单删工作", "type": "industry", "status": "planned"},
            user_id=1,
        )
        work_id = created["id"]

        resp = test_client.delete(f"/api/v1/rural-works/{work_id}")
        assert resp.status_code == 200, f"单删失败: {resp.status_code} {resp.text}"
        # verify it's actually gone
        resp2 = test_client.get(f"/api/v1/rural-works/{work_id}")
        assert resp2.status_code == 404

    def test_get_villages_for_select(self, client):
        """GET /api/v1/rural-works/villages — get_villages_for_select method exists."""
        test_client, _ = client
        resp = test_client.get("/api/v1/rural-works/villages")
        assert resp.status_code == 200, f"村庄列表失败: {resp.status_code} {resp.text}"

    def test_generate_work_report(self, client):
        """GET /api/v1/rural-works/report/generate — generate_work_report method exists."""
        test_client, _ = client
        resp = test_client.get("/api/v1/rural-works/report/generate?year=2024")
        assert resp.status_code == 200, f"报告失败: {resp.status_code} {resp.text}"
        data = resp.json()["data"]
        assert "total" in data
        assert "by_status" in data


# ──────────────────────────────────────────────────────────────
# Fix 1 (direct unit-level): service methods exist & return dict
# ──────────────────────────────────────────────────────────────


class TestRuralWorkServiceMethods:
    """Verify all route-called service methods exist and return the dict contract."""

    def test_all_methods_exist(self, client):
        _, db = client
        from app.services.rural_work_service import RuralWorkService

        svc = RuralWorkService(db)
        # Every method that routes call must exist (original crash was missing create_rural_work)
        for method in (
            "create_rural_work",
            "update_rural_work",
            "get_rural_works",
            "get_rural_work_by_id",
            "delete_rural_work",
            "get_statistics",
            "get_villages_for_select",
            "generate_work_report",
            "get_available_years",
            "batch_delete",
        ):
            assert hasattr(svc, method), f"RuralWorkService 缺少方法: {method}"

    def test_create_returns_dict_not_model(self, client):
        """Service must return a dict (route passes it directly to ResponseModel)."""
        _, db = client
        from app.services.rural_work_service import RuralWorkService

        svc = RuralWorkService(db)
        result = svc.create_rural_work(
            {"name": "契约验证", "type": "infrastructure", "status": "planned"},
            user_id=1,
        )
        assert isinstance(result, dict), "create_rural_work 必须返回 dict"
        assert "id" in result and "name" in result

    def test_update_returns_dict_not_model(self, client):
        _, db = client
        from app.services.rural_work_service import RuralWorkService

        svc = RuralWorkService(db)
        created = svc.create_rural_work({"name": "更新契约", "type": "education"}, user_id=1)
        result = svc.update_rural_work(created["id"], {"name": "已更新"}, user_id=1)
        assert isinstance(result, dict), "update_rural_work 必须返回 dict"
        assert result["name"] == "已更新"

    def test_update_backward_compat_kwargs(self, client):
        """update_rural_work must accept old-style kwargs (backward compat)."""
        _, db = client
        from app.services.rural_work_service import RuralWorkService

        svc = RuralWorkService(db)
        created = svc.create_rural_work({"name": "kwargs兼容", "type": "education"}, user_id=1)
        # old-style: pass fields as kwargs, no schema data
        result = svc.update_rural_work(created["id"], name="kwargs更新", status="completed")
        assert isinstance(result, dict)
        assert result["name"] == "kwargs更新"
        assert result["status"] == "completed"


# ──────────────────────────────────────────────────────────────
# Fix 8: Schema mutable default values
# ──────────────────────────────────────────────────────────────


class TestSchemaMutableDefaults:
    """Verify schemas use Field(default_factory=...) not mutable literals."""

    def test_list_response_default_factory_list(self):
        """RuralWorkListResponse.items must not share a mutable default list."""
        from app.schemas.rural_work import RuralWorkListResponse

        r1 = RuralWorkListResponse()
        r2 = RuralWorkListResponse()
        # If default_factory is used, the lists are independent objects
        assert r1.items is not r2.items, (
            "items 应使用 Field(default_factory=list)，不应共享可变默认值"
        )
        assert r1.items == []
        assert r2.items == []

    def test_statistics_default_factory_dict(self):
        """RuralWorkStatistics.by_type must not share a mutable default dict."""
        from app.schemas.rural_work import RuralWorkStatistics

        s1 = RuralWorkStatistics()
        s2 = RuralWorkStatistics()
        assert s1.by_type is not s2.by_type, (
            "by_type 应使用 Field(default_factory=dict)，不应共享可变默认值"
        )
        assert s1.by_type == {}
        assert s2.by_type == {}


# ──────────────────────────────────────────────────────────────
# Fix 3: AuditLogService.log persists to DB (db= + details=)
# ──────────────────────────────────────────────────────────────


class TestAuditLogPersistence:
    """Verify audit.log now writes to DB (was silently dropped before fix)."""

    def test_audit_log_persists_with_db_and_details(self, client):
        """AuditLogService.log must actually write to DB after Fix 6.

        Round 1 found: AuditLog(resource=..., details=..., ip_address=...)
        used wrong column names → silent failure.

        Round 2: Fix 6 maps to resource_type / user_ip / metadata_.
        Verify the log persists with correct field values.
        """
        _, db = client
        from app.core.security import AuditLogService
        from app.models.audit import AuditLog
        import asyncio

        svc = AuditLogService(db)
        asyncio.run(
            svc.log(
                db=db,
                user_id=1,
                action="create_project",
                resource="project",
                resource_id="42",
                details="创建项目: 测试项目 (PRJ-001)",
                ip_address="127.0.0.1",
            )
        )
        # The log MUST be persisted after the field-name fix
        logs = db.query(AuditLog).filter(AuditLog.action == "create_project").all()
        assert len(logs) == 1, (
            "审计日志应写入数据库 — AuditLogService.log 字段映射修复后仍写入失败"
        )
        assert logs[0].resource_type == "project", "resource 应映射到 resource_type"
        assert logs[0].resource_id == "42"
        assert logs[0].user_ip == "127.0.0.1", "ip_address 应映射到 user_ip"
        # details stored in metadata_ JSON column
        assert logs[0].metadata_ is not None, "details 应存入 metadata_ JSON 列"
        assert logs[0].metadata_.get("details") == "创建项目: 测试项目 (PRJ-001)"

    def test_audit_log_without_db_returns_silently(self, client):
        """Without db= the log is silently skipped (no crash) — backward-safe."""
        from app.core.security import AuditLogService
        import asyncio

        svc = AuditLogService(None)
        # Should not raise
        asyncio.run(svc.log(action="noop"))


# ──────────────────────────────────────────────────────────────
# Fix 4: UserCascadeDeleteService.delete_user_cascade
# ──────────────────────────────────────────────────────────────


class TestUserCascadeDelete:
    """Verify user cascade delete no longer 500s."""

    def test_delete_user_cascade_not_found(self, client):
        _, db = client
        from app.services.user_cascade_delete_service import UserCascadeDeleteService

        svc = UserCascadeDeleteService(db)
        result = svc.delete_user_cascade(99999)
        assert result["success"] is False
        assert result["message"] == "用户不存在"

    def test_delete_user_cascade_success(self, client):
        _, db = client
        from app.services.user_cascade_delete_service import UserCascadeDeleteService
        from app.models.user import User

        user = User(
            username="cascade_test",
            email="cascade@test.com",
            hashed_password="fake_hashed_pwd",
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        uid = user.id

        svc = UserCascadeDeleteService(db)
        result = svc.delete_user_cascade(uid)
        assert result["success"] is True
        assert result["message"] == "用户删除成功"
        # user must be gone
        assert db.query(User).filter(User.id == uid).first() is None


# ──────────────────────────────────────────────────────────────
# Fix 5: ExcelExportService.export_organization_pass_codes
# ──────────────────────────────────────────────────────────────


class TestExportOrganizationPassCodes:
    """Verify organization pass-code export no longer 500s."""

    def test_export_returns_excel_bytes(self):
        from app.services.export_service import ExcelExportService

        svc = ExcelExportService()
        result = svc.export_organization_pass_codes(
            [
                {
                    "organization_name": "测试组织",
                    "verification_code": "VC-001",
                    "pass_code": "PC-001",
                    "allow_subordinate_generation": True,
                    "status": "active",
                    "created_at": "2024-01-01",
                }
            ]
        )
        assert isinstance(result, bytes)
        assert len(result) > 0
        # xlsx files start with PK zip signature
        assert result[:2] == b"PK"

    def test_export_empty_list(self):
        from app.services.export_service import ExcelExportService

        svc = ExcelExportService()
        result = svc.export_organization_pass_codes([])
        assert isinstance(result, bytes)
        assert result[:2] == b"PK"
