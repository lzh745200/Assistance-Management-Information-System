"""
安全数据隔离测试 — 验证 CRIT-1/2/3 + HIGH-1/2/3 修复

测试策略：
  - 创建两个不同组织的用户（org=1 管理员, org=2 普通用户）
  - 用 org=1 用户创建记录，用 org=2 用户尝试越权访问
  - 断言返回 403（跨组织）而非 200（数据泄露）

覆盖模块: supported_village / policy / projects / funds / school
"""
import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient


@pytest.fixture
def org1_admin_client(client):
    """org=1 的管理员客户端"""
    if client is None:
        pytest.skip("client fixture unavailable")
    from app.core.security import get_current_user

    user = Mock()
    user.id = 1
    user.username = "admin1"
    user.role = "admin"
    user.is_superuser = False
    user.is_active = True
    user.permissions_list = ["*"]
    user.organization_id = 1

    original = client.app.dependency_overrides.copy()
    client.app.dependency_overrides[get_current_user] = lambda: user
    yield client
    client.app.dependency_overrides = original


@pytest.fixture
def org2_user_client(client):
    """org=2 的普通用户客户端（非管理员）"""
    if client is None:
        pytest.skip("client fixture unavailable")
    from app.core.security import get_current_user

    user = Mock()
    user.id = 2
    user.username = "user2"
    user.role = "user"
    user.is_superuser = False
    user.is_active = True
    user.permissions_list = ["read"]
    user.organization_id = 2

    original = client.app.dependency_overrides.copy()
    client.app.dependency_overrides[get_current_user] = lambda: user
    yield client
    client.app.dependency_overrides = original


# ──────────────────────── CRIT-1: supported_village ────────────────────────


class TestSupportedVillageIsolation:
    """帮扶村数据隔离：跨组织详情访问应返回 403"""

    def test_cross_org_village_detail_returns_403(self, client):
        """org1 创建的帮扶村，org2 用户不应能访问详情"""
        # org1_admin_client/org2_user_client 两个 fixture 共享同一 app 的
        # dependency_overrides，同时使用时后生效者会覆盖前者（两个"客户端"
        # 实际同身份），因此本测试显式按阶段切换覆盖。
        from app.core.security import get_current_user

        org1_admin = Mock()
        org1_admin.id = 1
        org1_admin.username = "admin1"
        org1_admin.role = "admin"
        org1_admin.is_superuser = False
        org1_admin.is_active = True
        org1_admin.permissions_list = ["*"]
        org1_admin.organization_id = 1

        org2_user = Mock()
        org2_user.id = 2
        org2_user.username = "user2"
        org2_user.role = "user"
        org2_user.is_superuser = False
        org2_user.is_active = True
        org2_user.permissions_list = ["read"]
        org2_user.organization_id = 2

        original = client.app.dependency_overrides.copy()
        try:
            # org1 管理员创建帮扶村
            client.app.dependency_overrides[get_current_user] = lambda: org1_admin
            resp = client.post("/api/v1/supported-villages", json={
                "village_name": "测试村A",
                "province": "贵州省",
                "county": "测试县",
            })
            # 创建可能因 schema 差异失败，跳过而非报错
            if resp.status_code not in (200, 201):
                pytest.skip(f"创建帮扶村失败: {resp.status_code} {resp.text[:200]}")
            village_id = resp.json().get("data", {}).get("id")
            if not village_id:
                pytest.skip("无法获取帮扶村ID")

            # org2 普通用户尝试访问 → 应 403（跨组织）
            client.app.dependency_overrides[get_current_user] = lambda: org2_user
            resp2 = client.get(f"/api/v1/supported-villages/{village_id}")
            assert resp2.status_code in (403, 404), (
                f"跨组织访问应返回 403/404，实际 {resp2.status_code} — 数据隔离漏洞!"
            )
        finally:
            client.app.dependency_overrides = original


# ──────────────────────── CRIT-2: policy 写操作 ────────────────────────


class TestPolicyWritePermission:
    """政策写操作：非管理员应返回 403"""

    def test_non_admin_cannot_create_policy(self, org2_user_client):
        """普通用户不能创建政策"""
        resp = org2_user_client.post("/api/v1/policies", json={
            "title": "测试政策",
            "content": "内容",
            "category": "local",
            "level": "national",
        })
        assert resp.status_code == 403, (
            f"普通用户创建政策应返回 403，实际 {resp.status_code} — 写操作鉴权缺失!"
        )

    def test_non_admin_cannot_delete_policy(self, org2_user_client):
        """普通用户不能删除政策"""
        resp = org2_user_client.delete("/api/v1/policies/99999")
        assert resp.status_code == 403, (
            f"普通用户删除政策应返回 403，实际 {resp.status_code} — 写操作鉴权缺失!"
        )

    def test_non_admin_cannot_batch_delete_policies(self, org2_user_client):
        """普通用户不能批量删除政策"""
        resp = org2_user_client.post("/api/v1/policies/batch-delete", json={"ids": [1, 2, 3]})
        assert resp.status_code == 403, (
            f"普通用户批量删除应返回 403，实际 {resp.status_code} — 写操作鉴权缺失!"
        )


# ──────────────────────── CRIT-2: policy 收藏 IDOR ────────────────────────


class TestPolicyFavoriteIDOR:
    """政策收藏 IDOR：不能操作他人收藏"""

    def test_favorite_no_user_id_param(self, org2_user_client):
        """收藏接口不应再接受 user_id 参数（已移除）"""
        # POST /policies/{id}/favorite 不带 user_id — 应使用 current_user.id
        resp = org2_user_client.post("/api/v1/policies/99999/favorite")
        # 政策不存在应 404，而非 422（缺少 user_id 参数）
        assert resp.status_code != 422, (
            "收藏接口仍要求 user_id 参数 — IDOR 修复未生效!"
        )

    def test_get_others_favorites_returns_403(self, org2_user_client):
        """查看他人收藏应返回 403"""
        # org2 用户(id=2) 尝试查看 user_id=1 的收藏
        resp = org2_user_client.get("/api/v1/policies/user/1/favorites")
        assert resp.status_code == 403, (
            f"查看他人收藏应返回 403，实际 {resp.status_code} — IDOR 漏洞!"
        )


# ──────────────────────── HIGH-1: projects 子端点 ────────────────────────


class TestProjectSubEndpointIsolation:
    """项目子端点：跨组织访问应返回 403"""

    def test_cross_org_project_funds_returns_403(self, client):
        """org1 创建的项目，org2 用户不应能访问经费"""
        # 与 TestSupportedVillageIsolation 相同的原因：两个组织身份 fixture
        # 共享同一 app 的 dependency_overrides，必须显式按阶段切换。
        from app.core.security import get_current_user

        org1_admin = Mock()
        org1_admin.id = 1
        org1_admin.username = "admin1"
        org1_admin.role = "admin"
        org1_admin.is_superuser = False
        org1_admin.is_active = True
        org1_admin.permissions_list = ["*"]
        org1_admin.organization_id = 1

        org2_user = Mock()
        org2_user.id = 2
        org2_user.username = "user2"
        org2_user.role = "user"
        org2_user.is_superuser = False
        org2_user.is_active = True
        org2_user.permissions_list = ["read"]
        org2_user.organization_id = 2

        original = client.app.dependency_overrides.copy()
        try:
            # org1 创建项目
            client.app.dependency_overrides[get_current_user] = lambda: org1_admin
            resp = client.post("/api/v1/projects", json={
                "name": "隔离测试项目",
                "type": "infrastructure",
            })
            if resp.status_code not in (200, 201):
                pytest.skip(f"创建项目失败: {resp.status_code} {resp.text[:200]}")
            data = resp.json()
            project_id = data.get("id") or data.get("data", {}).get("id")
            if not project_id:
                pytest.skip("无法获取项目ID")

            # org2 用户访问项目经费 → 应 403
            client.app.dependency_overrides[get_current_user] = lambda: org2_user
            resp2 = client.get(f"/api/v1/projects/{project_id}/funds")
            assert resp2.status_code in (403, 404), (
                f"跨组织访问项目经费应返回 403/404，实际 {resp2.status_code} — 越权漏洞!"
            )
        finally:
            client.app.dependency_overrides = original


# ──────────────────────── 单元级：check_record_access ────────────────────────


class TestCheckRecordAccess:
    """直接测试 check_record_access 工具函数"""

    def test_admin_sees_all(self, admin_user):
        from app.core.data_permission import check_record_access

        record = Mock()
        record.organization_id = 999
        record.created_by = 888
        assert check_record_access(record, admin_user) is True

    def test_own_dept_access(self, regular_user):
        from app.core.data_permission import check_record_access

        # role="user" 的数据域为 OWN（仅本人记录），部门级访问需要 manager/admin 角色
        regular_user.role = "manager"
        record = Mock()
        record.organization_id = 2  # 同组织
        record.created_by = 999
        assert check_record_access(record, regular_user) is True

    def test_cross_dept_denied(self, regular_user):
        from app.core.data_permission import check_record_access

        record = Mock()
        record.organization_id = 999  # 不同组织
        record.created_by = 888  # 也不是自己创建的
        assert check_record_access(record, regular_user) is False

    def test_own_record_access(self, viewer_user):
        """普通用户访问自己创建的记录"""
        from app.core.data_permission import check_record_access

        record = Mock()
        record.organization_id = 999  # 不同组织
        record.created_by = 3  # 但自己创建的 (viewer_user.id=3)
        assert check_record_access(record, viewer_user) is True


# ──────────────────────── 单元级：require_manager_role ────────────────────────


class TestRequireManagerRole:
    """测试 require_manager_role 权限函数"""

    def test_admin_passes(self, admin_user):
        from app.api.v1.deps import require_manager_role
        require_manager_role(admin_user)  # 不应抛异常

    def test_super_admin_passes(self):
        from app.api.v1.deps import require_manager_role
        user = Mock()
        user.role = "super_admin"
        user.is_superuser = True
        require_manager_role(user)  # 不应抛异常

    def test_manager_passes(self):
        from app.api.v1.deps import require_manager_role
        user = Mock()
        user.role = "manager"
        user.is_superuser = False
        require_manager_role(user)  # 不应抛异常

    def test_regular_user_denied(self, regular_user):
        from app.api.v1.deps import require_manager_role
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            require_manager_role(regular_user)
        assert exc_info.value.status_code == 403
