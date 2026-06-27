# -*- mode: python ; coding: utf-8 -*-
"""
麒麟 V10 ARM64 专用 PyInstaller spec
一体化单机版（无 Electron 依赖）

构建命令:
  pyinstaller --clean --noconfirm backend_linux_arm64_standalone.spec
"""

block_cipher = None

a = Analysis(
    ['start.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/**/*.py', 'app'),
        ('app/data/*.json', 'app/data'),
        ('alembic/**/*.py', 'alembic'),
        ('alembic/**/*.mako', 'alembic'),
        ('alembic/versions/*.py', 'alembic/versions'),
        ('alembic.ini', '.'),
    ],
    hiddenimports=[
        # ── FastAPI + Starlette + Uvicorn ──
        'fastapi', 'starlette', 'uvicorn',
        'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'httptools', 'websockets', 'watchfiles',

        # ── SQLAlchemy + SQLite ──
        'sqlalchemy', 'sqlalchemy.dialects.sqlite',
        'sqlalchemy.ext.asyncio', 'aiosqlite',

        # ── 应用模块（确保所有子模块被扫描） ──
        'app.models', 'app.api', 'app.services', 'app.core',
        'app.middleware', 'app.utils', 'app.schemas',
        'app.api.v1', 'app.static_files',

        # ── 认证与安全 ──
        'jose', 'jose.jwt', 'bcrypt', 'passlib', 'passlib.hash',
        'pyotp', 'cryptography', 'cryptography.hazmat',

        # ── 调度与缓存 ──
        'apscheduler', 'apscheduler.schedulers.asyncio',
        'apscheduler.triggers.cron', 'apscheduler.triggers.interval',
        'diskcache',

        # ── 数据处理 ──
        'pandas', 'numpy', 'openpyxl', 'xlsxwriter',

        # ── 文档生成 ──
        'reportlab', 'fpdf2', 'docx', 'pptx', 'mammoth',

        # ── 图像处理 ──
        'PIL', 'PIL.Image', 'qrcode',

        # ── 中文处理 ──
        'jieba',

        # ── Web 工具 ──
        'bleach', 'email_validator', 'multipart', 'python_multipart',
        'httpx', 'aiofiles',

        # ── 日志与监控 ──
        'prometheus_client',

        # ── 文件类型检测 ──
        'magic',

        # ── 配置 ──
        'pydantic', 'pydantic_settings', 'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    excludes=[
        # GUI 框架（后端不需要）
        'tkinter', 'matplotlib.backends.backend_tkagg',
        'PIL.ImageTk', 'PIL.ImageQt',

        # 测试与开发工具
        'unittest', 'test', 'tests', 'pytest', 'coverage',
        'IPython', 'jupyter', 'notebook',

        # 无 ARM64 wheel 或非核心功能
        'scrapy', 'twisted',
        'redis', 'hiredis',
        'selenium', 'playwright',
        'prophet', 'cmdstanpy', 'stanio',
        'scipy', 'sklearn',
        'matplotlib',

        # Windows 专用
        'pywin32_ctypes', 'win32api', 'win32com',

        # 其他不需要的标准库
        'curses', 'distutils', 'setuptools',
        'xmlrpc', 'pydoc', 'difflib', 'ftplib',
    ],
    runtime_hooks=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='assistance-management-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台输出便于诊断
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='assistance-management-backend',
    strip=True,
    upx=True,
    upx_exclude=[],
)
