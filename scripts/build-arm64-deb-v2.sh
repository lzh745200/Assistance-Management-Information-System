#!/bin/bash
# ============================================================
# 军队乡村振兴管理系统 - arm64 DEB 本地构建脚本 v2
#
# ⚠️ 已弃用 - 请使用统一构建脚本:
#   bash scripts/build-kylin-arm64.sh
# ============================================================

set -e

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
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo -e "${CYAN}==============================================${NC}"
echo -e "${CYAN}  arm64 DEB 构建 v2${NC}"
echo -e "${CYAN}==============================================${NC}"
echo ""

cd /mnt/c/military-Rural\ Revitalization-system
PROJECT_ROOT="$(pwd)"

# 清理
rm -rf "${PROJECT_ROOT}/${OUTPUT_DIR}" "${PROJECT_ROOT}/backend/dist_arm64" "${PROJECT_ROOT}/frontend/dist" "${BUILD_DIR}"
mkdir -p "${PROJECT_ROOT}/${OUTPUT_DIR}" "${BUILD_DIR}"

# ============================================================
# 阶段1: 前端
# ============================================================
echo ""
log_info "阶段1: 构建前端..."
cd "${PROJECT_ROOT}/frontend"
npm install --legacy-peer-deps 2>&1 | tail -3
npm run build 2>&1 | tail -5
log_success "前端完成"

# ============================================================
# 阶段2: 后端
# ============================================================
echo ""
log_info "阶段2: 构建后端..."

cd "${PROJECT_ROOT}/backend"

# 创建虚拟环境
python3 -m venv "${BUILD_DIR}/venv-arm64"
"${BUILD_DIR}/venv-arm64/bin/pip" install --upgrade pip wheel setuptools 2>&1 | tail -2
"${BUILD_DIR}/venv-arm64/bin/pip" install pyinstaller==6.3.0 2>&1 | tail -2

# 核心依赖 (纯Python + 预编译wheel)
"${BUILD_DIR}/venv-arm64/bin/pip" install \
    fastapi==0.109.2 uvicorn[standard]==0.27.1 starlette==0.36.3 \
    pydantic==2.6.3 pydantic-settings==2.2.1 sqlalchemy==2.0.27 aiosqlite==0.20.0 \
    python-jose[cryptography]==3.5.0 passlib[bcrypt]==1.7.4 cryptography==42.0.5 \
    pyotp==2.9.0 python-multipart==0.0.9 python-docx==1.1.0 \
    fpdf2==2.8.7 reportlab==4.1.0 python-pptx==1.0.2 mammoth==1.6.0 \
    httpx==0.27.0 email-validator==2.1.1 bleach==6.3.0 \
    pillow==10.4.0 qrcode==7.4.2 jieba==0.42.1 \
    APScheduler==3.10.4 structlog==24.1.0 slowapi==0.1.9 diskcache==5.6.3 prometheus_client==0.24.1 \
    pandas==2.2.1 numpy==1.26.4 openpyxl==3.1.2 XlsxWriter==3.1.9 \
    2>&1 | grep -E "(Successfully|ERROR)" | tail -5

# 创建spec文件
cat > backend_linux_arm64.spec << 'SPECEOF'
# -*- mode: python ; coding: utf-8 -*-
import os
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
    'sqlalchemy', 'sqlalchemy.dialects.sqlite', 'sqlalchemy.orm', 'sqlalchemy.ext.declarative',
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
    ['start.py'], pathex=[backend_dir], binaries=binaries, datas=datas,
    hiddenimports=hiddenimports, hookspath=[], hooksconfig={},
    runtime_hooks=[], excludes=['tkinter', 'matplotlib', 'scipy', 'sklearn', 'scrapy', 'redis'],
    win_no_prefer_redirects=False, win_private_assemblies=False,
    cipher=block_cipher, noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='military-rural-backend',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=True)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True,
    upx_exclude=[], name='military-rural-backend')
SPECEOF

# 交叉编译
export CROSS_COMPILE=aarch64-linux-gnu-
export CC=aarch64-linux-gnu-gcc
export CXX=aarch64-linux-gnu-g++

rm -rf build dist dist_arm64 2>/dev/null || true

"${BUILD_DIR}/venv-arm64/bin/python" -m PyInstaller \
    backend_linux_arm64.spec \
    --clean --noconfirm \
    --distpath dist_arm64 \
    --workpath /tmp/pyinstaller_work \
    2>&1 | tail -20

if [ ! -d "dist_arm64/military-rural-backend" ]; then
    log_error "后端构建失败"
    exit 1
fi
log_success "后端完成"

# ============================================================
# 阶段3: 组装DEB
# ============================================================
echo ""
log_info "阶段3: 组装DEB..."

DEB_DIR="${BUILD_DIR}/pkg"
mkdir -p "${DEB_DIR}"/{DEBIAN,lib/systemd/system,usr/{bin,share/applications},var/log/${APP_NAME},opt/${APP_NAME}/{backend,frontend,data,logs,config}}

cp -r frontend/dist/* "${DEB_DIR}/opt/${APP_NAME}/frontend/"
cp -r backend/dist_arm64/military-rural-backend/* "${DEB_DIR}/opt/${APP_NAME}/backend/"
cp backend/.env.example "${DEB_DIR}/opt/${APP_NAME}/config/config.env.example" 2>/dev/null || true

# 启动脚本
printf '#!/bin/bash\nAPP_DIR="/opt/military-rural-system"\nexport PYTHONPATH="$APP_DIR/backend"\nexport DATABASE_URL="sqlite:///$APP_DIR/data/rural_revitalization.db"\nmkdir -p "$APP_DIR/data" "$APP_DIR/logs" "$APP_DIR/data/uploads" "$APP_DIR/data/exports"\ncd "$APP_DIR"\nexec "$APP_DIR/backend/military-rural-backend" "$@"\n' > "${DEB_DIR}/usr/bin/${APP_NAME}"
chmod 755 "${DEB_DIR}/usr/bin/${APP_NAME}"

# systemd服务
cat > "${DEB_DIR}/lib/systemd/system/${APP_NAME}.service" << 'SERVICEOF'
[Unit]
Description=军队乡村振兴管理系统
After=network.target
[Service]
Type=simple
User=military-rural
Group=military-rural
WorkingDirectory=/opt/military-rural-system
ExecStart=/opt/military-rural-system/backend/military-rural-backend
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=military-rural-system
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
SERVICEOF

# 桌面文件
cat > "${DEB_DIR}/usr/share/applications/${APP_NAME}.desktop" << 'DESKTOPEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=军队乡村振兴管理系统
Exec=/usr/bin/military-rural-system
Icon=military-rural-system
Terminal=false
Categories=Utility;Office;
DESKTOPEOF

# control文件
INSTALL_SIZE=$(du -sk "${DEB_DIR}/opt" 2>/dev/null | awk '{print int($1)}')
cat > "${DEB_DIR}/DEBIAN/control" << CONTROLEOF
Package: military-rural-system
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: arm64
Installed-Size: ${INSTALL_SIZE}
Maintainer: 军队乡村振兴管理系统开发组
Depends: libc6 (>= 2.31), libmagic1, libstdc++6, libgcc-s1
Description: 军队乡村振兴管理系统 v${VERSION}
 军队乡村振兴工作综合管理平台
CONTROLEOF

# postinst
cat > "${DEB_DIR}/DEBIAN/postinst" << 'POSTINSTEOF'
#!/bin/bash
set -e
APP_DIR="/opt/military-rural-system"
if ! getent group military-rural > /dev/null 2>&1; then groupadd --system military-rural; fi
if ! getent passwd military-rural > /dev/null 2>&1; then useradd --system --gid military-rural --home-dir "$APP_DIR" --shell /bin/false --comment "军队乡村振兴管理系统" military-rural; fi
mkdir -p "$APP_DIR/data" "$APP_DIR/logs" /var/log/military-rural-system
chown -R military-rural:military-rural "$APP_DIR" /var/log/military-rural-system 2>/dev/null || true
if [ ! -f "$APP_DIR/config/config.env" ] && [ -f "$APP_DIR/config/config.env.example" ]; then
    cp "$APP_DIR/config/config.env.example" "$APP_DIR/config/config.env"
fi
if command -v systemctl > /dev/null 2>&1; then systemctl daemon-reload && systemctl enable military-rural-system.service 2>/dev/null || true; fi
echo "================================================"
echo "  安装完成！"
echo "  启动: sudo systemctl start military-rural-system"
echo "  访问: http://localhost:8000"
echo "================================================"
exit 0
POSTINSTEOF
chmod 755 "${DEB_DIR}/DEBIAN/postinst"

# prerm
cat > "${DEB_DIR}/DEBIAN/prerm" << 'PRERMEOF'
#!/bin/bash
set -e
if command -v systemctl > /dev/null 2>&1; then systemctl stop military-rural-system 2>/dev/null || true; fi
exit 0
PRERMEOF
chmod 755 "${DEB_DIR}/DEBIAN/prerm"

# postrm
cat > "${DEB_DIR}/DEBIAN/postrm" << 'POSTRMEOF'
#!/bin/bash
set -e
if [ "$1" = "purge" ]; then rm -rf /opt/military-rural-system /var/log/military-rural-system; fi
if command -v systemctl > /dev/null 2>&1; then systemctl daemon-reload 2>/dev/null || true; fi
exit 0
POSTRMEOF
chmod 755 "${DEB_DIR}/DEBIAN/postrm"

# ============================================================
# 阶段4: 打包
# ============================================================
echo ""
log_info "阶段4: 打包DEB..."

cd "${BUILD_DIR}"
fakeroot dpkg-deb --build pkg "${PROJECT_ROOT}/${OUTPUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}==============================================${NC}"
    echo -e "${GREEN}  构建完成！${NC}"
    echo -e "${GREEN}==============================================${NC}"
    log_success "文件: ${PROJECT_ROOT}/${OUTPUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb"
    log_info "大小: $(du -h "${PROJECT_ROOT}/${OUTPUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb" | awk '{print $1}')"
    log_info "SHA256: $(sha256sum "${PROJECT_ROOT}/${OUTPUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb" | awk '{print $1}')"
    echo ""
    log_info "安装:"
    echo "  sudo dpkg -i ${OUTPUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb"
    echo "  sudo apt-get install -f"
    echo "  sudo systemctl start ${APP_NAME}"
else
    log_error "打包失败"
    exit 1
fi

rm -rf "${BUILD_DIR}"
