#!/bin/bash
# ============================================================
#  军队乡村振兴管理系统 - 源码打包脚本（Windows → Ubuntu）
#
#  用途: 从 Windows 物理机打包完整源码，传输到 Ubuntu 后
#        使用 Docker 构建麒麟 V10 ARM64 .deb 安装包
#
#  在 Windows Git Bash / MSYS2 中执行:
#    bash scripts/package-for-ubuntu.sh
# ============================================================
set -euo pipefail

# ─── 颜色 ───
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

VERSION=$(node -p "require('./package.json').version" 2>/dev/null || echo "1.1.0")
ARCHIVE_NAME="mrrms-src-${VERSION}.tar.gz"

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  军队乡村振兴管理系统${NC}"
echo -e "${GREEN}  源码打包 for Ubuntu Docker 构建${NC}"
echo -e "${GREEN}  版本: ${VERSION}${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""

# ══════════════════════════════════════════════════════
# [1/3] 清理构建产物和临时文件
# ══════════════════════════════════════════════════════
echo -e "${YELLOW}[1/3] 清理临时文件...${NC}"

# 清理 Python 缓存
find backend/app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find backend/app -name "*.pyc" -delete 2>/dev/null || true

# 清理测试数据库（不含初始数据）
rm -f backend/data/test_integration.db* 2>/dev/null || true
rm -f backend/data/token_blacklist.db 2>/dev/null || true
rm -rf backend/data/cache/* 2>/dev/null || true
rm -rf backend/data/checkpoints/* 2>/dev/null || true

# 清理构建产物（源码不需要这些）
rm -rf backend/dist backend/build 2>/dev/null || true
rm -rf dist/electron/linux-unpacked dist/electron/win-unpacked 2>/dev/null || true
rm -rf frontend/node_modules 2>/dev/null || true
rm -rf node_modules 2>/dev/null || true

echo -e "${GREEN}[OK] 清理完成${NC}"

# ══════════════════════════════════════════════════════
# [2/3] 打包源码（排除不需要的文件）
# ══════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[2/3] 打包源码...${NC}"

# 先写到临时目录避免 "file changed as we read it"
TMP_ARCHIVE="$(cd "$ROOT" && cd .. && pwd)/${ARCHIVE_NAME}"
tar czf "$TMP_ARCHIVE" \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='.git' \
    --exclude='.idea' \
    --exclude='.vscode' \
    --exclude='*.log' \
    --exclude='dist' \
    --exclude='backend/dist' \
    --exclude='backend/build' \
    --exclude='backend/data/test_*.db*' \
    --exclude='backend/data/token_blacklist.db' \
    --exclude='backend/data/cache' \
    --exclude='backend/data/checkpoints' \
    --exclude='*.db-shm' \
    --exclude='*.db-wal' \
    --exclude='.env' \
    --exclude='.DS_Store' \
    --exclude='mrrms-src-*.tar.gz' \
    --exclude='*.exe' \
    --exclude='*.deb' \
    .
mv "$TMP_ARCHIVE" "$ROOT/${ARCHIVE_NAME}"

ARCHIVE_SIZE=$(du -sh "$ARCHIVE_NAME" | cut -f1)
echo -e "${GREEN}[OK] 打包完成: ${CYAN}${ARCHIVE_NAME}${NC} (${ARCHIVE_SIZE})${NC}"

# ══════════════════════════════════════════════════════
# [3/3] 输出传输指南
# ══════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  打包完成！${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  文件: ${CYAN}${ARCHIVE_NAME}${NC}"
echo -e "  大小: ${CYAN}${ARCHIVE_SIZE}${NC}"
echo -e "  路径: ${CYAN}$(pwd)/${ARCHIVE_NAME}${NC}"
echo ""
echo -e "${YELLOW}───────── 传输到 Ubuntu ─────────${NC}"
echo ""
echo "  方法1 - SCP（推荐）:"
echo "    scp ${ARCHIVE_NAME} user@<Ubuntu-IP>:~/"
echo ""
echo "  方法2 - U盘:"
echo "    将 ${ARCHIVE_NAME} 复制到U盘，插入Ubuntu电脑"
echo ""
echo "  方法3 - 共享文件夹（VMware）:"
echo "    放到共享文件夹，Ubuntu 中从 /mnt/hgfs/ 复制"
echo ""
echo -e "${YELLOW}───────── Ubuntu 端操作 ─────────${NC}"
echo ""
echo "  # 1. 解压"
echo "  tar -xzf ${ARCHIVE_NAME}"
echo "  cd mrrms-src  # 或解压到的目录"
echo ""
echo "  # 2. 一键构建（需要先安装 Docker + QEMU）"
echo "  bash scripts/build-ubuntu-deb.sh"
echo ""
