"""b3 攻坚：覆盖 app.models.rbac 的 _uuid 默认值函数"""
import uuid

from app.models.rbac import (
    AccessLog,
    MachineCodePermission,
    RbacRole,
    RolePermission,
    UserPermission,
    UserRole,
    _uuid,
)


class TestUuidDefault:
    def test_uuid_returns_str(self):
        value = _uuid()
        assert isinstance(value, str)
        # 合法 UUID
        assert str(uuid.UUID(value)) == value

    def test_uuid_unique(self):
        assert _uuid() != _uuid()


class TestRbacModelMethods:
    def test_role_repr_and_to_dict(self):
        role = RbacRole(id="r1", name="admin", description="管理员")
        assert "admin" in repr(role)
        d = role.to_dict()
        assert d["id"] == "r1"
        assert d["name"] == "admin"
        assert d["created_at"] is None
        assert d["updated_at"] is None

    def test_user_role_repr(self):
        ur = UserRole(user_id=1, role_id="r1")
        assert "user_id=1" in repr(ur)

    def test_role_permission_repr(self):
        rp = RolePermission(role_id="r1", permission="fund:read")
        assert "fund:read" in repr(rp)

    def test_user_permission_repr(self):
        up = UserPermission(user_id=2, permission="fund:write")
        assert "fund:write" in repr(up)

    def test_resource_access_control_repr(self):
        rac = ResourceAccessControl(user_id=3, resource_type="fund", resource_id="9")
        assert "fund:9" in repr(rac)

    def test_access_log_repr(self):
        log = AccessLog(user_id="u1", action="read", access_granted=True)
        assert "read" in repr(log)

    def test_machine_code_permission_repr(self):
        mcp = MachineCodePermission(machine_code_id=5, permission="export")
        assert "export" in repr(mcp)
