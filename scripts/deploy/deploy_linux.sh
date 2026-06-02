#!/bin/bash

# 军队乡村振兴管理系统 - Linux 一键部署脚本
# 支持：Ubuntu 20.04+, CentOS 8+, 麒麟 V10

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 部署目录
DEPLOY_DIR="/opt/mrrms"
SERVICE_USER="mrrms"

echo "========================================"
echo "军队乡村振兴管理系统 - 一键部署"
echo "========================================"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误：需要 root 权限运行此脚本${NC}"
    echo "请使用 sudo 运行：sudo bash deploy_linux.sh"
    exit 1
fi

echo -e "${GREEN}[1/12] 检测系统环境...${NC}"
# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
    echo "操作系统：$OS $VER"
else
    echo -e "${RED}错误：无法检测操作系统${NC}"
    exit 1
fi

# 检测架构
ARCH=$(uname -m)
echo "系统架构：$ARCH"
echo ""

echo -e "${GREEN}[2/12] 安装系统依赖...${NC}"
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv nodejs npm sqlite3 git curl wget -qq
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    yum install -y python3 python3-pip nodejs npm sqlite git curl wget -q
elif [[ "$OS" == *"Kylin"* ]] || [[ "$OS" == *"麒麟"* ]]; then
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv nodejs npm sqlite3 git curl wget -qq
else
    echo -e "${YELLOW}警告：未识别的操作系统，尝试继续...${NC}"
fi
echo -e "${GREEN}✓ 系统依赖已安装${NC}"
echo ""

echo -e "${GREEN}[3/12] 创建系统用户...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash "$SERVICE_USER"
    echo -e "${GREEN}✓ 用户 $SERVICE_USER 已创建${NC}"
else
    echo -e "${YELLOW}用户 $SERVICE_USER 已存在${NC}"
fi
echo ""

echo -e "${GREEN}[4/12] 创建部署目录...${NC}"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"
echo -e "${GREEN}✓ 部署目录：$DEPLOY_DIR${NC}"
echo ""

echo -e "${GREEN}[5/12] 复制项目文件...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -r "$SCRIPT_DIR/backend" "$DEPLOY_DIR/"
cp -r "$SCRIPT_DIR/frontend" "$DEPLOY_DIR/"
cp -r "$SCRIPT_DIR/electron" "$DEPLOY_DIR/"
cp "$SCRIPT_DIR/package.json" "$DEPLOY_DIR/"
echo -e "${GREEN}✓ 项目文件已复制${NC}"
echo ""

echo -e "${GREEN}[6/12] 安装后端依赖...${NC}"
cd "$DEPLOY_DIR/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓ 后端依赖已安装${NC}"
echo ""

echo -e "${GREEN}[7/12] 初始化数据库...${NC}"
mkdir -p data
python3 -c "from app.core.database import init_db; init_db()" || echo -e "${YELLOW}警告：数据库初始化失败${NC}"
echo -e "${GREEN}✓ 数据库已初始化${NC}"
echo ""

echo -e "${GREEN}[8/12] 创建默认管理员账户...${NC}"
python3 << 'PYEOF'
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
if not admin:
    admin = User(
        username='admin',
        password=get_password_hash('admin123456'),
        full_name='系统管理员',
        role='admin',
        is_active=True
    )
    db.add(admin)
    db.commit()
    print('管理员账户已创建')
else:
    print('管理员账户已存在')
PYEOF
echo -e "${GREEN}✓ 默认管理员账户：admin / admin123456${NC}"
echo ""

echo -e "${GREEN}[9/12] 安装前端依赖...${NC}"
cd "$DEPLOY_DIR/frontend"
npm install --production
echo -e "${GREEN}✓ 前端依赖已安装${NC}"
echo ""

echo -e "${GREEN}[10/12] 构建前端...${NC}"
npm run build
echo -e "${GREEN}✓ 前端已构建${NC}"
echo ""

echo -e "${GREEN}[11/12] 配置系统服务...${NC}"
# 创建后端服务
cat > /etc/systemd/system/mrrms-backend.service << EOF
[Unit]
Description=军队乡村振兴管理系统 - 后端服务
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$DEPLOY_DIR/backend
Environment="PATH=$DEPLOY_DIR/backend/.venv/bin"
ExecStart=$DEPLOY_DIR/backend/.venv/bin/python start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 创建前端服务（使用 nginx 或 serve）
cat > /etc/systemd/system/mrrms-frontend.service << EOF
[Unit]
Description=军队乡村振兴管理系统 - 前端服务
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$DEPLOY_DIR/frontend
ExecStart=/usr/bin/npx serve -s dist -l 5173
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 设置权限
chown -R "$SERVICE_USER:$SERVICE_USER" "$DEPLOY_DIR"
chmod -R 755 "$DEPLOY_DIR"

# 重新加载 systemd
systemctl daemon-reload
echo -e "${GREEN}✓ 系统服务已配置${NC}"
echo ""

echo -e "${GREEN}[12/12] 启动服务...${NC}"
systemctl enable mrrms-backend
systemctl enable mrrms-frontend
systemctl start mrrms-backend
systemctl start mrrms-frontend

# 等待服务启动
sleep 5

# 检查服务状态
if systemctl is-active --quiet mrrms-backend; then
    echo -e "${GREEN}✓ 后端服务已启动${NC}"
else
    echo -e "${RED}✗ 后端服务启动失败${NC}"
    systemctl status mrrms-backend --no-pager
fi

if systemctl is-active --quiet mrrms-frontend; then
    echo -e "${GREEN}✓ 前端服务已启动${NC}"
else
    echo -e "${RED}✗ 前端服务启动失败${NC}"
    systemctl status mrrms-frontend --no-pager
fi
echo ""

echo "========================================"
echo -e "${GREEN}部署完成！${NC}"
echo "========================================"
echo ""
echo "部署信息："
echo "- 安装目录：$DEPLOY_DIR"
echo "- 服务用户：$SERVICE_USER"
echo "- 默认账户：admin / admin123456"
echo "- 后端地址：http://localhost:8000"
echo "- 前端地址：http://localhost:5173"
echo ""
echo "服务管理命令："
echo "- 查看状态：systemctl status mrrms-backend mrrms-frontend"
echo "- 启动服务：systemctl start mrrms-backend mrrms-frontend"
echo "- 停止服务：systemctl stop mrrms-backend mrrms-frontend"
echo "- 重启服务：systemctl restart mrrms-backend mrrms-frontend"
echo "- 查看日志：journalctl -u mrrms-backend -f"
echo ""
echo "访问系统："
echo "- 在浏览器中打开：http://$(hostname -I | awk '{print $1}'):5173"
echo ""
