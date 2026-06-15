# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 完整打包配置 - Windows版本 (优化版)
将 FastAPI 后端打包为单文件可执行程序，包含所有依赖
版本: 1.0.4
"""

import os
import sys
from pathlib import Path

block_cipher = None
backend_dir = os.path.dirname(os.path.abspath(SPEC))

# 使用 collect_submodules 自动收集子模块，避免手动列出
from PyInstaller.utils.hooks import collect_submodules

# 数据文件列表
datas = [
    (os.path.join(backend_dir, 'alembic'), 'alembic'),
    (os.path.join(backend_dir, '.env.example'), '.'),
    (os.path.join(backend_dir, 'app'), 'app'),
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

# 二进制文件列表
binaries = []

# 优化的 hidden imports - 只保留关键框架级导入
# 使用 collect_submodules 自动收集 app 包下的所有模块
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
    'psutil._pswindows',
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
    'magic',
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
]

# 自动收集 app 包下的所有子模块
hiddenimports += collect_submodules('app')

# 排除不需要的模块（避免 Analysis 时间过长）
excludes = [
    'pytest', 'pytest_asyncio', 'pytest_cov', 'pytest_mock',
    'hypothesis', 'flake8', 'black', 'mypy',
    'tkinter', 'test', 'tests',
    'matplotlib', 'IPython', 'jupyter',
    'notebook', 'spyder', 'pylint',
    # 可选依赖（未安装的不需要导入）
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
    # magic 模块导致 PyInstaller 子进程崩溃（需要 libmagic DLL）
    # file_upload.py 中已用 try/except 保护，运行时自动降级
    'magic',
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
    name='assistance-management-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(backend_dir, '..', 'resources', 'icons', 'app.ico'),
)
