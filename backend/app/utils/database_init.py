#!/usr/bin/env python3
"""
数据库初始化工具

提供数据库连接检查、表创建、默认数据初始化等功能。
"""

import logging
import sys
from pathlib import Path

from passlib.context import CryptContext
from sqlalchemy import create_engine, inspect, text

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal, engine  # noqa: E402
from app.models.base import Base as ModelBase  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.role import BasicRole as Role  # noqa: E402
from app.models.user import User  # noqa: E402

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def check_database_connection(db_url: str) -> bool:
    """
    检查数据库连接是否可用

    Args:
        db_url: 数据库URL

    Returns:
        bool: 连接成功返回True，否则返回False
    """
    try:
        test_engine = create_engine(db_url)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ 数据库连接成功")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {str(e)}")
        return False


def create_database_if_not_exists(db_url: str) -> None:
    """
    如果数据库不存在则创建

    Args:
        db_url: 数据库URL
    """
    try:
        from sqlalchemy_utils import create_database, database_exists

        if not database_exists(db_url):
            logger.info(f"📦 创建数据库: {db_url}")
            create_database(db_url)
            logger.info("✅ 数据库创建成功")
        else:
            logger.info("✅ 数据库已存在")
    except Exception as e:
        logger.error(f"❌ 创建数据库失败: {str(e)}")
        raise


def init_database_tables() -> None:
    """初始化数据库表"""
    try:
        logger.info("📋 创建数据库表...")
        # 导入所有模型确保注册到 metadata
        import app.models  # noqa: F401

        ModelBase.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表创建成功")

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"📊 已创建的表: {', '.join(tables)}")
    except Exception as e:
        logger.error(f"❌ 创建数据库表失败: {str(e)}")
        raise


def drop_all_tables() -> None:
    """删除所有表（危险操作！）"""
    try:
        logger.warning("⚠️ 删除所有数据库表...")
        import app.models  # noqa: F401

        ModelBase.metadata.drop_all(bind=engine)
        logger.info("✅ 所有表已删除")
    except Exception as e:
        logger.error(f"❌ 删除表失败: {str(e)}")
        raise


def init_default_roles(db: SessionLocal) -> None:
    """
    初始化默认角色

    Args:
        db: 数据库会话
    """
    try:
        existing_roles = db.query(Role).count()
        if existing_roles > 0:
            logger.info("✅ 角色已存在，跳过初始化")
            return

        logger.info("📋 初始化默认角色...")

        admin_role = Role(
            name="admin",
            description="系统管理员 - 拥有所有权限",
        )

        officer_role = Role(
            name="officer",
            description="军官 - 管理人员和项目",
        )

        villager_role = Role(
            name="villager",
            description="村民 - 查看和参与项目",
        )

        viewer_role = Role(
            name="viewer",
            description="访客 - 仅查看仪表板",
        )

        db.add_all([admin_role, officer_role, villager_role, viewer_role])
        db.commit()
        logger.info("✅ 默认角色初始化成功")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 初始化角色失败: {str(e)}")
        raise


def init_default_users(db: SessionLocal) -> None:
    """
    初始化默认用户

    Args:
        db: 数据库会话
    """
    try:
        existing_users = db.query(User).count()
        if existing_users > 0:
            logger.info("✅ 用户已存在，跳过初始化")
            return

        logger.info("📋 初始化默认用户...")

        admin_user = User(
            username="admin",
            email="admin@military-rural.gov.cn",
            full_name="系统管理员",
            hashed_password=pwd_context.hash("password123"),
            role="admin",
            is_active=True,
            is_superuser=True,
            phone="13800138000",
        )

        officer_user = User(
            username="officer01",
            email="officer01@military.gov.cn",
            full_name="张军官",
            hashed_password=pwd_context.hash("officer123"),
            role="user",
            is_active=True,
            is_superuser=False,
            phone="13900139001",
        )

        db.add_all([admin_user, officer_user])
        db.flush()

        # 为管理员关联顶级组织
        try:
            top_org = db.query(Organization).filter(Organization.parent_id.is_(None)).first()
            if not top_org:
                top_org = Organization(
                    name="军队乡村振兴总部",
                    code="ROOT",
                    org_type="department",
                    level="level_1",
                    is_active=True,
                    description="顶级组织（系统自动创建）",
                )
                db.add(top_org)
                db.flush()
                logger.info(f"创建顶级组织: {top_org.name} (id={top_org.id})")
            admin_user.organization_id = top_org.id
            logger.info(f"管理员已关联顶级组织: {top_org.name}")
        except Exception as e:
            logger.warning(f"关联管理员组织失败: {e}")

        db.commit()
        logger.info("✅ 默认用户初始化成功")
        logger.info("📝 管理员账号: admin / 首次登录需修改密码")
        logger.info("📝 军官账号: officer01 / 首次登录需修改密码")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 初始化用户失败: {str(e)}")
        raise


def reset_database(db_url: str) -> None:
    """
    重置数据库（危险操作）

    Args:
        db_url: 数据库URL
    """
    try:
        from sqlalchemy_utils import database_exists, drop_database

        logger.warning("⚠️ 重置数据库...")

        if database_exists(db_url):
            logger.warning("🗑️ 删除现有数据库...")
            drop_database(db_url)
            logger.info("✅ 数据库已删除")

        create_database_if_not_exists(db_url)
        init_database_tables()
        logger.info("✅ 数据库重置完成")
    except Exception as e:
        logger.error(f"❌ 重置数据库失败: {str(e)}")
        raise


def get_database_info() -> None:
    """显示数据库信息"""
    try:
        logger.info("=" * 60)
        logger.info("📊 数据库信息")

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"📋 表数量: {len(tables)}")

        for table_name in tables:
            columns = inspector.get_columns(table_name)
            logger.info(f"\n表: {table_name}")
            logger.info(f"  列数: {len(columns)}")
            logger.info(f"  列名: {', '.join([col['name'] for col in columns])}")

        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            role_count = db.query(Role).count()

            logger.info("\n📈 数据统计:")
            logger.info(f"  用户数: {user_count}")
            logger.info(f"  角色数: {role_count}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ 获取数据库信息失败: {str(e)}")
        raise


def main() -> None:
    """主函数 - 数据库初始化入口"""
    import argparse

    parser = argparse.ArgumentParser(description="数据库初始化工具")
    parser.add_argument("--reset", action="store_true", help="重置数据库（危险操作）")
    parser.add_argument("--info", action="store_true", help="显示数据库信息")
    parser.add_argument("--init-only", action="store_true", help="仅初始化表，不创建默认数据")

    args = parser.parse_args()
    db_url = settings.DATABASE_URL

    try:
        logger.info("🚀 数据库初始化工具")
        logger.info(f"📍 数据库URL: {db_url}")

        if args.reset:
            reset_database(db_url)
        elif args.info:
            get_database_info()
            return

        logger.info("\n🔧 开始初始化...")

        if not check_database_connection(db_url):
            logger.error("❌ 数据库连接失败，退出")
            return

        create_database_if_not_exists(db_url)
        init_database_tables()

        if not args.init_only:
            db = SessionLocal()
            try:
                init_default_roles(db)
                init_default_users(db)
            finally:
                db.close()

        logger.info("\n" + "=" * 60)
        get_database_info()
        logger.info("✅ 数据库初始化完成!")
    except Exception as e:
        logger.error(f"\n❌ 初始化失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
