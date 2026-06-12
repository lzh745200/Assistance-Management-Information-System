# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 - Windows 32-bit (x86) 版本
将 FastAPI 后端打包为 32 位单文件可执行程序
版本: 1.2.0

注意: 32-bit 版本排除了部分重量级依赖以保证兼容性
排除: scipy, prophet, scikit-learn (不支持 Windows x86 构建)
保留: 所有核心业务功能、报表生成、数据分析（pandas/numpy）
"""

import os
import sys
from pathlib import Path

block_cipher = None
backend_dir = os.path.dirname(os.path.abspath(SPEC))

from PyInstaller.compat import is_win
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 数据文件列表
datas = [
    (os.path.join(backend_dir, 'alembic'), 'alembic'),
    (os.path.join(backend_dir, '.env.example'), '.'),
    (os.path.join(backend_dir, 'app'), 'app'),
]

# 自动收集 snownlp 包数据
import importlib.util as _ilu
_snownlp_spec = _ilu.find_spec('snownlp')
if _snownlp_spec and _snownlp_spec.submodule_search_locations:
    _snownlp_dir = list(_snownlp_spec.submodule_search_locations)[0]
    datas.append((_snownlp_dir, 'snownlp'))

# 二进制文件列表
binaries = []

# hidden imports - 32-bit 精简版
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
    'passlib.handlers.sha_256',
    'bcrypt',
    'pyotp',

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

    # 数据处理 (保留 pandas/numpy 基本功能)
    'openpyxl.styles',
    'openpyxl.utils',
    'pandas.core',
    'pandas.io.excel',

    # 文件处理
    'PIL.Image',

    # AI功能 - 精简版
    'jieba',
    'jieba.analyse',
    'snownlp',
]

if is_win:
    hiddenimports.append('psutil._pswindows')

# 自动收集 app 包下的所有子模块
hiddenimports += collect_submodules('app')

# 显式添加所有 API v1 路由模块
hiddenimports += [
    'app.api.v1.auth',
    'app.api.v1.data',
    'app.api.v1.import_export',
    'app.api.v1.system',
    'app.api.v1.system.health',
    'app.api.v1.system.env',
    'app.api.v1.system.config_package',
    'app.api.v1.monitoring',
    'app.api.v1.monitoring.metrics',
    'app.api.v1.monitoring.secrets',
    'app.api.v1.monitoring.data_tier',
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

# 32-bit 排除列表 - 排除不支持 x86 的重量级包
excludes = [
    'pytest', 'pytest_asyncio', 'pytest_cov', 'pytest_mock',
    'hypothesis', 'flake8', 'black', 'mypy',
    'tkinter', 'test', 'tests',
    'matplotlib', 'IPython', 'jupyter',
    'notebook', 'spyder', 'pylint',
    # 32-bit 不兼容: 科学计算重量级包
    'scipy', 'scipy.signal', 'scipy.stats',
    'prophet',
    'sklearn', 'sklearn.linear_model', 'sklearn.preprocessing',
    # 可选依赖
    'docx', 'mammoth', 'apscheduler',
    # 不必要的 jose 后端
    'jose.backends.native_types',
    'jose.backends.pycryptodome_backend',
    # 不存在的旧路径
    'app.api.v1.users',
    'app.api.v1.user_management',
    'app.api.v1.rbac',
    'app.api.v1.analytics',
    'app.api.v1.statistics',
    'magic',
    'scrapy',
]

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
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='military-rural-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86',
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(backend_dir, '..', 'resources', 'icons', 'app.ico'),
)
