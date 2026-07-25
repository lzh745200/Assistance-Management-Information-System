"""app.services.permission_package_service 覆盖率攻坚测试

补齐缺口：
- confirm_import 解析失败返回（297）+ _parse_import_zip 异常分支（343-345）
- _clear_existing_data 非系统角色删除（367-368）与系统角色权限清理（370）
- _import_user_roles / _import_user_permissions / _import_user_menus / _import_user_legacy
  各自的异常记录分支（430-431, 451-452, 467-468, 483-484）

db 使用 MagicMock；ZIP 文件用 tmp_path 真实构造。
"""

import zipfile
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.permission_package_service import PermissionPackageService


class TestConfirmImportParseFailure:
    def test_invalid_json_zip_returns_parse_failure(self, tmp_path):
        # data/roles.json 为非法 JSON → _parse_import_zip 返回 None → confirm 报"解析失败"
        zip_path = tmp_path / "bad.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data/roles.json", "not-json{{{")

        svc = PermissionPackageService(MagicMock())
        result = svc.confirm_import(str(zip_path))

        assert result["success"] is False
        assert result["errors"] == ["解析 ZIP 失败"]
        assert result["message"] == "解析失败"


class TestClearExistingData:
    def test_clears_non_system_and_system_role_permissions(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        sys_role = SimpleNamespace(id=1, name="admin")
        custom_role = SimpleNamespace(id=9, name="custom_role")
        # 第一次 all() → 系统角色；第二次 all() → 非系统角色
        q.all.side_effect = [[sys_role], [custom_role]]

        svc = PermissionPackageService(db)
        svc._clear_existing_data()

        # 非系统角色权限删除 + 系统角色权限删除 + UserRole + UserPermission 共 4 次 execute
        assert db.execute.call_count == 4
        db.delete.assert_called_once_with(custom_role)
        db.flush.assert_called_once()


class TestImportUserRolesError:
    def test_invalid_expires_at_recorded_as_error(self):
        db = MagicMock()
        svc = PermissionPackageService(db)
        stats = svc._init_import_stats()

        stats, errors = svc._import_user_roles(
            [{"role_id": "r1", "user_id": 1, "expires_at": "not-a-date"}],
            {"r1": "r1"},
            stats,
            [],
        )

        assert stats["user_roles_assigned"] == 0
        assert len(errors) == 1
        assert "用户-角色关联导入失败" in errors[0]


class TestImportUserPermissionsError:
    def test_invalid_expires_at_recorded_as_error(self):
        db = MagicMock()
        svc = PermissionPackageService(db)
        stats = svc._init_import_stats()

        stats, errors = svc._import_user_permissions(
            [{"user_id": 1, "permission": "user:read", "expires_at": "bad"}],
            stats,
            [],
        )

        assert stats["user_permissions_assigned"] == 0
        assert len(errors) == 1
        assert "用户权限导入失败" in errors[0]


class TestImportUserMenusError:
    def test_unserializable_menus_recorded_as_error(self):
        db = MagicMock()
        svc = PermissionPackageService(db)
        stats = svc._init_import_stats()

        # set 无法被 json.dumps 序列化 → 触发异常记录分支
        stats, errors = svc._import_user_menus(
            [{"username": "u1", "allowed_menus": {"a", "b"}}],
            stats,
            [],
        )

        assert stats["user_menus_updated"] == 0
        assert len(errors) == 1
        assert "用户菜单「u1」导入失败" in errors[0]


class TestImportUserLegacyError:
    def test_db_error_recorded_as_error(self):
        db = MagicMock()
        db.query.side_effect = RuntimeError("db down")
        svc = PermissionPackageService(db)
        stats = svc._init_import_stats()

        stats, errors = svc._import_user_legacy(
            [{"username": "u1", "role": "admin"}],
            stats,
            [],
        )

        assert stats["user_legacy_updated"] == 0
        assert len(errors) == 1
        assert "用户遗留权限「u1」导入失败" in errors[0]
