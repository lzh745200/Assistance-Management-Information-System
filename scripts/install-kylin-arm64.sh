#!/bin/bash
# ============================================================
# 军队乡村振兴管理系统 - 麒麟V10 ARM64 源码部署脚本
# 适用: 银河麒麟 V10 ARM64
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

VERSION="1.0.4"
APP_NAME="military-rural-system"
INSTALL_DIR="/opt/${APP_NAME}"

log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo -e "${CYAN}==============================================${NC}"
echo -e "${CYAN}  军队乡村振兴管理系统 - 麒麟V10 ARM64 安装${NC}"
echo -e "${CYAN}==============================================${NC}"
echo ""
log_info "版本: ${VERSION}"
log_info "安装目录: ${INSTALL_DIR}"
echo ""

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 root 权限运行此脚本"
    echo "  sudo bash install-kylin-arm64.sh"
    exit 1
fi

# 检查架构
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ] && [ "$ARCH" != "arm64" ]; then
    log_error "此脚本适用于 ARM64 架构，当前架构: $ARCH"
    exit 1
fi
log_success "检测到 ARM64 架构"

# 创建用户和组
log_info "创建系统用户..."
if ! getent group ${APP_NAME} > /dev/null 2>&1; then
    groupadd --system ${APP_NAME}
fi
if ! getent passwd ${APP_NAME} > /dev/null 2>&1; then
    useradd --system --gid ${APP_NAME} --home-dir ${INSTALL_DIR} --shell /bin/false --comment "军队乡村振兴管理系统" ${APP_NAME}
fi

# 创建目录
log_info "创建安装目录..."
mkdir -p ${INSTALL_DIR}/{backend,frontend,data,logs,config,uploads,exports,backups}
mkdir -p /var/log/${APP_NAME}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查源码目录
if [ -d "${SCRIPT_DIR}/backend" ] && [ -d "${SCRIPT_DIR}/frontend" ]; then
    SRC_DIR="${SCRIPT_DIR}"
else
    log_error "未找到源码目录"
    log_info "请将安装脚本放在项目根目录"
    exit 1
fi

# 安装系统依赖
log_info "安装系统依赖..."
apt-get update
apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    libmagic1 \
    libmagic-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpq-dev \
    gcc \
    g++ \
    make \
    file \
    upx-ucl \
    || true

# 安装Python依赖
log_info "安装Python依赖..."
cd ${SRC_DIR}/backend

# 创建虚拟环境
python3.12 -m venv ${INSTALL_DIR}/venv

# 激活虚拟环境安装依赖
${INSTALL_DIR}/venv/bin/pip install --upgrade pip wheel setuptools

${INSTALL_DIR}/venv/bin/pip install \
    fastapi==0.109.2 \
    uvicorn[standard]==0.27.1 \
    starlette==0.36.3 \
    pydantic==2.6.3 \
    pydantic-settings==2.2.1 \
    sqlalchemy==2.0.27 \
    alembic==1.13.1 \
    aiosqlite==0.20.0 \
    python-jose[cryptography]==3.5.0 \
    passlib[bcrypt]==1.7.4 \
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
    pyinstaller==6.3.0 \
    2>&1 | tail -5

# 复制应用
log_info "复制应用文件..."
cp -r ${SRC_DIR}/backend/app ${INSTALL_DIR}/backend/
cp -r ${SRC_DIR}/frontend/dist ${INSTALL_DIR}/frontend/
cp ${SRC_DIR}/backend/.env.example ${INSTALL_DIR}/config/config.env 2>/dev/null || true
cp ${SRC_DIR}/backend/start.py ${INSTALL_DIR}/backend/ 2>/dev/null || true
cp -r ${SRC_DIR}/backend/alembic ${INSTALL_DIR}/backend/ 2>/dev/null || true

# 创建启动脚本
log_info "创建启动脚本..."
cat > /usr/bin/${APP_NAME} << 'STARTEOF'
#!/bin/bash
APP_DIR="/opt/military-rural-system"
VENV_DIR="$APP_DIR/venv"
export PYTHONPATH="$APP_DIR/backend"
export DATABASE_URL="sqlite:///$APP_DIR/data/rural_revitalization.db"
export STATIC_FILES_DIR="$APP_DIR/frontend"
mkdir -p "$APP_DIR/data" "$APP_DIR/logs" "$APP_DIR/data/uploads" "$APP_DIR/data/exports"
cd "$APP_DIR"
exec "$VENV_DIR/bin/python" "$APP_DIR/backend/start.py" "$@"
STARTEOF
chmod 755 /usr/bin/${APP_NAME}

# 创建 systemd 服务
log_info "创建 systemd 服务..."
cat > /lib/systemd/system/${APP_NAME}.service << 'SVCEOF'
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
ExecStart=/opt/military-rural-system/venv/bin/python /opt/military-rural-system/backend/start.py
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
SVCEOF

# 创建桌面文件
log_info "创建桌面文件..."
cat > /usr/share/applications/${APP_NAME}.desktop << 'DTEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=军队乡村振兴管理系统
Name[en]=Military Rural Revitalization System
Comment=军队全面推进乡村振兴工作综合管理平台
Exec=/usr/bin/military-rural-system
Icon=military-rural-system
Terminal=false
Categories=Utility;Office;
Keywords=military;rural;management;
DTEOF

# 设置权限
log_info "设置权限..."
chown -R ${APP_NAME}:${APP_NAME} ${INSTALL_DIR}
chown -R ${APP_NAME}:${APP_NAME} /var/log/${APP_NAME}
chmod +x ${INSTALL_DIR}/backend/start.py 2>/dev/null || true

# 重载 systemd
systemctl daemon-reload
systemctl enable ${APP_NAME}.service

echo ""
echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}  安装完成！${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""
log_success "应用已安装到: ${INSTALL_DIR}"
log_success "启动脚本: /usr/bin/${APP_NAME}"
log_success "系统服务: military-rural-system.service"
echo ""
log_info "启动服务:"
echo "  sudo systemctl start military-rural-system"
echo "  sudo systemctl status military-rural-system"
echo ""
log_info "访问系统:"
echo "  浏览器打开: http://localhost:8000"
echo ""
log_info "默认账号: admin"
log_info "默认密码: Admin@2026（首次登录须修改）"
echo ""
log_info "查看日志:"
echo "  journalctl -u military-rural-system -f"
echo ""
