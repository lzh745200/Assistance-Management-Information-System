#!/bin/bash
# ============================================================
# 军队乡村振兴管理系统 - arm64 DEB 本地构建脚本
# 目标: 银河麒麟 V10 arm64
# 特点: 完全本地构建，零外部依赖
#
# ⚠️ 已弃用 - 请使用统一构建脚本:
#   bash scripts/build-kylin-arm64.sh
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

VERSION="${VERSION:-1.0.4}"
ARCH="arm64"
APP_NAME="military-rural-system"
BUILD_DIR="/tmp/deb-build-$$"
OUTPUT_DIR="dist/deb"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo -e "${CYAN}==============================================${NC}"
echo -e "${CYAN}  军队乡村振兴管理系统 - arm64 DEB 构建${NC}"
echo -e "${CYAN}==============================================${NC}"
echo ""
log_info "  版本: ${VERSION}"
log_info "  架构: ${ARCH}"
log_info "  目标: 银河麒麟 V10"
log_info "  构建目录: ${BUILD_DIR}"
echo ""

# 切换到项目目录
cd /mnt/c/military-Rural\ Revitalization-system
PROJECT_ROOT="$(pwd)"

# 清理旧构建
log_info "清理旧构建..."
rm -rf "${PROJECT_ROOT}/${OUTPUT_DIR}"
rm -rf "${PROJECT_ROOT}/backend/dist_arm64"
rm -rf "${PROJECT_ROOT}/frontend/dist"
rm -rf "${BUILD_DIR}"

mkdir -p "${PROJECT_ROOT}/${OUTPUT_DIR}"
mkdir -p "${BUILD_DIR}"

# ============================================================
# 阶段1: 构建前端
# ============================================================
echo ""
log_info "=============================================="
log_info "  阶段1: 构建前端"
log_info "=============================================="

cd "${PROJECT_ROOT}/frontend"

log_info "安装前端依赖..."
npm install --legacy-peer-deps 2>&1 | tail -5

log_info "构建前端..."
npm run build 2>&1 | tail -10

if [ ! -d "dist" ]; then
    log_error "前端构建失败: dist 目录不存在"
    exit 1
fi

log_success "前端构建完成"
ls -la dist/ | head -5

# ============================================================
# 阶段2: 构建后端 (arm64 交叉编译)
# ============================================================
echo ""
log_info "=============================================="
log_info "  阶段2: 构建后端 (arm64 交叉编译)"
log_info "=============================================="

cd "${PROJECT_ROOT}/backend"

# 创建 Python 虚拟环境用于交叉编译
log_info "创建 arm64 交叉编译 Python 环境..."
python3 -m venv "${BUILD_DIR}/venv-arm64"

# 安装基础依赖到虚拟环境
"${BUILD_DIR}/venv-arm64/bin/pip" install --upgrade pip wheel setuptools 2>&1 | tail -3

# 安装 PyInstaller (需要从源码编译)
"${BUILD_DIR}/venv-arm64/bin/pip" install pyinstaller==6.3.0 2>&1 | tail -3

# 安装其他运行时依赖 (不需要编译的)
"${BUILD_DIR}/venv-arm64/bin/pip" install \
    fastapi==0.109.2 \
    uvicorn[standard]==0.27.1 \
    starlette==0.36.3 \
    pydantic==2.6.3 \
    pydantic-settings==2.2.1 \
    sqlalchemy==2.0.27 \
    aiosqlite==0.20.0 \
    bcrypt==4.0.1 \
    passlib[bcrypt]==1.7.4 \
    python-jose[cryptography]==3.5.0 \
    cryptography==42.0.5 \
    pyotp==2.9.0 \
    python-multipart==0.0.9 \
    python-docx==1.1.0 \
    fpdf2==2.8.7 \
    reportlab==4.1.0 \
    python-pptx==1.0.2 \
    mammoth==1.6.0 \
    httpx==0.27.0 \
    email-validator==2.1.1 \
    bleach==6.3.0 \
    pillow==10.4.0 \
    qrcode==7.4.2 \
    jieba==0.42.1 \
    APScheduler==3.10.4 \
    structlog==24.1.0 \
    slowapi==0.1.9 \
    diskcache==5.6.3 \
    prometheus_client==0.24.1 \
    pandas==2.2.1 \
    numpy==1.26.4 \
    openpyxl==3.1.2 \
    XlsxWriter==3.1.9 \
    2>&1 | grep -E "(Successfully|Requirement)" | tail -10

# 创建 arm64 专用的 PyInstaller spec 文件
log_info "创建 arm64 PyInstaller 配置..."

cat > backend_linux_arm64.spec << 'SPECEOF'
# -*- mode: python ; coding: utf-8 -*-
"""arm64 Linux PyInstaller 打包配置"""
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
backend_dir = os.path.dirname(os.path.abspath(SPEC))

datas = [
    (os.path.join(backend_dir, 'alembic'), 'alembic'),
    (os.path.join(backend_dir, 'app'), 'app'),
]

binaries = []

hiddenimports = [
    'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
    'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl', 'uvicorn.lifespan', 'uvicorn.lifespan.on',
    'fastapi', 'fastapi.middleware', 'fastapi.middleware.cors',
    'starlette', 'starlette.middleware', 'starlette.middleware.base',
    'sqlalchemy', 'sqlalchemy.dialects.sqlite',
    'sqlalchemy.orm', 'sqlalchemy.ext.declarative',
    'pydantic', 'pydantic.v1', 'pydantic_settings',
    'passlib', 'passlib.handlers.bcrypt', 'passlib.handlers.sha2_crypt',
    'jose', 'jose.jwt', 'jose.exceptions',
    'cryptography', 'cryptography.fernet', 'cryptography.hazmat',
    'aiosqlite', 'alembic', 'alembic.config',
    'email_validator', 'python_multipart', 'multipart',
    'pandas', 'numpy', 'openpyxl', 'xlsxwriter',
    'docx', 'fpdf', 'reportlab', 'pptx',
    'PIL', 'PIL.Image', 'qrcode', 'jieba',
    'apscheduler', 'structlog', 'slowapi', 'diskcache',
    'bcrypt', 'bleach', 'httpx',
    'app.main', 'app.core.config', 'app.core.database',
    'app.core.security', 'app.api.v1',
]

hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('sqlalchemy')

a = Analysis(
    ['start.py'],
    pathex=[backend_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'sklearn', 'scrapy', 'redis'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='military-rural-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='military-rural-backend',
)
SPECEOF

# 执行 PyInstaller 交叉编译
log_info "执行 PyInstaller 交叉编译 (arm64)..."

# 设置交叉编译环境变量
export CROSS_COMPILE=aarch64-linux-gnu-
export CC=aarch64-linux-gnu-gcc
export CXX=aarch64-linux-gnu-g++
export PYINSTALLER_CONFIG_FILE="${BUILD_DIR}/pyinstaller-arm64.cfg"

# 创建 PyInstaller 配置
cat > "${BUILD_DIR}/pyinstaller-arm64.cfg" << 'PYEOF'
[exe]
CROSS_COMPILE=aarch64-linux-gnu-
PYOF

# 清理可能的旧构建
rm -rf build dist dist_arm64 2>/dev/null || true

# 使用虚拟环境中的 PyInstaller 进行交叉编译
# 需要指定交叉编译的Python
"${BUILD_DIR}/venv-arm64/bin/python" -m PyInstaller \
    backend_linux_arm64.spec \
    --clean \
    --noconfirm \
    --distpath dist_arm64 \
    --workpath /tmp/pyinstaller_work \
    2>&1 | tail -30

if [ ! -d "dist_arm64/military-rural-backend" ]; then
    log_error "后端构建失败"
    exit 1
fi

log_success "后端构建完成"
ls -la dist_arm64/military-rural-backend/ | head -10

# ============================================================
# 阶段3: 组装 DEB 包
# ============================================================
echo ""
log_info "=============================================="
log_info "  阶段3: 组装 DEB 包"
log_info "=============================================="

cd "${PROJECT_ROOT}"

DEB_DIR="${BUILD_DIR}/pkg"
mkdir -p "${DEB_DIR}"/{DEBIAN,etc,lib/systemd/system,usr/{bin,share/applications,share/icons/hicolor/256x256/apps},var/log/${APP_NAME},opt/${APP_NAME}/{backend,frontend,data,logs,config}}

# 复制前端
log_info "复制前端..."
cp -r frontend/dist/* "${DEB_DIR}/opt/${APP_NAME}/frontend/"

# 复制后端
log_info "复制后端..."
cp -r backend/dist_arm64/military-rural-backend/* "${DEB_DIR}/opt/${APP_NAME}/backend/"

# 复制环境配置示例
cp backend/.env.example "${DEB_DIR}/opt/${APP_NAME}/config/config.env.example" 2>/dev/null || true

# 创建启动脚本
log_info "创建启动脚本..."
cat > "${DEB_DIR}/usr/bin/${APP_NAME}" << 'STARTSCRIPT'
#!/bin/bash
APP_DIR="/opt/military-rural-system"
export PYTHONPATH="$APP_DIR/backend"
export DATABASE_URL="sqlite:///$APP_DIR/data/rural_revitalization.db"
export STATIC_FILES_DIR="$APP_DIR/frontend"
mkdir -p "$APP_DIR/data" "$APP_DIR/logs" "$APP_DIR/data/uploads" "$APP_DIR/data/exports" "$APP_DIR/data/backups"
cd "$APP_DIR"
exec "$APP_DIR/backend/military-rural-backend" "$@"
STARTSCRIPT
chmod 755 "${DEB_DIR}/usr/bin/${APP_NAME}"

# 创建 systemd 服务文件
log_info "创建 systemd 服务..."
cat > "${DEB_DIR}/lib/systemd/system/${APP_NAME}.service" << 'SERVICEOF'
[Unit]
Description=军队乡村振兴管理系统
Documentation=file:///opt/military-rural-system/README.md
After=network.target
Wants=network.target

[Service]
Type=simple
User=military-rural
Group=military-rural
WorkingDirectory=/opt/military-rural-system
ExecStart=/opt/military-rural-system/backend/military-rural-backend
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=military-rural-system
Environment=PYTHONUNBUFFERED=1
Environment=ENV=production
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
SERVICEOF

# 创建桌面文件
cat > "${DEB_DIR}/usr/share/applications/${APP_NAME}.desktop" << 'DESKTOPEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=军队乡村振兴管理系统
Name[en]=Military Rural Revitalization System
Comment=军队全面推进乡村振兴工作综合管理平台
Comment[en]=Military Rural Revitalization Management Platform
Exec=/usr/bin/military-rural-system
Icon=military-rural-system
Terminal=false
Categories=Utility;Office;
Keywords=military;rural;management;
DESKTOPEOF

# 创建 DEB control 文件
log_info "创建 DEB 控制文件..."
cat > "${DEB_DIR}/DEBIAN/control" << 'CONTROLEOF'
Package: military-rural-system
Version: VERSION_PLACEHOLDER
Section: utils
Priority: optional
Architecture: arm64
Installed-Size: INSTALL_SIZE_PLACEHOLDER
Maintainer: 军队乡村振兴管理系统开发组 <support@military-rural-system.internal>
Depends: libc6 (>= 2.31), libmagic1, libstdc++6, libgcc-s1, libssl3, libpq5
Recommends: systemd
Homepage: https://military-rural-system.internal
Description: 军队乡村振兴管理系统 vVERSION_PLACEHOLDER
 军队全面推进乡村振兴工作综合管理平台
 .
 主要功能:
  - 帮扶项目管理与进度跟踪
  - 资金使用监控与审计
  - 政策法规知识库管理
  - 组织架构与人员管理
  - GIS 地图可视化展示
  - 数据统计报表生成
  - 离线数据同步与备份
  - 多级权限访问控制
 .
 运行环境: Linux arm64 (银河麒麟 V10)
 访问地址: http://localhost:8000
CONTROLEOF

# 替换版本号和大小
sed -i "s/VERSION_PLACEHOLDER/${VERSION}/g" "${DEB_DIR}/DEBIAN/control"
INSTALL_SIZE=$(du -sk "${DEB_DIR}/opt" 2>/dev/null | awk '{print int($1)}')
sed -i "s/INSTALL_SIZE_PLACEHOLDER/${INSTALL_SIZE}/g" "${DEB_DIR}/DEBIAN/control"

# 创建 postinst
log_info "创建安装后脚本..."
cat > "${DEB_DIR}/DEBIAN/postinst" << 'POSTINSTEOF'
#!/bin/bash
set -e

APP_DIR="/opt/military-rural-system"

# 创建专用用户和组
if ! getent group military-rural > /dev/null 2>&1; then
    groupadd --system military-rural
fi
if ! getent passwd military-rural > /dev/null 2>&1; then
    useradd --system --gid military-rural \
            --home-dir "$APP_DIR" \
            --shell /bin/false \
            --comment "军队乡村振兴管理系统" \
            military-rural
fi

# 创建数据目录
mkdir -p "$APP_DIR/data"
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/data/uploads"
mkdir -p "$APP_DIR/data/exports"
mkdir -p "$APP_DIR/data/backups"
mkdir -p /var/log/military-rural-system

# 设置权限
chown -R military-rural:military-rural "$APP_DIR"
chown -R military-rural:military-rural /var/log/military-rural-system
chmod 755 "$APP_DIR/backend/military-rural-backend"
chmod 644 "$APP_DIR/config/config.env.example" 2>/dev/null || true

# 如果配置文件不存在，从示例创建
if [ ! -f "$APP_DIR/config/config.env" ]; then
    if [ -f "$APP_DIR/config/config.env.example" ]; then
        cp "$APP_DIR/config/config.env.example" "$APP_DIR/config/config.env"
        chown military-rural:military-rural "$APP_DIR/config/config.env"
    fi
fi

# 重载并启用 systemd 服务
if command -v systemctl > /dev/null 2>&1; then
    systemctl daemon-reload
    systemctl enable military-rural-system.service || true
fi

echo ""
echo "================================================"
echo "  军队乡村振兴管理系统 vVERSION_PLACEHOLDER 安装完成！"
echo "================================================"
echo ""
echo "  启动服务:"
echo "    sudo systemctl start military-rural-system"
echo ""
echo "  访问系统:"
echo "    http://localhost:8000"
echo ""
echo "  默认账号: admin"
echo "  默认密码: Admin@2026（首次登录须修改）"
echo ""
echo "  查看日志:"
echo "    journalctl -u military-rural-system -f"
echo ""

exit 0
POSTINSTEOF
sed -i "s/VERSION_PLACEHOLDER/${VERSION}/g" "${DEB_DIR}/DEBIAN/postinst"
chmod 755 "${DEB_DIR}/DEBIAN/postinst"

# 创建 prerm
cat > "${DEB_DIR}/DEBIAN/prerm" << 'PRERMEOF'
#!/bin/bash
set -e

if command -v systemctl > /dev/null 2>&1; then
    if systemctl is-active --quiet military-rural-system; then
        systemctl stop military-rural-system || true
    fi
    if systemctl is-enabled --quiet military-rural-system 2>/dev/null; then
        systemctl disable military-rural-system.service || true
    fi
fi

exit 0
PRERMEOF
chmod 755 "${DEB_DIR}/DEBIAN/prerm"

# 创建 postrm
cat > "${DEB_DIR}/DEBIAN/postrm" << 'POSTRMEOF'
#!/bin/bash
set -e

if [ "$1" = "purge" ]; then
    # 完全卸载：删除数据和用户
    rm -rf /opt/military-rural-system
    rm -rf /var/log/military-rural-system

    if getent passwd military-rural > /dev/null 2>&1; then
        userdel military-rural || true
    fi
    if getent group military-rural > /dev/null 2>&1; then
        groupdel military-rural || true
    fi
fi

if command -v systemctl > /dev/null 2>&1; then
    systemctl daemon-reload || true
fi

exit 0
POSTRMEOF
chmod 755 "${DEB_DIR}/DEBIAN/postrm"

# 创建 conffiles (可选，用于标记配置文件)
# touch "${DEB_DIR}/DEBIAN/conffiles"

# ============================================================
# 阶段4: 打包 DEB
# ============================================================
echo ""
log_info "=============================================="
log_info "  阶段4: 打包 DEB"
log_info "=============================================="

cd "${BUILD_DIR}"

# 设置所有权为 root (用于 dpkg-deb)
fakeroot dpkg-deb --build pkg "dist/deb/${APP_NAME}_${VERSION}_${ARCH}.deb" 2>&1

if [ $? -eq 0 ]; then
    log_success "DEB 打包完成！"
else
    log_error "DEB 打包失败"
    exit 1
fi

# 复制 DEB 到项目目录
cp "dist/deb/${APP_NAME}_${VERSION}_${ARCH}.deb" "${PROJECT_ROOT}/${OUTPUT_DIR}/"

# ============================================================
# 完成
# ============================================================
echo ""
echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}  构建完成！${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""
log_success "DEB 文件: ${PROJECT_ROOT}/${OUTPUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb"
log_info "文件大小: $(du -h "${PROJECT_ROOT}/${OUTPUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb" | awk '{print $1}')"
log_info "SHA256: $(sha256sum "${PROJECT_ROOT}/${OUTPUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb" | awk '{print $1}')"
echo ""
log_info "包信息:"
dpkg-deb -I "${PROJECT_ROOT}/${OUTPUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb" 2>/dev/null | head -15
echo ""
log_info "安装方法:"
echo "  sudo dpkg -i ${OUTPUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb"
echo "  sudo apt-get install -f  # 安装依赖"
echo ""
log_info "启动服务:"
echo "  sudo systemctl start military-rural-system"
echo "  sudo systemctl enable military-rural-system  # 开机自启"
echo ""

# 清理构建目录
rm -rf "${BUILD_DIR}"

log_success "构建流程结束"
