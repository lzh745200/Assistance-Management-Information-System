# -*- mode: python ; coding: utf-8 -*-
"""
帮扶管理系统 - ARM64 (麒麟V10) PyInstaller 打包配置

使用方法:
    pyinstaller bumofu-arm64.spec --clean --noconfirm

目标平台: Linux ARM64 (aarch64)
Python 版本: 3.11
"""

import os
import sys
from pathlib import Path

block_cipher = None

# 数据文件：GeoJSON、种子数据、静态文件
data_files = []

# GeoJSON 数据
geojson_dir = os.path.join('data')
if os.path.isdir(geojson_dir):
    data_files.append((geojson_dir, 'data'))

# 种子数据
seed_dir = os.path.join('seeders')
if os.path.isdir(seed_dir):
    data_files.append((seed_dir, 'seeders'))

# 静态文件
static_dir = os.path.join('app', 'static')
if os.path.isdir(static_dir):
    data_files.append((static_dir, os.path.join('app', 'static')))

# 模板文件
template_dir = os.path.join('app', 'templates')
if os.path.isdir(template_dir):
    data_files.append((template_dir, os.path.join('app', 'templates')))


a = Analysis(
    ['start.py'],
    pathex=['.'],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        # 核心依赖
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.loops',
        'uvicorn.loops.auto',

        # SQLAlchemy 和数据库
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.orm',
        'sqlalchemy.ext.declarative',
        'alembic',

        # Pydantic
        'pydantic',
        'pydantic_settings',
        'pydantic.deprecated',

        # 数据处理
        'numpy',
        'pandas',

        # 安全
        'bcrypt',
        'jose',
        'python_jose',

        # 文件处理
        'aiofiles',
        'multipart',
        'python_multipart',

        # 模板
        'jinja2',
        'jinja2.ext',

        # 邮件（即使不启用，导入也需要存在）
        'email_validator',

        # 缓存
        'diskcache',

        # 日志
        'logging',
        'logging.handlers',

        # HTTP
        'httpx',
        'starlette',
        'starlette.middleware',
        'starlette.middleware.cors',

        # 工具
        'openpyxl',
        'xlsxwriter',
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib.backends',
        'matplotlib.backends.backend_tkagg',
        'IPython',
        'notebook',
        'jupyter_client',
        'jupyter_core',
        'scipy',
        'test',
        'unittest',
        'pytest',
    ],
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
    name='bumofu-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Linux: strip 符号表减小体积
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台输出（便于日志排查）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # 使用当前架构（ARM64 编译时使用 ARM64 机器）
    codesign_identity=None,
    entitlements_file=None,
)
