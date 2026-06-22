# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 完整打包配置 - 跨平台通用版
将 FastAPI 后端打包为单文件可执行程序，包含所有依赖
版本: 1.2.0 (路径防御增强版)
"""

import os
import sys
from pathlib import Path

from PyInstaller.compat import is_win
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# ---------- 路径定义 ----------
backend_dir = os.path.dirname(os.path.abspath(SPEC))  # 使用 PyInstaller 预定义的 SPEC 变量
project_root = os.path.dirname(backend_dir)               # 项目根目录
resources_dir = os.path.join(project_root, 'resources')
frontend_dir = os.path.join(resources_dir, 'frontend')

# ---------- 检查前端资源（必须存在） ----------
if not os.path.isdir(frontend_dir):
    raise FileNotFoundError(
        f"前端资源目录不存在: {frontend_dir}\n"
        "请确保在运行 PyInstaller 之前执行了 'npm run build' 并将产物复制到 resources/frontend"
    )

# ---------- 数据文件列表 ----------
datas = [
    (os.path.join(backend_dir, 'alembic'), 'alembic'),
    (os.path.join(backend_dir, '.env.example'), '.'),
    (os.path.join(backend_dir, 'app'), 'app'),
    # 前端静态文件 – 使用绝对路径确保添加
    (frontend_dir, 'resources/frontend'),
]

# 自动收集 prophet 包数据
import importlib.util as _ilu
_prophet_spec = _ilu.find_spec('prophet')
if _prophet_spec and _prophet_spec.submodule_search_locations:
    _prophet_dir = list(_prophet_spec.submodule_search_locations)[0]
    datas.append((_prophet_dir, 'prophet'))

# 自动收集 snownlp 包数据
_snownlp_spec = _ilu.find_spec('snownlp')
if _snownlp_spec and _snownlp_spec.submodule_search_locations:
    _snownlp_dir = list(_snownlp_spec.submodule_search_locations)[0]
    datas.append((_snownlp_dir, 'snownlp'))

# 自动收集 prometheus_client 包数据（包含 HTML 模板等静态文件）
datas += collect_data_files('prometheus_client')

# ---------- 二进制文件 ----------
binaries = []

# ---------- 隐藏导入（保持原有，并补充必要模块） ----------
hiddenimports = [
    # FastAPI 和 Web 框架核心
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops.auto',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan.on',
    'fastapi',
    'fastapi.middleware.cors',
    'fastapi.middleware.gzip',
    'starlette',
    'starlette.middleware.sessions',
    'starlette.templating',
    'anyio._backends._asyncio',
    'slowapi',

    # SQLAlchemy 核心
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.ext.asyncio',
    'sqlalchemy.ext.declarative',
    'aiosqlite',
    'alembic.runtime.migration',

    # Pydantic
    'pydantic_settings',
    'pydantic_core',

    # 认证和安全
    'jose.jwt',
    'jose.backends.cryptography_backend',
    'passlib.context',
    'passlib.handlers.bcrypt',
    'passlib.handlers.pbkdf2',
    'passlib.handlers.sha2_crypt',
    'bcrypt',
    'pyotp',
    'qrcode.image.svg',

    # 工具库
    'python_multipart',
    'dotenv',
    'diskcache',
    'dateutil.tz',
    'pytz',
    'filelock',

    # 日志
    'structlog.processors',
    'pythonjsonlogger.jsonlogger',

    # 数据处理
    'openpyxl.styles',
    'openpyxl.utils',
    'pandas.core',
    'pandas.io.excel',
    'numpy.core._multiarray_umath',

    # 文件处理
    'PIL.Image',

    # AI功能
    'sklearn.linear_model',
    'sklearn.preprocessing',
    'prophet',
    'jieba',
    'jieba.analyse',
    'snownlp',

    # 舆情监控
    'scrapy',
    'bs4.builder._lxml',
    'feedparser',

    # 业务指标监控
    'prometheus_client',
]

# Windows 平台特定隐藏导入
if is_win:
    hiddenimports.append('psutil._pswindows')

# 自动收集 app 包下的所有子模块
hiddenimports += collect_submodules('app')

# 显式添加所有 API v1 路由模块（确保 PyInstaller 能正确打包）
hiddenimports += [
    # 子模块包
    'app.api.v1.auth',
    'app.api.v1.data',
    'app.api.v1.import_export',
    'app.api.v1.system',
    # System 子模块
    'app.api.v1.system.health',
    'app.api.v1.system.env',
    'app.api.v1.system.config_package',
    # Monitoring 子模块
    'app.api.v1.monitoring',
    'app.api.v1.monitoring.metrics',
    'app.api.v1.monitoring.secrets',
    'app.api.v1.monitoring.data_tier',
    # 业务模块
    'app.api.v1.organization',
    'app.api.v1.policy',
    'app.api.v1.projects',
    'app.api.v1.school',
    'app.api.v1.supported_village',
    'app.api.v1.supported_village_export',
    'app.api.v1.rural_works',
    'app.api.v1.rural_tasks',
    'app.api.v1.villages',
    'app.api.v1.village_templates',
    'app.api.v1.validation',
    'app.api.v1.report_templates',
    'app.api.v1.approval',
    'app.api.v1.messages',
    'app.api.v1.feedback',
    'app.api.v1.todos',
    'app.api.v1.ai',
    'app.api.v1.map',
    'app.api.v1.project_milestones',
    'app.api.v1.fund_budgets',
    'app.api.v1.fund_lifecycle',
    'app.api.v1.work_logs',
    'app.api.v1.assessment',
    'app.api.v1.system_health',
    'app.api.v1.performance',
    'app.api.v1.monitoring_legacy',
    'app.api.v1.data_quality',
    'app.api.v1.ai_enhanced',
    'app.api.v1.data_sync',
    'app.api.v1.offline_map',
    'app.api.v1.batch_operations',
    'app.api.v1.sync',
    'app.api.v1.user_permissions',
    'app.api.v1.machine_code',
    'app.api.v1.effectiveness',
    'app.api.v1.sentiment',
    'app.api.v1.messages_extended',
    'app.api.v1.encryption',
    'app.api.v1.search',
]

# ---------- 排除不需要的模块 ----------
excludes = [
    'pytest', 'pytest_asyncio', 'pytest_cov', 'pytest_mock',
    'hypothesis', 'flake8', 'black', 'mypy',
    'tkinter', 'test', 'tests',
    'matplotlib', 'IPython', 'jupyter',
    'notebook', 'spyder', 'pylint',
    'docx', 'mammoth', 'apscheduler',
    'jose.backends.native_types',
    'jose.backends.pycryptodome_backend',
    'app.api.v1.users',
    'app.api.v1.user_management',
    'app.api.v1.rbac',
    'app.api.v1.analytics',
    'app.api.v1.statistics',
    'magic',
]

# ---------- Analysis ----------
a = Analysis(
    [os.path.join(backend_dir, 'start.py')],
    pathex=[backend_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    cipher=None,
    noarchive=False,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
)

# ---------- PYZ ----------
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ---------- EXE ----------
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='assistance-management-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(resources_dir, 'icons', 'app.ico'),
)