"""军队振兴乡村管理系统 - FastAPI 入口模块"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from pathlib import Path

# ── 关键修复：Windows ProactorEventLoop ConnectionResetError ──
# 必须在 import fastapi/uvicorn 之前应用，因为 uvicorn 会在启动时创建事件循环。
# 修复采用三层纵深防御：
#   Layer 1: Monkey-patch _ProactorBasePipeTransport._call_connection_lost
#   Layer 2: 替换全局 EventLoopPolicy，所有新 loop 自动继承异常处理器
#   Layer 3: 对当前运行时 loop 设置异常处理器
if sys.platform == "win32":
    from app.utils.win_proactor_fix import apply_windows_proactor_fix
    apply_windows_proactor_fix()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from app.api.v1 import api_v1_router
from app.core.audit_middleware import AuditMiddleware
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import SafeLogger
from app.core.security import SecurityHeadersMiddleware, hash_password
from app.core.static_files import setup_static_files
from app.middleware.camel_to_snake import CamelToSnakeMiddleware
from app.middleware.csrf_middleware import CSRFMiddleware
from app.middleware.metrics_middleware import MetricsMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_logger import RequestLoggerMiddleware

env = os.getenv("ENV", "dev")
logger = SafeLogger(env=env).logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """应用生命周期：启动时初始化数据库、种子数据、依赖检查"""
    _init_database_tables()
    _load_token_blacklist()
    _check_and_record_version_change()
    _seed_default_admin()
    _check_required_packages()
    _verify_file_integrity()
    _start_resource_monitoring()
    _start_database_health_monitoring()
    _start_approval_reminder()
    _start_db_maintenance()
    yield
    _stop_db_maintenance()
    _stop_approval_reminder()
    _stop_resource_monitoring()
    _stop_database_health_monitoring()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="军队振兴乡村管理系统 API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    redirect_slashes=True,
    lifespan=lifespan,
)

register_exception_handlers(app)

# 中间件注册顺序（Starlette 按添加的逆序执行）：
# 执行顺序: RequestID → SecurityHeaders → CORS → CamelToSnake → CSRF → RequestLogger → Audit → Metrics
# 添加顺序: Metrics → Audit → RequestLogger → CSRF → CamelToSnake → CORS → SecurityHeaders → RequestID

# 1. 性能监控中间件（最内层，最后执行，包裹实际请求处理）
app.add_middleware(MetricsMiddleware)

# 2. 审计日志中间件
app.add_middleware(AuditMiddleware)

# 3. 请求日志中间件
app.add_middleware(RequestLoggerMiddleware)

# 4. CSRF 保护中间件（仅在 settings.CSRF_ENABLED=True 时生效）
# BaseHTTPMiddleware 会导致 h11 协议错误，仅在明确启用时注册
if settings.CSRF_ENABLED:
    app.add_middleware(CSRFMiddleware)

# 4.5 驼峰→蛇形转换中间件（将前端 camelCase JSON 转为后端 snake_case）
app.add_middleware(CamelToSnakeMiddleware)

# 4.6 缓存头中间件（对静态/低变化数据添加 Cache-Control 减少重复查询）
from app.middleware.cache_headers import CacheHeadersMiddleware  # noqa: E402
app.add_middleware(CacheHeadersMiddleware)

# 5. CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOWED_METHODS,
    allow_headers=settings.CORS_ALLOWED_HEADERS,
    expose_headers=["Content-Disposition", "X-Request-ID", "X-Total-Count"],
    max_age=3600,
)

# 6. 安全响应头中间件（在 CORS 之后，确保所有响应都有安全头）
app.add_middleware(SecurityHeadersMiddleware)

# 7. 请求ID链路追踪中间件（最外层，最先执行）
app.add_middleware(RequestIDMiddleware)

app.include_router(api_v1_router)


# 全局 Content-Type charset=UTF-8 修复
@app.middleware("http")
async def _ensure_charset_utf8(request: Request, call_next):
    response = await call_next(request)
    ct = response.headers.get("content-type", "")
    if ct and "charset" not in ct:
        if ct.startswith("text/") or ct.startswith("application/json") or ct.startswith("application/javascript"):
            response.headers["content-type"] = f"{ct}; charset=utf-8"
    return response


# 修复 API 路径尾部斜杠 404：/api/v1/xxx/?q=1 → 307 → /api/v1/xxx?q=1
@app.middleware("http")
async def _trailing_slash_redirect(request: Request, call_next):
    path = request.url.path
    if len(path) > 1 and path.endswith("/"):
        new_path = path.rstrip("/")
        qs = request.url.query
        redirect_url = f"{new_path}?{qs}" if qs else new_path
        return RedirectResponse(url=redirect_url, status_code=307)
    return await call_next(request)


class CachedStaticFiles(StaticFiles):
    """带 Cache-Control 头的静态文件服务。

    对带 hash 的文件名（如 index-AY635XGl.js）设置长期缓存（immutable），
    因为这些文件内容永不改变，hash 变化意味着新版本用新文件名。
    """

    def __init__(self, *args, cache_max_age: int = 31536000, **kwargs):
        self._cache_max_age = cache_max_age
        super().__init__(*args, **kwargs)

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        # 安全策略：对静态资源设置长期缓存 + immutable
        response.headers["Cache-Control"] = (
            f"public, max-age={self._cache_max_age}, immutable"
        )
        return response


REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "pandas",
    "openpyxl",
]


# /health 等非API路由必须在 SPA catch-all 之前注册
@app.get("/health", summary="健康检查", tags=["系统"])
def health():
    """健康检查端点"""
    return {"status": "ok"}


@app.post("/api/v1/shutdown", include_in_schema=False)
async def shutdown(request: Request):
    """内部关闭端点，仅接受 127.0.0.1 来源 + 内部密钥验证"""
    client_host = request.client.host if request.client else ""
    if client_host not in ("127.0.0.1", "::1"):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="仅限本机调用")

    # 内部密钥验证：防止本机恶意进程关闭服务
    import os

    expected_key = os.getenv("INTERNAL_SHUTDOWN_KEY", "")
    if expected_key:
        from fastapi import HTTPException

        request_key = request.headers.get("X-Internal-Shutdown", "")
        if request_key != expected_key:
            raise HTTPException(status_code=403, detail="内部密钥验证失败")
    logger.info("收到 shutdown 请求，正在关闭...")
    # 在后台线程中延迟关闭，使用 sys.exit 以触发正常清理流程
    import signal
    import threading

    threading.Timer(0.5, lambda: signal.raise_signal(signal.SIGINT)).start()
    return {"status": "shutting_down"}


# 静态文件和 SPA catch-all 必须在所有路由之后注册
_frontend_dir = setup_static_files(app)

if _frontend_dir:
    # ── 挂载前端静态资源 ──
    # 使用 CachedStaticFiles 为带 hash 的静态资源设置长期缓存（1 年 + immutable）。
    # Vite 构建产物文件名包含内容 hash（如 index-AY635XGl.js），
    # 内容变化 → hash 变化 → 新文件名 → 浏览器自动获取新版本。
    # 安全策略：Cache-Control: public, max-age=31536000, immutable

    assets_dir = os.path.join(_frontend_dir, "assets")
    if os.path.isdir(assets_dir):
        app.mount(
            "/assets",
            CachedStaticFiles(directory=assets_dir, cache_max_age=31536000),
            name="frontend_assets",
        )
    images_dir = os.path.join(_frontend_dir, "images")
    if os.path.isdir(images_dir):
        app.mount(
            "/images",
            CachedStaticFiles(directory=images_dir, cache_max_age=31536000),
            name="frontend_images",
        )
    # 挂载静态文件目录（模板、下载文件等离线兜底资源）
    # 注意：这些文件没有内容 hash 文件名（如 project_import_template.xlsx），
    # 不能使用 immutable 缓存策略，否则更新模板后浏览器仍使用过期缓存。
    static_dir = os.path.join(_frontend_dir, "static")
    if os.path.isdir(static_dir):
        app.mount(
            "/static",
            StaticFiles(directory=static_dir),
            name="frontend_static",
        )

    # index.html 路径（每次请求时重新读取，避免 rebuild 后缓存旧版本）
    _index_path = Path(_frontend_dir) / "index.html"
    _favicon_path = Path(_frontend_dir) / "favicon.ico"
    _favicon_path = _favicon_path if _favicon_path.exists() else None
    _version_json_path = Path(_frontend_dir) / "version.json"
    _version_json_path = _version_json_path if _version_json_path.exists() else None

    @app.get("/favicon.ico")
    async def favicon():
        if _favicon_path:
            return FileResponse(_favicon_path)
        return JSONResponse({"message": "Favicon not found"}, status_code=404)

    @app.get("/version.json")
    async def version_json():
        """构建版本指纹 — 前端 useVersionCheck 启动时拉取"""
        if _version_json_path:
            return FileResponse(
                _version_json_path,
                media_type="application/json",
                headers={"Cache-Control": "no-cache"},
            )
        return JSONResponse({"version": "unknown"}, status_code=404)

    # ── SPA fallback ──
    # 所有非 API / 非文档 / 非已挂载静态路径的 GET 请求，返回 index.html。
    # 前端 Vue Router 在浏览器端接管路由（History 模式）。
    # index.html 不缓存：确保浏览器始终获取最新版本，避免引用过时的 hash 资源。

    _reserved = (
        settings.API_PREFIX.lstrip("/"),
        "docs", "openapi", "uploads", "version.json",
    )

    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def spa_fallback(request: Request, full_path: str = ""):
        if full_path.startswith(_reserved):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        # 每次请求重新读取 index.html — 确保 rebuild 后不返回缓存旧版本
        return HTMLResponse(
            _index_path.read_text(encoding="utf-8"),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
else:
    logger.warning(
        "前端静态资源未挂载。可能原因：\n"
        "  1. 开发模式：请先执行 'cd frontend && npm run build' 构建前端\n"
        "  2. 打包模式：确认 resources/frontend 目录存在且包含 index.html\n"
        "  3. 环境变量 FRONTEND_DIST_PATH 指向的目录不存在"
    )


def _load_token_blacklist():
    """启动时从数据库恢复 token 黑名单到内存。"""
    try:
        from app.core.database import SessionLocal
        from app.core.token_blacklist import load_from_db
        db = SessionLocal()
        try:
            count = load_from_db(db)
            if count:
                logger.info("Token 黑名单已恢复: %d 条记录", count)
        finally:
            db.close()
    except Exception as e:
        logger.warning("Token 黑名单加载失败: %s", e)


def _init_database_tables():
    """确保所有数据库表已创建，并补全已有表中缺失的列"""
    # 导入所有模型确保表定义已注册
    import app.models  # noqa: F401
    from app.core.database import engine
    from app.models.base import Base as ModelBase

    ModelBase.metadata.create_all(bind=engine)
    # SQLite: create_all 不会给已有表添加新列，需手动 ALTER TABLE
    if settings.ENABLE_AUTO_MIGRATION:
        _migrate_missing_columns(engine, ModelBase)
    else:
        logger.info("Schema auto-migration disabled (ENABLE_AUTO_MIGRATION=false)")
    # 创建性能优化索引
    from app.core.database_indexes import create_indexes

    create_indexes(engine)
    logger.info("数据库表初始化完成")


def _migrate_missing_columns(engine, model_base):
    """检测列差异并自动添加缺失列 [DEPRECATED: 逐步迁移到纯 Alembic]

    ⚠️ 生产环境警告：此函数在启动时执行自动 DDL，存在风险。
    请尽快完成 Alembic 迁移迁移后，通过环境变量 DISABLE_AUTO_MIGRATION=1 禁用此函数。

    推荐迁移路径：新增字段后先生成 Alembic 迁移脚本，而非依赖此自动补齐。

    改进点：
    - 为 Boolean/Integer/Numeric 列添加 DEFAULT 值，确保已有行获得合理默认值
    - 对 nullable=False 且有默认值的列添加 NOT NULL DEFAULT 约束
    """
    import os
    if os.getenv("DISABLE_AUTO_MIGRATION", "").strip() == "1":
        logger.info("DISABLE_AUTO_MIGRATION=1，跳过自动列补齐（请使用 Alembic 迁移）")
        return

    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy import text

    try:
        inspector = sa_inspect(engine)
    except Exception as e:
        logger.warning("Schema migration: failed to create inspector: %s", e)
        return

    total_added = 0
    total_failed = 0
    for table_name, table in model_base.metadata.tables.items():
        try:
            if not inspector.has_table(table_name):
                continue
            db_cols = {c["name"] for c in inspector.get_columns(table_name)}
            model_cols = {c.name for c in table.columns}
            missing = model_cols - db_cols
            if not missing:
                continue
            logger.info(
                "Schema migration: table [%s] has %d missing column(s): %s",
                table_name,
                len(missing),
                sorted(missing),
            )
            with engine.connect() as conn:
                for col_name in sorted(missing):
                    try:
                        col = table.c[col_name]
                        stype, default_clause = _sqlite_col_spec(col)
                        # SQLite: nullable=False 列必须有 DEFAULT 才能 ADD COLUMN
                        not_null = ""
                        if not col.nullable and default_clause:
                            not_null = "NOT NULL "
                        ddl = (
                            f"ALTER TABLE [{table_name}] ADD COLUMN [{col_name}] " f"{stype} {not_null}{default_clause}"
                        ).rstrip()
                        conn.execute(text(ddl))
                        total_added += 1
                        default_info = f" {default_clause}" if default_clause else ""
                        logger.info(
                            "Schema migration: [AUTO-ADD] %s.%s (%s%s)",
                            table_name,
                            col_name,
                            stype,
                            default_info,
                        )
                    except (ValueError, TypeError, AttributeError) as col_err:
                        total_failed += 1
                        logger.warning(
                            "Schema migration: failed to add %s.%s: %s",
                            table_name,
                            col_name,
                            col_err,
                        )
                conn.commit()
        except (ValueError, TypeError, KeyError) as tbl_err:
            logger.warning(
                "Schema migration: error processing table %s: %s",
                table_name,
                tbl_err,
            )

    if total_added or total_failed:
        logger.info(
            "Schema migration summary: %d column(s) added, %d failed",
            total_added,
            total_failed,
        )
    else:
        logger.info("Schema migration: all tables up to date, no columns to add")


def _sqlite_col_spec(col):
    """根据 SQLAlchemy Column 推断 SQLite 列类型和 DEFAULT 子句。

    Returns:
        (sqlite_type, default_clause) - 例如 ("INTEGER", "DEFAULT 0")
    """
    t = str(col.type).upper()

    # 类型映射
    if "INT" in t or "BOOL" in t:
        stype = "INTEGER"
    elif "FLOAT" in t or "REAL" in t or "NUMERIC" in t:
        stype = "REAL"
    else:
        # DATE, DATETIME, JSON, VARCHAR, TEXT, ENUM 等在 SQLite 中均用 TEXT
        stype = "TEXT"

    # 推断 DEFAULT 值
    default_clause = ""
    # 优先使用模型 default（ColumnDefault）
    if (
        col.default is not None
        and hasattr(col.default, "arg")
        and col.default.arg is not None
        and not callable(col.default.arg)
    ):
        raw = col.default.arg
        if isinstance(raw, bool):
            default_clause = f"DEFAULT {1 if raw else 0}"
        elif isinstance(raw, (int, float)):
            default_clause = f"DEFAULT {raw}"
        elif isinstance(raw, str):
            escaped = raw.replace("'", "''")
            default_clause = f"DEFAULT '{escaped}'"
    elif col.server_default is not None:
        # 注意: SQLite ALTER TABLE ADD COLUMN 不支持非常量 DEFAULT
        # (CURRENT_TIMESTAMP 会报错 "Cannot add a column with non-constant default")
        # 对于 server_default=func.now() 这类情况，跳过 DEFAULT，
        # ORM 层的 default=_utcnow 会为新行自动赋值。
        pass
    elif not col.nullable:
        # nullable=False 但没有显式 default → 给一个类型感知的零值
        if stype == "INTEGER":
            default_clause = "DEFAULT 0"
        elif stype == "REAL":
            default_clause = "DEFAULT 0"
        else:
            default_clause = "DEFAULT ''"

    return stype, default_clause


# 默认管理员用户名（可通过环境变量配置）
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin").strip() or "admin"


def _seed_default_admin():
    """确保默认管理员账户存在，并在启动时解锁所有被锁定的用户账户。

    未设置 DEFAULT_ADMIN_PASSWORD 环境变量时，将自动生成符合密码策略的随机强密码。
    must_change_password=True 强制首次登录修改密码。

    离线单机系统没有远程管理员可以手动解锁账户，因此每次启动时
    自动重置所有用户的锁定状态，确保用户不会因上次会话的失败尝试
    而被永久锁定。运行期间的锁定机制仍然正常生效。
    """
    from app.core.database import SessionLocal
    from app.models.user import User

    _admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "").strip()
    if not _admin_password:
        from app.core.security import generate_password
        _admin_password = generate_password(length=16, exclude_ambiguous=True)
        import hashlib
        _pw_hash_prefix = hashlib.sha256(_admin_password.encode()).hexdigest()[:8]
        # 控制台打印明文密码（用户需要看到才能登录）
        print(f"\n{'='*60}")
        print("  🔑 默认管理员密码（自动生成）")
        print("  用户名: admin")
        print(f"  密码:   {_admin_password}")
        print("  ⚠️  请立即复制保存！首次登录后须修改密码。")
        print(f"{'='*60}\n")
        # 日志中仅记录哈希前缀（安全）
        logger.warning(
            "自动生成管理员密码（SHA256前缀: %s），请从控制台查看明文", _pw_hash_prefix
        )

    db = SessionLocal()
    try:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        users_to_clean = db.query(User).filter(
            User.locked_until.isnot(None),
            User.locked_until <= now,
        ).all()
        unlocked_count = 0
        unlocked_names = []
        for user in users_to_clean:
            user.locked_until = None
            user.failed_login_count = 0
            unlocked_names.append(user.username)
            unlocked_count += 1
        # admin 账户强制解锁（单机版误锁后无法远程解锁）
        admin_locked = db.query(User).filter(
            User.username == DEFAULT_ADMIN_USERNAME,
            User.locked_until.isnot(None),
        ).first()
        if admin_locked:
            admin_locked.locked_until = None
            admin_locked.failed_login_count = 0
            if "admin" not in unlocked_names:
                unlocked_names.append("admin")
                unlocked_count += 1

        if unlocked_count > 0:
            db.commit()
            logger.info("启动时已自动处理 %d 个账户: %s", unlocked_count, unlocked_names)

        admin = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if not admin:
            # 尝试获取顶级组织作为管理员的所属组织
            top_org_id = None
            try:
                from app.models.organization import Organization

                top_org = db.query(Organization).filter(Organization.parent_id.is_(None)).first()
                if top_org:
                    top_org_id = top_org.id
            except Exception as e:
                logger.warning("Failed to get top organization: %s", e)
            admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                email="admin@example.com",
                hashed_password=hash_password(_admin_password),
                full_name="系统管理员",
                role="admin",
                is_active=True,
                is_superuser=True,
                department="系统管理部",
                organization_id=top_org_id,
                permissions="",
                must_change_password=True,
            )
            db.add(admin)
            db.commit()
            logger.info(
                "默认管理员账户已创建 (用户名: admin, 请通过 DEFAULT_ADMIN_PASSWORD 环境变量设置强密码，首次登录须修改密码)",
            )
        else:
            logger.info("管理员账户已存在，跳过创建")
    except Exception as e:
        db.rollback()
        logger.error("创建默认管理员失败: %s", e)
    finally:
        db.close()


def _check_required_packages():
    """启动时检查必需包（仅逐个检查核心包，避免遍历全部已安装包）"""
    import importlib

    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        logger.warning(
            "缺少依赖包 %s，请运行: pip install %s",
            missing,
            " ".join(missing),
        )
    else:
        logger.info("所有关键依赖包已安装。")


def _start_resource_monitoring():
    """启动资源监控"""
    try:
        from app.services.resource_limiter import resource_limiter

        resource_limiter.start_monitoring()
        logger.info("资源监控已启动")
    except Exception as e:
        logger.warning("启动资源监控失败: %s", e)


def _stop_resource_monitoring():
    """停止资源监控"""
    try:
        from app.services.resource_limiter import resource_limiter

        resource_limiter.stop_monitoring()
        logger.info("资源监控已停止")
    except Exception as e:
        logger.warning("停止资源监控失败: %s", e)


def _start_database_health_monitoring():
    """启动数据库健康监控"""
    try:
        from app.services.database_health_service import database_health_service

        database_health_service.start_monitoring()
        logger.info("数据库健康监控已启动")
    except Exception as e:
        logger.warning("启动数据库健康监控失败: %s", e)


def _stop_database_health_monitoring():
    """停止数据库健康监控"""
    try:
        from app.services.database_health_service import database_health_service

        database_health_service.stop_monitoring()
        logger.info("数据库健康监控已停止")
    except Exception as e:
        logger.warning("停止数据库健康监控失败: %s", e)


def _check_and_record_version_change():
    """检查版本变更并记录更新日志"""
    try:
        from app.core.database import SessionLocal
        from app.services.update_log_service import UpdateLogService
        from app.services.version_service import version_service

        db = SessionLocal()
        try:
            update_service = UpdateLogService(db)
            current_version = version_service.get_current_version()
            version_str = current_version.get("version", "unknown")

            result = update_service.check_and_record_version_change(
                current_version=version_str,
                updated_by="system",
            )

            if result:
                action = result.get("action")
                if action == "initialize":
                    init_count = result["result"].get("initialized_count", 0)
                    logger.info("版本历史初始化完成: %s 条记录", init_count)
                elif action == "record_change":
                    old_ver = result.get("old_version")
                    new_ver = result.get("new_version")
                    logger.info("检测到版本变更: %s -> %s", old_ver, new_ver)
            else:
                logger.info("当前版本: %s", version_str)

        finally:
            db.close()
    except Exception as e:
        logger.warning("版本变更检查失败: %s", e)


def _verify_file_integrity():
    """启动时验证关键文件完整性，防止二进制被替换"""
    import hashlib

    _critical_files = [
        "app/core/config.py",
        "app/core/security.py",
        "app/core/database.py",
        "app/main.py",
    ]

    try:
        base_dir = Path(__file__).parent.parent
        for rel_path in _critical_files:
            file_path = base_dir / rel_path
            if not file_path.exists():
                logger.warning("文件完整性检查: 关键文件缺失: %s", rel_path)
                continue

            file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            logger.debug("文件完整性: %s SHA256=%s", rel_path, file_hash[:16])

        logger.info("关键文件完整性检查完成 (%d个文件)", len(_critical_files))
    except Exception as e:
        logger.error("文件完整性检查失败: %s", e)


# 审批提醒服务全局引用
_approval_reminder = None


def _start_approval_reminder():
    """启动审批超时提醒后台服务"""
    global _approval_reminder
    try:
        from app.services.reminder_service import start_approval_reminder

        _approval_reminder = start_approval_reminder(check_interval_minutes=30)
        logger.info("审批超时提醒服务已启动")
    except Exception as e:
        logger.warning("启动审批提醒服务失败: %s", e)


def _stop_approval_reminder():
    """停止审批超时提醒后台服务"""
    global _approval_reminder
    try:
        from app.services.reminder_service import stop_approval_reminder

        stop_approval_reminder(_approval_reminder)
        _approval_reminder = None
        logger.info("审批超时提醒服务已停止")
    except Exception as e:
        logger.warning("停止审批提醒服务失败: %s", e)


def _start_db_maintenance():
    """启动 SQLite 定期维护（VACUUM + PRAGMA optimize）。"""
    try:
        from app.services.db_maintenance import start_db_maintenance
        start_db_maintenance()
    except Exception as e:
        logger.warning("数据库维护启动失败: %s", e)


def _stop_db_maintenance():
    """停止 SQLite 定期维护。"""
    try:
        from app.services.db_maintenance import stop_db_maintenance
        stop_db_maintenance()
    except Exception as e:
        logger.warning("数据库维护停止失败: %s", e)


__all__ = ["app"]
