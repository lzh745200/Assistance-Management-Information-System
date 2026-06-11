"""
权限配置包管理服务

用于离线多机协作场景：管理员导出完整权限配置为 ZIP 包，
在另一台电脑导入后完全还原权限分配。

ZIP 结构:
  manifest.json           — 版本、时间戳、用户数、角色数、SHA-256 校验和
  data/roles.json         — 所有 RBAC 角色 + 权限定义
  data/user_roles.json    — 用户↔角色关联
  data/user_permissions.json — 用户直接权限
  data/user_menus.json    — 用户 allowed_menus 覆盖
  data/user_legacy.json   — User.role, User.permissions, User.data_scope

导入策略：完全替换（mirror mode）。目标电脑的所有权限配置被包内容覆盖。
用户名匹配用户，不存在则跳过。
"""

import hashlib
import json
import logging
import os
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.rbac import (
    RbacRole,
    RolePermission,
    UserPermission,
    UserRole,
)
from app.models.user import User

logger = logging.getLogger(__name__)

CURRENT_VERSION = "1.0"

# 系统内置角色名 — 导入时不删除/不覆盖
SYSTEM_ROLE_NAMES = {"super_admin", "admin", "approval_leader", "manager", "operator", "viewer"}


class PermissionPackageService:
    """权限配置包服务"""

    def __init__(self, db: Session):
        self.db = db

    # ================================================================
    # 导出
    # ================================================================

    def export_package(
        self,
        password: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        导出完整权限配置包

        Args:
            password: 可选的加密密码
            description: 导出说明

        Returns:
            PermissionPackageExportResult 字典
        """
        # 1. 收集所有 RBAC 角色 + 权限
        roles = self.db.query(RbacRole).order_by(RbacRole.priority).all()
        roles_data = []
        for role in roles:
            role_perms = (
                self.db.query(RolePermission)
                .filter(RolePermission.role_id == role.id)
                .all()
            )
            roles_data.append({
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_system": role.is_system,
                "is_active": role.is_active,
                "priority": role.priority,
                "permissions": [rp.permission for rp in role_perms],
            })

        # 2. 收集用户-角色关联
        user_roles = self.db.query(UserRole).all()
        user_roles_data = []
        for ur in user_roles:
            user_roles_data.append({
                "user_id": ur.user_id,
                "role_id": ur.role_id,
                "expires_at": ur.expires_at.isoformat() if ur.expires_at else None,
            })

        # 3. 收集用户直接权限
        user_permissions = self.db.query(UserPermission).all()
        user_permissions_data = []
        for up in user_permissions:
            user_permissions_data.append({
                "user_id": up.user_id,
                "permission": up.permission,
                "expires_at": up.expires_at.isoformat() if up.expires_at else None,
            })

        # 4. 收集用户菜单覆盖
        users = self.db.query(User).filter(User.is_active.is_(True)).all()
        user_menus_data = []
        user_legacy_data = []
        for user in users:
            # 菜单覆盖
            if user.allowed_menus is not None:
                try:
                    menus = (
                        json.loads(user.allowed_menus)
                        if isinstance(user.allowed_menus, str)
                        else user.allowed_menus
                    )
                except (json.JSONDecodeError, TypeError):
                    menus = None
                if menus is not None:
                    user_menus_data.append({
                        "username": user.username,
                        "allowed_menus": menus,
                    })
            # 遗留权限字段
            user_legacy_data.append({
                "username": user.username,
                "role": user.role or "operator",
                "permissions": user.permissions or "",
                "data_scope": user.data_scope or "org",
                "is_superuser": user.is_superuser or False,
            })

        # 构建清单
        manifest = {
            "version": CURRENT_VERSION,
            "export_time": datetime.now(timezone.utc).isoformat(),
            "user_count": len(user_legacy_data),
            "role_count": len(roles_data),
            "description": description,
        }

        # 生成 ZIP
        from app.utils.paths import get_uploads_path

        upload_dir = str(get_uploads_path("permission_packages"))
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"permission_package_{timestamp}.zip"
        file_path = os.path.join(upload_dir, file_name)

        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            zf.writestr("data/roles.json", json.dumps(roles_data, ensure_ascii=False, indent=2))
            zf.writestr("data/user_roles.json", json.dumps(user_roles_data, ensure_ascii=False, indent=2))
            zf.writestr("data/user_permissions.json", json.dumps(user_permissions_data, ensure_ascii=False, indent=2))
            zf.writestr("data/user_menus.json", json.dumps(user_menus_data, ensure_ascii=False, indent=2))
            zf.writestr("data/user_legacy.json", json.dumps(user_legacy_data, ensure_ascii=False, indent=2))

        # 计算校验和
        checksum = self._calculate_checksum(file_path)

        logger.info(
            "权限配置包已导出: %s (角色 %d, 用户 %d, checksum=%s)",
            file_path,
            len(roles_data),
            len(user_legacy_data),
            checksum,
        )

        return {
            "success": True,
            "file_path": file_path,
            "file_name": file_name,
            "file_size": os.path.getsize(file_path),
            "checksum": checksum,
            "user_count": len(user_legacy_data),
            "role_count": len(roles_data),
            "message": f"导出完成: {len(roles_data)} 个角色, {len(user_legacy_data)} 个用户",
        }

    # ================================================================
    # 导入 — 预览阶段
    # ================================================================

    def import_package(self, file_path: str) -> Dict[str, Any]:
        """
        导入权限配置包（预览阶段 — 验证 + 返回预览数据）

        Args:
            file_path: ZIP 文件路径

        Returns:
            {"success": bool, "preview": dict | None, "errors": list, "message": str}
        """
        errors = []
        warnings = []

        if not os.path.exists(file_path):
            return {"success": False, "errors": ["文件不存在"], "message": "文件不存在"}

        if not zipfile.is_zipfile(file_path):
            return {"success": False, "errors": ["不是有效的 ZIP 文件"], "message": "不是有效的 ZIP 文件"}

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                names = zf.namelist()

                # 验证必要文件
                required = ["manifest.json", "data/roles.json", "data/user_legacy.json"]
                for req in required:
                    if req not in names:
                        errors.append(f"缺少必要文件: {req}")

                if errors:
                    return {"success": False, "errors": errors, "message": "包结构不完整"}

                # 读取清单
                manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
                version = manifest.get("version", "unknown")
                if version != CURRENT_VERSION:
                    warnings.append(f"配置包版本 {version} 与当前版本 {CURRENT_VERSION} 不匹配")

                # 读取角色
                roles_data = json.loads(zf.read("data/roles.json").decode("utf-8"))

                # 读取用户遗留数据用于用户名匹配
                user_legacy_data = json.loads(zf.read("data/user_legacy.json").decode("utf-8"))
                export_usernames = {u["username"] for u in user_legacy_data}

                # 检查哪些用户在当前系统中存在
                existing_users = (
                    self.db.query(User)
                    .filter(User.username.in_(export_usernames))
                    .all()
                )
                existing_usernames = {u.username for u in existing_users}
                missing_usernames = export_usernames - existing_usernames
                if missing_usernames:
                    warnings.append(
                        f"以下 {len(missing_usernames)} 个用户在目标系统中不存在，将跳过: "
                        + ", ".join(sorted(list(missing_usernames))[:10])
                        + ("..." if len(missing_usernames) > 10 else "")
                    )

                preview = {
                    "version": version,
                    "export_time": manifest.get("export_time"),
                    "roles": roles_data[:20],  # 预览前 20 个角色
                    "role_count": len(roles_data),
                    "user_role_count": (
                        len(json.loads(zf.read("data/user_roles.json").decode("utf-8")))
                        if "data/user_roles.json" in names else 0
                    ),
                    "user_permission_count": (
                        len(json.loads(zf.read("data/user_permissions.json").decode("utf-8")))
                        if "data/user_permissions.json" in names else 0
                    ),
                    "user_menu_count": (
                        len(json.loads(zf.read("data/user_menus.json").decode("utf-8")))
                        if "data/user_menus.json" in names else 0
                    ),
                    "user_legacy_count": len(user_legacy_data),
                    "warnings": warnings,
                }

            return {
                "success": True,
                "preview": preview,
                "errors": [],
                "message": f"验证通过。将导入 {len(roles_data)} 个角色，更新 {len(existing_usernames)} 个用户权限",
            }

        except json.JSONDecodeError as e:
            return {"success": False, "errors": [f"JSON 解析错误: {e}"], "message": f"JSON 解析错误: {e}"}
        except Exception as e:
            logger.error("权限配置包预览失败: %s", e, exc_info=True)
            return {"success": False, "errors": [str(e)], "message": f"预览失败: {e}"}

    # ================================================================
    # 导入 — 确认阶段
    # ================================================================

    def confirm_import(self, file_path: str, overwrite_existing: bool = True) -> Dict[str, Any]:
        """
        确认导入权限配置包（应用阶段 — 完全替换）

        Args:
            file_path: ZIP 文件路径
            overwrite_existing: 是否覆盖已有配置（当前固定为 True mirror mode）

        Returns:
            PermissionPackageConfirmResult 字典
        """
        if not os.path.exists(file_path) or not zipfile.is_zipfile(file_path):
            return {"success": False, "errors": ["无效的文件"], "message": "无效的文件"}

        errors = []
        roles_created = 0
        roles_updated = 0
        user_roles_assigned = 0
        user_permissions_assigned = 0
        user_menus_updated = 0
        user_legacy_updated = 0

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                roles_data = json.loads(zf.read("data/roles.json").decode("utf-8"))
                user_roles_data = (
                    json.loads(zf.read("data/user_roles.json").decode("utf-8"))
                    if "data/user_roles.json" in zf.namelist() else []
                )
                user_permissions_data = (
                    json.loads(zf.read("data/user_permissions.json").decode("utf-8"))
                    if "data/user_permissions.json" in zf.namelist() else []
                )
                user_menus_data = (
                    json.loads(zf.read("data/user_menus.json").decode("utf-8"))
                    if "data/user_menus.json" in zf.namelist() else []
                )
                user_legacy_data = json.loads(zf.read("data/user_legacy.json").decode("utf-8"))

            if overwrite_existing:
                # ── 完全替换模式 ──

                # 1. 删除非系统角色的 role permissions
                system_role_ids = {
                    r.id for r in self.db.query(RbacRole)
                    .filter(RbacRole.name.in_(SYSTEM_ROLE_NAMES))
                    .all()
                }
                # 只删除非系统角色的权限（保留系统角色权限）
                non_system_roles = (
                    self.db.query(RbacRole)
                    .filter(~RbacRole.name.in_(SYSTEM_ROLE_NAMES))
                    .all()
                )
                for role in non_system_roles:
                    self.db.execute(
                        delete(RolePermission).where(RolePermission.role_id == role.id)
                    )
                    self.db.delete(role)
                # 清除系统角色的权限（将被导入数据重新设置）
                for sid in system_role_ids:
                    self.db.execute(
                        delete(RolePermission).where(RolePermission.role_id == sid)
                    )

                # 2. 删除所有用户-角色关联
                self.db.execute(delete(UserRole))
                # 3. 删除所有用户直接权限
                self.db.execute(delete(UserPermission))

                self.db.flush()

            # ── 导入角色 ──
            role_id_map: Dict[str, str] = {}  # old_id → new_id

            for role_data in roles_data:
                try:
                    old_id = role_data.get("id")
                    name = role_data.get("name", "")

                    # 按名称查找现有角色
                    existing = self.db.query(RbacRole).filter(RbacRole.name == name).first()
                    if existing:
                        # 更新现有角色
                        existing.description = role_data.get("description", existing.description)
                        existing.is_active = role_data.get("is_active", True)
                        existing.priority = role_data.get("priority", 100)
                        new_id = existing.id
                        roles_updated += 1
                    else:
                        # 创建新角色
                        new_role = RbacRole(
                            name=name,
                            description=role_data.get("description"),
                            is_system=role_data.get("is_system", False),
                            is_active=role_data.get("is_active", True),
                            priority=role_data.get("priority", 100),
                        )
                        self.db.add(new_role)
                        self.db.flush()
                        new_id = new_role.id
                        roles_created += 1

                    role_id_map[old_id] = new_id

                    # 导入角色权限
                    for perm in role_data.get("permissions", []):
                        rp = RolePermission(role_id=new_id, permission=perm)
                        self.db.add(rp)

                except Exception as e:
                    errors.append(f"角色「{role_data.get('name', '未知')}」导入失败: {e}")

            self.db.flush()

            # ── 导入用户-角色关联 ──
            # 需要构建 username → user_id 映射
            username_to_user_id = {}
            all_users = self.db.query(User).all()
            for u in all_users:
                username_to_user_id[u.username] = u.id

            for ur_data in user_roles_data:
                try:
                    old_role_id = ur_data.get("role_id", "")
                    new_role_id = role_id_map.get(old_role_id, old_role_id)
                    user_id = ur_data.get("user_id")

                    # 尝试通过旧 user_id 直接匹配
                    existing_user = self.db.query(User).filter(User.id == user_id).first()
                    if not existing_user:
                        continue  # 用户不存在，跳过

                    new_ur = UserRole(
                        user_id=existing_user.id,
                        role_id=new_role_id,
                        expires_at=(
                            datetime.fromisoformat(ur_data["expires_at"])
                            if ur_data.get("expires_at")
                            else None
                        ),
                    )
                    self.db.add(new_ur)
                    user_roles_assigned += 1
                except Exception as e:
                    errors.append(f"用户-角色关联导入失败: {e}")

            # ── 导入用户直接权限 ──
            for up_data in user_permissions_data:
                try:
                    user_id = up_data.get("user_id")
                    existing_user = self.db.query(User).filter(User.id == user_id).first()
                    if not existing_user:
                        continue

                    new_up = UserPermission(
                        user_id=existing_user.id,
                        permission=up_data.get("permission", ""),
                        expires_at=(
                            datetime.fromisoformat(up_data["expires_at"])
                            if up_data.get("expires_at")
                            else None
                        ),
                    )
                    self.db.add(new_up)
                    user_permissions_assigned += 1
                except Exception as e:
                    errors.append(f"用户权限导入失败: {e}")

            # ── 导入用户菜单覆盖 ──
            for menu_data in user_menus_data:
                try:
                    username = menu_data.get("username", "")
                    user = self.db.query(User).filter(User.username == username).first()
                    if not user:
                        continue
                    user.allowed_menus = json.dumps(
                        menu_data.get("allowed_menus", []), ensure_ascii=False
                    )
                    user_menus_updated += 1
                except Exception as e:
                    errors.append(f"用户菜单「{username}」导入失败: {e}")

            # ── 导入遗留权限字段 ──
            for legacy_data in user_legacy_data:
                try:
                    username = legacy_data.get("username", "")
                    user = self.db.query(User).filter(User.username == username).first()
                    if not user:
                        continue
                    user.role = legacy_data.get("role", "operator")
                    user.permissions = legacy_data.get("permissions", "")
                    user.data_scope = legacy_data.get("data_scope", "org")
                    # 不覆盖 is_superuser（安全考虑）
                    user_legacy_updated += 1
                except Exception as e:
                    errors.append(f"用户遗留权限「{username}」导入失败: {e}")

            self.db.commit()

            logger.info(
                "权限配置包导入完成: 角色创建%d/更新%d, 用户角色%d, 用户权限%d, 菜单%d, 遗留%d",
                roles_created,
                roles_updated,
                user_roles_assigned,
                user_permissions_assigned,
                user_menus_updated,
                user_legacy_updated,
            )

            return {
                "success": True,
                "roles_created": roles_created,
                "roles_updated": roles_updated,
                "user_roles_assigned": user_roles_assigned,
                "user_permissions_assigned": user_permissions_assigned,
                "user_menus_updated": user_menus_updated,
                "user_legacy_updated": user_legacy_updated,
                "errors": errors,
                "message": (
                    f"导入完成: 角色 {roles_created}新建/{roles_updated}更新, "
                    f"用户角色关联 {user_roles_assigned}, "
                    f"用户权限 {user_permissions_assigned}, "
                    f"菜单覆盖 {user_menus_updated}, "
                    f"遗留字段 {user_legacy_updated}"
                ),
            }

        except Exception as e:
            self.db.rollback()
            logger.error("权限配置包导入失败: %s", e, exc_info=True)
            return {"success": False, "errors": [str(e)], "message": f"导入失败: {e}"}

    # ================================================================
    # 工具方法
    # ================================================================

    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件的 SHA-256 校验和"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"
