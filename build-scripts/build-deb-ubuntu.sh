#!/bin/bash
# ============================================================
# 军队乡村振兴管理系统 — 一体化 .deb 构建脚本
# ============================================================
# 在 Ubuntu 22.04+ (x86_64 或 ARM64) 上运行此脚本，
# 自动完成所有依赖安装、前后端构建、.deb 打包。
#
# 使用方法:
#   chmod +x build-deb-ubuntu.sh
#   sudo ./build-deb-ubuntu.sh
#
# 生成产物: dist/ 目录下的 .deb 安装包
# ============================================================

set -euo pipefail

APP_NAME="military-rural-system"
APP_TITLE="军队乡村振兴管理系统"
VERSION="${VERSION:-1.2.0}"
ARCH="${ARCH:-$(dpkg --print-architecture)}"
BUILD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_ROOT}/build/deb-${ARCH}"
DIST_DIR="${BUILD_ROOT}/dist"
PROJECT_ROOT="${BUILD_ROOT}"

echo "=============================================="
echo "  ${APP_TITLE}"
echo "  .deb 安装包构建 — v${VERSION}"
echo "  目标架构: ${ARCH}"
echo "=============================================="

# ─── 0. 系统检查 ───
echo "[0/7] 系统环境检查..."

if [[ "$EUID" -ne 0 ]]; then
    echo "错误: 请使用 sudo 运行此脚本（需要安装系统包）"
    exit 1
fi

if [[ ! -f /etc/os-release ]]; then
    echo "错误: 无法检测操作系统版本（需要 Ubuntu 22.04+）"
    exit 1
fi
source /etc/os-release
echo "  操作系统: ${NAME} ${VERSION_ID}"
echo "  架构: ${ARCH}"

# ─── 0.1 安装系统依赖 ───
echo ""
echo "[0.1] 安装系统构建依赖..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    nodejs npm \
    curl wget git \
    dpkg-dev fakeroot \
    build-essential \
    libffi-dev libssl-dev \
    libbz2-dev libreadline-dev libsqlite3-dev \
    libgtk-3-0 libnotify4 libnss3 libxss1 libxtst6 \
    libatspi2.0-0 libuuid1 libdrm2 libgbm1 \
    libasound2

# 检查 Node.js 版本（需要 18+）
NODE_VER=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [[ "$NODE_VER" -lt 18 ]]; then
    echo "Node.js 版本过低 (需要 18+)，正在升级..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

# ─── 0.2 安装 Python 依赖 ───
echo ""
echo "[0.2] 安装 Python 构建依赖..."
cd "${PROJECT_ROOT}/backend"
pip3 install --upgrade pip -q
pip3 install -r requirements.txt -q
pip3 install pyinstaller -q

# ─── 1. 构建前端 ───
echo ""
echo "[1/7] 构建前端 (Vite)..."
cd "${PROJECT_ROOT}/frontend"
npm install --legacy-peer-deps 2>&1 | tail -3
npm run build 2>&1 | tail -5
echo "  前端构建完成"

# ─── 2. 构建后端 ───
echo ""
echo "[2/7] 构建后端 (PyInstaller)..."
cd "${PROJECT_ROOT}/backend"

# 创建 PyInstaller spec
cat > military-rural.spec << 'PYISPEC'
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

added_files = [
    ('data/', 'data/'),
    ('../frontend/dist/', 'frontend/dist/'),
    ('../resources/', 'resources/'),
]

a = Analysis(
    ['start.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'app', 'app.models', 'app.api', 'app.core', 'app.services',
        'sqlalchemy', 'passlib', 'jose', 'bcrypt', 'pydantic',
        'fastapi', 'uvicorn', 'starlette', 'click', 'h11',
        'openpyxl', 'pandas', 'diskcache', 'reportlab',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'scipy', 'matplotlib', 'numpy.core', 'tkinter',
        'PyQt5', 'PySide2', 'IPython', 'jupyter',
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
    name='military-rural-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
PYISPEC

pyinstaller military-rural.spec --clean --noconfirm --distpath dist 2>&1 | tail -5

if [[ ! -f "dist/military-rural-backend" ]]; then
    echo "错误: PyInstaller 构建失败"
    exit 1
fi
echo "  后端构建成功"

# ─── 3. 准备打包目录 ───
echo ""
echo "[3/7] 准备 .deb 打包目录..."

DEB_ROOT="${BUILD_DIR}/deb-root"
rm -rf "${DEB_ROOT}"
mkdir -p "${DEB_ROOT}/DEBIAN"
mkdir -p "${DEB_ROOT}/opt/${APP_NAME}"
mkdir -p "${DEB_ROOT}/opt/${APP_NAME}/backend"
mkdir -p "${DEB_ROOT}/opt/${APP_NAME}/frontend"
mkdir -p "${DEB_ROOT}/opt/${APP_NAME}/data"
mkdir -p "${DEB_ROOT}/opt/${APP_NAME}/logs"
mkdir -p "${DEB_ROOT}/usr/share/applications"
mkdir -p "${DEB_ROOT}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${DEB_ROOT}/etc/${APP_NAME}"

# 复制后端
cp "${PROJECT_ROOT}/backend/dist/military-rural-backend" "${DEB_ROOT}/opt/${APP_NAME}/backend/"
cp -r "${PROJECT_ROOT}/backend/data/"* "${DEB_ROOT}/opt/${APP_NAME}/data/" 2>/dev/null || true

# 复制前端
cp -r "${PROJECT_ROOT}/frontend/dist/"* "${DEB_ROOT}/opt/${APP_NAME}/frontend/"

# 复制资源
if [[ -d "${PROJECT_ROOT}/resources" ]]; then
    cp -r "${PROJECT_ROOT}/resources/"* "${DEB_ROOT}/opt/${APP_NAME}/" 2>/dev/null || true
fi

# 桌面快捷方式
cat > "${DEB_ROOT}/usr/share/applications/${APP_NAME}.desktop" << DESKTOP
[Desktop Entry]
Name=${APP_TITLE}
Name[zh_CN]=${APP_TITLE}
Comment=军队乡村振兴管理系统
Exec=/opt/${APP_NAME}/backend/military-rural-backend
Icon=${APP_NAME}
Terminal=false
Type=Application
Categories=Office;
StartupNotify=true
DESKTOP

# 图标（使用项目内置图标或生成占位符）
if [[ -f "${PROJECT_ROOT}/resources/icons/256x256.png" ]]; then
    cp "${PROJECT_ROOT}/resources/icons/256x256.png" "${DEB_ROOT}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
fi

# ─── 4. 创建 systemd 服务 ───
echo ""
echo "[4/7] 创建 systemd 服务..."
mkdir -p "${DEB_ROOT}/usr/lib/systemd/system"
cat > "${DEB_ROOT}/usr/lib/systemd/system/${APP_NAME}.service" << SERVICED
[Unit]
Description=${APP_TITLE}
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/${APP_NAME}/backend
ExecStart=/opt/${APP_NAME}/backend/military-rural-backend
Restart=on-failure
RestartSec=10
Environment="PORT=8000"
Environment="FRONTEND_DIST_PATH=/opt/${APP_NAME}/frontend"

[Install]
WantedBy=multi-user.target
SERVICED

# ─── 5. 创建安装/卸载脚本 ───
echo ""
echo "[5/7] 创建安装/卸载脚本..."
cat > "${DEB_ROOT}/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e

# 创建数据目录并设置权限
mkdir -p /opt/military-rural-system/data
mkdir -p /opt/military-rural-system/logs
chmod -R 755 /opt/military-rural-system

# 初始化数据库目录
if [[ ! -f /opt/military-rural-system/backend/data/rural_revitalization.db ]]; then
    touch /opt/military-rural-system/backend/data/rural_revitalization.db
fi

# 启用并启动服务
systemctl daemon-reload
systemctl enable military-rural-system 2>/dev/null || true
systemctl start military-rural-system 2>/dev/null || true

echo "============================================"
echo "  军队乡村振兴管理系统 安装完成！"
echo "  访问地址: http://localhost:8000"
echo "  默认账号: admin"
echo "  默认密码: 首次启动时自动生成，查看日志获取"
echo "  查看日志: journalctl -u military-rural-system -f"
echo "============================================"
POSTINST

cat > "${DEB_ROOT}/DEBIAN/prerm" << 'PRERM'
#!/bin/bash
set -e
systemctl stop military-rural-system 2>/dev/null || true
systemctl disable military-rural-system 2>/dev/null || true
PRERM

chmod 755 "${DEB_ROOT}/DEBIAN/postinst"
chmod 755 "${DEB_ROOT}/DEBIAN/prerm"

# ─── 6. 创建 DEBIAN/control ───
echo ""
echo "[6/7] 创建 control 文件..."

DEB_SIZE=$(du -sk "${DEB_ROOT}" | cut -f1)

cat > "${DEB_ROOT}/DEBIAN/control" << CONTROL
Package: ${APP_NAME}
Version: ${VERSION}
Section: office
Priority: optional
Architecture: ${ARCH}
Installed-Size: ${DEB_SIZE}
Maintainer: Military Rural System Team <dev@military-rural.system>
Description: ${APP_TITLE}
 军队乡村振兴管理系统 — 离线单机版桌面应用。
 支持帮扶村管理、项目管理、经费管理、学校管理、
 数据分析、离线地图、多机数据同步等功能。
 .
 运行环境: Linux (x86_64 / ARM64 麒麟V10+)
 技术栈: Python FastAPI + Vue 3 + SQLite + Electron
Depends: libgtk-3-0, libnotify4, libnss3, libxss1, libxtst6, libatspi2.0-0, libuuid1, libgbm1, libasound2, libdrm2
CONTROL

# ─── 7. 构建 .deb 包 ───
echo ""
echo "[7/7] 构建 .deb 安装包..."

mkdir -p "${DIST_DIR}"

DEB_FILENAME="${APP_NAME}_${VERSION}_${ARCH}.deb"
dpkg-deb --build "${DEB_ROOT}" "${DIST_DIR}/${DEB_FILENAME}"

echo ""
echo "=============================================="
echo "  构建完成！"
echo "=============================================="
echo "  安装包: ${DIST_DIR}/${DEB_FILENAME}"
echo "  大小:   $(du -h "${DIST_DIR}/${DEB_FILENAME}" | cut -f1)"
echo ""
echo "  一键安装:"
echo "    sudo dpkg -i ${DIST_DIR}/${DEB_FILENAME}"
echo ""
echo "  安装后自动启动服务，访问 http://localhost:8000"
echo "=============================================="
