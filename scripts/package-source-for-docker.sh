#!/bin/bash
# ============================================================
# 军队乡村振兴管理系统 — 源码打包脚本
#
# 用途: 将源码打包为干净的 .tar.gz，用于传输到另一台
#       安装了 Docker 的 Ubuntu 机器上进行 ARM64 .deb 构建
#
# 产物: dist/military-rural-source-<version>.tar.gz
#
# 执行: bash scripts/package-source-for-docker.sh
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

VERSION=$(node -p "require('./package.json').version" 2>/dev/null || echo "1.1.0")
ARCHIVE_NAME="military-rural-source-${VERSION}.tar.gz"
OUTPUT_DIR="dist"
ARCHIVE_PATH="${OUTPUT_DIR}/${ARCHIVE_NAME}"

echo ""
echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}  军队乡村振兴管理系统 — 源码打包${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""
echo -e "  版本: ${CYAN}${VERSION}${NC}"
echo -e "  目标: ${CYAN}${ARCHIVE_PATH}${NC}"
echo ""

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# ─── 打包（排除构建产物） ───
echo -e "${YELLOW}[1/2] 打包源码...${NC}"

# 使用 git archive 如果可用（最干净），否则使用 tar
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "  使用 git archive（仅跟踪文件）..."
    git archive --format=tar.gz \
        --prefix="military-rural-system/" \
        --output="${ARCHIVE_PATH}" \
        HEAD
    echo -e "${GREEN}[OK] git archive 完成${NC}"
else
    echo "  使用 tar（排除 node_modules/.venv/dist/__pycache__）..."
    tar -czf "${ARCHIVE_PATH}" \
        --exclude='node_modules' \
        --exclude='.venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='.git' \
        --exclude='dist' \
        --exclude='backend/dist' \
        --exclude='backend/build' \
        --exclude='frontend/dist' \
        --exclude='frontend/node_modules' \
        --exclude='**/node_modules' \
        --exclude='**/__pycache__' \
        --exclude='*.tar.gz' \
        --exclude='*.tar' \
        --exclude='*.zip' \
        --exclude='*.exe' \
        --exclude='*.deb' \
        .
    echo -e "${GREEN}[OK] tar 完成${NC}"
fi

# ─── 显示结果 ───
echo ""
echo -e "${YELLOW}[2/2] 验证...${NC}"

if [ -f "$ARCHIVE_PATH" ]; then
    SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
    echo ""
    echo -e "${GREEN}==============================================${NC}"
    echo -e "${GREEN}  打包完成！${NC}"
    echo -e "${GREEN}==============================================${NC}"
    echo ""
    echo -e "  文件: ${CYAN}$(realpath "$ARCHIVE_PATH")${NC}"
    echo -e "  大小: ${CYAN}${SIZE}${NC}"
    echo ""
    echo -e "${YELLOW}───────── 下一步：在 Ubuntu 上构建 ─────────${NC}"
    echo ""
    echo "  1. 将 ${ARCHIVE_NAME} 复制到 Ubuntu 机器"
    echo "     scp ${ARCHIVE_NAME} user@ubuntu-host:~/"
    echo "     或通过 U盘/网络共享 传输"
    echo ""
    echo "  2. 在 Ubuntu 上解压"
    echo "     tar -xzf ${ARCHIVE_NAME}"
    echo "     cd military-rural-system"
    echo ""
    echo "  3. 一键构建 ARM64 .deb"
    echo "     bash scripts/build-ubuntu-deb.sh"
    echo ""
    echo -e "${GREEN}==============================================${NC}"
    echo ""
else
    echo -e "${RED}[错误] 打包失败：产物不存在${NC}"
    exit 1
fi
