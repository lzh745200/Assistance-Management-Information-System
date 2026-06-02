"""
配置包管理服务

用于离线多机协作场景：管理员导出用户+组织信息为ZIP配置包，
普通用户在另一台电脑导入配置包后即可登录使用。
"""

import json
import logging
import os
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User

logger = logging.getLogger(__name__)

CURRENT_VERSION = "1.0"


class ConfigPackageService:
    """配置包服务"""

    def __init__(self, db: Session):
        self.db = db

    # ================================================================
    # 导出
    # ================================================================

    def export_package(
        self,
        user_ids: Optional[List[int]] = None,
        org_ids: Optional[List[int]] = None,
        export_all_users: bool = False,
        export_all_orgs: bool = False,
    ) -> Dict[str, Any]:
        """
        导出配置包

        Args:
            user_ids: 要导出的用户ID列表
            org_ids: 要导出的组织ID列表
            export_all_users: 是否导出全部用户
            export_all_orgs: 是否导出全部组织

        Returns:
            {"file_path": str, "file_name": str, "user_count": int, "org_count": int}
        """
        # 查询用户
        if export_all_users:
            users = self.db.query(User).filter(User.is_active.is_(True)).all()
        elif user_ids:
            users = self.db.query(User).filter(User.id.in_(user_ids)).all()
        else:
            users = []

        # 查询组织
        if export_all_orgs:
            orgs = self.db.query(Organization).all()
        elif org_ids:
            orgs = self.db.query(Organization).filter(Organization.id.in_(org_ids)).all()
        else:
            # 自动包含用户所关联的组织
            linked_org_ids = {u.organization_id for u in users if u.organization_id}
            if linked_org_ids:
                orgs = self.db.query(Organization).filter(Organization.id.in_(linked_org_ids)).all()
                # 补充父级组织，确保组织树完整
                orgs = self._expand_parent_orgs(orgs)
            else:
                orgs = self.db.query(Organization).all()

        # 序列化
        users_data = []
        for u in users:
            users_data.append(
                {
                    "username": u.username,
                    "hashed_password": u.hashed_password,
                    "full_name": u.full_name,
                    "email": u.email,
                    "phone": u.phone,
                    "role": u.role or "user",
                    "department": u.department,
                    "position": u.position,
                    "organization_id": u.organization_id,
                    "is_superuser": u.is_superuser or False,
                    "must_change_password": True,
                }
            )

        orgs_data = []
        for o in orgs:
            orgs_data.append(
                {
                    "id": o.id,
                    "name": o.name,
                    "code": o.code,
                    "parent_id": getattr(o, "parent_id", None),
                    "level": getattr(o, "level", None),
                    "type": getattr(o, "type", None),
                    "org_type": getattr(o, "org_type", None),
                    "sort_order": getattr(o, "sort_order", 0),
                    "description": getattr(o, "description", None),
                    "contact_person": getattr(o, "contact_person", None),
                    "contact_phone": getattr(o, "contact_phone", None),
                    "is_active": getattr(o, "is_active", True),
                }
            )

        config_data = {
            "version": CURRENT_VERSION,
            "export_time": datetime.now(timezone.utc).isoformat(),
            "user_count": len(users_data),
            "org_count": len(orgs_data),
        }

        # 生成 ZIP
        from app.utils.paths import get_uploads_path

        upload_dir = str(get_uploads_path("config_packages"))
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"config_package_{timestamp}.zip"
        file_path = os.path.join(upload_dir, file_name)

        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("config.json", json.dumps(config_data, ensure_ascii=False, indent=2))
            zf.writestr("users.json", json.dumps(users_data, ensure_ascii=False, indent=2))
            zf.writestr(
                "organizations.json",
                json.dumps(orgs_data, ensure_ascii=False, indent=2),
            )

        logger.info(
            "配置包已导出: %s (%d 个用户, %d 个组织)",
            file_path,
            len(users_data),
            len(orgs_data),
        )
        return {
            "file_path": file_path,
            "file_name": file_name,
            "user_count": len(users_data),
            "org_count": len(orgs_data),
        }

    def _expand_parent_orgs(self, orgs: list) -> list:
        """补充父级组织，确保导出的组织树完整"""
        existing_ids = {o.id for o in orgs}
        result = list(orgs)
        parent_ids_to_fetch = set()
        for o in orgs:
            pid = getattr(o, "parent_id", None)
            if pid and pid not in existing_ids:
                parent_ids_to_fetch.add(pid)

        while parent_ids_to_fetch:
            parents = self.db.query(Organization).filter(Organization.id.in_(parent_ids_to_fetch)).all()
            if not parents:
                break
            result.extend(parents)
            existing_ids.update(p.id for p in parents)
            parent_ids_to_fetch = set()
            for p in parents:
                pid = getattr(p, "parent_id", None)
                if pid and pid not in existing_ids:
                    parent_ids_to_fetch.add(pid)

        return result

    # ================================================================
    # 导入
    # ================================================================

    def import_package(self, file_path: str) -> Dict[str, Any]:
        """
        导入配置包

        Args:
            file_path: ZIP 文件路径

        Returns:
            {"users_created": int, "users_skipped": int, "orgs_created": int, "orgs_updated": int, "errors": list}
        """
        if not os.path.exists(file_path):
            return {"success": False, "message": "文件不存在", "errors": ["文件不存在"]}

        if not zipfile.is_zipfile(file_path):
            return {
                "success": False,
                "message": "不是有效的ZIP文件",
                "errors": ["不是有效的ZIP文件"],
            }

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                # 验证必要文件
                names = zf.namelist()
                if "config.json" not in names:
                    return {
                        "success": False,
                        "message": "缺少config.json",
                        "errors": ["缺少config.json"],
                    }

                # 读取配置
                config = json.loads(zf.read("config.json").decode("utf-8"))
                version = config.get("version", "unknown")
                if version != CURRENT_VERSION:
                    logger.warning("配置包版本不匹配: %s (期望 %s)", version, CURRENT_VERSION)

                # 读取组织
                orgs_data = []
                if "organizations.json" in names:
                    orgs_data = json.loads(zf.read("organizations.json").decode("utf-8"))

                # 读取用户
                users_data = []
                if "users.json" in names:
                    users_data = json.loads(zf.read("users.json").decode("utf-8"))

            # 导入组织（先导入组织，因为用户依赖 organization_id）
            org_result = self._import_organizations(orgs_data)

            # 导入用户
            user_result = self._import_users(users_data, org_result["id_mapping"])

            self.db.commit()

            result = {
                "success": True,
                "message": "配置包导入成功",
                "orgs_created": org_result["created"],
                "orgs_updated": org_result["updated"],
                "users_created": user_result["created"],
                "users_skipped": user_result["skipped"],
                "errors": org_result["errors"] + user_result["errors"],
            }
            logger.info(
                "配置包导入完成: 组织创建%d/更新%d, 用户创建%d/跳过%d",
                result["orgs_created"],
                result["orgs_updated"],
                result["users_created"],
                result["users_skipped"],
            )
            return result

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": f"JSON解析错误: {e}",
                "errors": [str(e)],
            }
        except Exception as e:
            self.db.rollback()
            logger.error("配置包导入失败: %s", e, exc_info=True)
            return {"success": False, "message": f"导入失败: {e}", "errors": [str(e)]}

    def _import_organizations(self, orgs_data: list) -> Dict[str, Any]:
        """
        导入组织数据

        Returns:
            {"created": int, "updated": int, "id_mapping": {old_id: new_id}, "errors": list}
        """
        created = 0
        updated = 0
        errors = []
        id_mapping: Dict[int, int] = {}

        if not orgs_data:
            return {"created": 0, "updated": 0, "id_mapping": {}, "errors": []}

        # 按层级排序（parent_id 为 None 的先处理）以确保父组织先于子组织创建
        sorted_orgs = sorted(orgs_data, key=lambda o: (o.get("parent_id") or 0, o.get("id", 0)))

        for org_data in sorted_orgs:
            old_id = org_data.get("id")
            code = org_data.get("code")
            name = org_data.get("name", "")

            try:
                # 优先按 code 匹配
                existing = None
                if code:
                    existing = self.db.query(Organization).filter(Organization.code == code).first()

                if existing:
                    # 更新现有组织
                    if name:
                        existing.name = name
                    for field in (
                        "level",
                        "type",
                        "org_type",
                        "sort_order",
                        "description",
                        "contact_person",
                        "contact_phone",
                        "is_active",
                    ):
                        val = org_data.get(field)
                        if val is not None and hasattr(existing, field):
                            setattr(existing, field, val)
                    # 映射 parent_id
                    old_parent = org_data.get("parent_id")
                    if old_parent and old_parent in id_mapping:
                        existing.parent_id = id_mapping[old_parent]
                    id_mapping[old_id] = existing.id
                    updated += 1
                else:
                    # 新建组织
                    new_org = Organization(
                        name=name,
                        code=code,
                        level=org_data.get("level"),
                        type=org_data.get("type"),
                        org_type=org_data.get("org_type"),
                        sort_order=org_data.get("sort_order", 0),
                        description=org_data.get("description"),
                        contact_person=org_data.get("contact_person"),
                        contact_phone=org_data.get("contact_phone"),
                        is_active=org_data.get("is_active", True),
                    )
                    # 映射 parent_id
                    old_parent = org_data.get("parent_id")
                    if old_parent and old_parent in id_mapping:
                        new_org.parent_id = id_mapping[old_parent]

                    self.db.add(new_org)
                    self.db.flush()  # 获取自增 ID
                    id_mapping[old_id] = new_org.id
                    created += 1

            except Exception as e:
                errors.append(f"组织「{name}」导入失败: {e}")
                logger.warning("组织导入失败 code=%s: %s", code, e)

        return {
            "created": created,
            "updated": updated,
            "id_mapping": id_mapping,
            "errors": errors,
        }

    def _import_users(self, users_data: list, org_id_mapping: Dict[int, int]) -> Dict[str, Any]:
        """
        导入用户数据

        Returns:
            {"created": int, "skipped": int, "errors": list}
        """
        created = 0
        skipped = 0
        errors = []

        for user_data in users_data:
            username = user_data.get("username")
            if not username:
                errors.append("缺少用户名的记录已跳过")
                skipped += 1
                continue

            try:
                existing = self.db.query(User).filter(User.username == username).first()
                if existing:
                    skipped += 1
                    continue

                # 转换 organization_id
                old_org_id = user_data.get("organization_id")
                new_org_id = None
                if old_org_id:
                    new_org_id = org_id_mapping.get(old_org_id, old_org_id)

                new_user = User(
                    username=username,
                    hashed_password=user_data.get("hashed_password", ""),
                    full_name=user_data.get("full_name"),
                    email=user_data.get("email"),
                    phone=user_data.get("phone"),
                    role=user_data.get("role", "user"),
                    department=user_data.get("department"),
                    position=user_data.get("position"),
                    organization_id=new_org_id,
                    is_superuser=user_data.get("is_superuser", False),
                    is_active=True,
                    must_change_password=user_data.get("must_change_password", True),
                )

                self.db.add(new_user)
                created += 1

            except Exception as e:
                errors.append(f"用户「{username}」导入失败: {e}")
                logger.warning("用户导入失败 username=%s: %s", username, e)
                skipped += 1

        return {"created": created, "skipped": skipped, "errors": errors}
