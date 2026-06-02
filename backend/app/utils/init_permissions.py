"""权限和角色初始化工具"""

import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_PERMISSIONS = [
    {
        "name": "user:create",
        "resource": "user",
        "action": "create",
        "description": "创建用户",
    },
    {
        "name": "user:read",
        "resource": "user",
        "action": "read",
        "description": "查看用户",
    },
    {
        "name": "user:update",
        "resource": "user",
        "action": "update",
        "description": "更新用户",
    },
    {
        "name": "user:delete",
        "resource": "user",
        "action": "delete",
        "description": "删除用户",
    },
    {
        "name": "village:create",
        "resource": "village",
        "action": "create",
        "description": "创建村庄",
    },
    {
        "name": "village:read",
        "resource": "village",
        "action": "read",
        "description": "查看村庄",
    },
    {
        "name": "village:update",
        "resource": "village",
        "action": "update",
        "description": "更新村庄",
    },
    {
        "name": "village:delete",
        "resource": "village",
        "action": "delete",
        "description": "删除村庄",
    },
    {
        "name": "project:create",
        "resource": "project",
        "action": "create",
        "description": "创建项目",
    },
    {
        "name": "project:read",
        "resource": "project",
        "action": "read",
        "description": "查看项目",
    },
    {
        "name": "project:update",
        "resource": "project",
        "action": "update",
        "description": "更新项目",
    },
    {
        "name": "project:delete",
        "resource": "project",
        "action": "delete",
        "description": "删除项目",
    },
    {
        "name": "fund:create",
        "resource": "fund",
        "action": "create",
        "description": "创建经费",
    },
    {
        "name": "fund:read",
        "resource": "fund",
        "action": "read",
        "description": "查看经费",
    },
    {
        "name": "fund:update",
        "resource": "fund",
        "action": "update",
        "description": "更新经费",
    },
    {
        "name": "fund:delete",
        "resource": "fund",
        "action": "delete",
        "description": "删除经费",
    },
    {
        "name": "school:create",
        "resource": "school",
        "action": "create",
        "description": "创建学校",
    },
    {
        "name": "school:read",
        "resource": "school",
        "action": "read",
        "description": "查看学校",
    },
    {
        "name": "school:update",
        "resource": "school",
        "action": "update",
        "description": "更新学校",
    },
    {
        "name": "school:delete",
        "resource": "school",
        "action": "delete",
        "description": "删除学校",
    },
    {
        "name": "audit:read",
        "resource": "audit",
        "action": "read",
        "description": "查看审计日志",
    },
]


def init_permissions(db) -> int:
    """初始化权限数据"""
    from app.models.permission import Permission

    logger.info("开始初始化权限...")
    created_count = 0

    for perm_data in DEFAULT_PERMISSIONS:
        existing = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing:
            permission = Permission(**perm_data)
            db.add(permission)
            created_count += 1
            logger.info(f"创建权限: {perm_data['name']}")

    db.commit()
    logger.info(f"权限初始化完成: 创建 {created_count} 条")
    return created_count


def init_roles(db) -> int:
    """初始化角色数据"""
    from app.models.permission import Permission
    from app.models.rbac import RbacRole as Role

    logger.info("开始初始化角色...")

    all_permissions = db.query(Permission).all()

    roles_config = [
        {
            "name": "admin",
            "display_name": "管理员",
            "description": "系统管理员，拥有所有权限",
            "is_system": True,
            "permissions": [p.name for p in all_permissions],
        },
        {
            "name": "editor",
            "display_name": "编辑员",
            "description": "可以创建、编辑数据",
            "is_system": True,
            "permissions": [p.name for p in all_permissions if p.action in ["create", "read", "update"]],
        },
        {
            "name": "viewer",
            "display_name": "查看员",
            "description": "只能查看数据",
            "is_system": True,
            "permissions": [p.name for p in all_permissions if p.action == "read"],
        },
    ]

    created_count = 0

    for role_data in roles_config:
        permissions_list = role_data.pop("permissions")
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()

        if not existing:
            role = Role(**role_data)
            role.permissions = json.dumps(permissions_list)
            db.add(role)
            created_count += 1
            logger.info(f"创建角色: {role_data['name']}")

    db.commit()
    logger.info(f"角色初始化完成: 创建 {created_count} 条")
    return created_count


def main():
    """主函数"""
    from app.core.database import SessionLocal

    logger.info("开始初始化权限和角色...")

    db = SessionLocal()
    try:
        init_permissions(db)
        init_roles(db)
        logger.info("初始化完成!")
    except Exception as e:
        db.rollback()
        logger.error(f"初始化失败: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
