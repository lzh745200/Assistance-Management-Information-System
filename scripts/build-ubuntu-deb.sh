#!/bin/bash
# ============================================================
#  军队乡村振兴管理系统 - Ubuntu Docker 一键构建脚本
#
#  用途: 在 Ubuntu (x86_64) 上通过 Docker buildx 交叉编译
#        生成麒麟 V10 ARM64 .deb 安装包
#
#  前置条件:
#    - Ubuntu 22.04+
#    - Docker 已安装
#    - QEMU 已安装（x86_64 交叉编译 ARM64 必需）
#    - 至少 10GB 可用磁盘空间
#
#  执行:
#    bash scripts/build-ubuntu-deb.sh
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

BUILD_START=$(date +%s)

# ══════════════════════════════════════════════════════
# [1/7] 环境预检
# ══════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  军队乡村振兴管理系统${NC}"
echo -e "${GREEN}  Ubuntu Docker 构建麒麟 V10 ARM64 .deb${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}[1/7] 环境预检...${NC}"

# 检查是否在正确的目录
if [ ! -f "package.json" ] || [ ! -f "docker/Dockerfile.kylin-arm64" ]; then
    echo -e "${RED}[错误] 未找到项目源码，请确认在正确的目录执行${NC}"
    echo "  需要: package.json 和 docker/Dockerfile.kylin-arm64"
    exit 1
fi

VERSION=$(node -p "require('./package.json').version" 2>/dev/null || echo "1.1.0")
echo "  项目版本: $VERSION"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[错误] Docker 未安装${NC}"
    echo ""
    echo "  安装 Docker:"
    echo "    sudo apt update"
    echo "    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin"
    echo "    sudo usermod -aG docker \$USER"
    echo "    newgrp docker"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}[错误] Docker 未运行，或当前用户无权限${NC}"
    echo ""
    echo "  解决:"
    echo "    sudo systemctl start docker"
    echo "    sudo usermod -aG docker \$USER && newgrp docker"
    exit 1
fi

DOCKER_VER=$(docker --version | awk '{print $3}' | tr -d ',')
echo "  Docker: $DOCKER_VER"

# 检查磁盘空间
AVAIL_GB=$(df -BG . | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "${AVAIL_GB:-0}" -lt 10 ]; then
    echo -e "${RED}[警告] 可用磁盘空间不足 ${AVAIL_GB}GB（建议至少 10GB）${NC}"
    echo "  清理: docker system prune -a"
fi
echo "  可用磁盘: ${AVAIL_GB}GB"

echo -e "${GREEN}[OK] 环境预检通过${NC}"

# ══════════════════════════════════════════════════════
# [2/7] 安装 QEMU（x86_64 交叉编译 ARM64 必需）
# ══════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[2/7] 检查 QEMU 模拟器...${NC}"

if docker run --rm --platform linux/arm64 arm64v8/alpine uname -m 2>/dev/null | grep -q aarch64; then
    echo -e "${GREEN}[OK] QEMU 已就绪，ARM64 模拟正常${NC}"
else
    echo "  QEMU 未安装，正在安装..."

    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq qemu-user-static binfmt-support
    else
        echo -e "${RED}[错误] 无法自动安装 QEMU，请手动安装${NC}"
        exit 1
    fi

    # 注册 QEMU 到 binfmt_misc
    docker run --rm --privileged multiarch/qemu-user-static --reset -p yes || {
        echo -e "${RED}[错误] QEMU 注册失败${NC}"
        exit 1
    }

    # 再次验证
    if docker run --rm --platform linux/arm64 arm64v8/alpine uname -m 2>/dev/null | grep -q aarch64; then
        echo -e "${GREEN}[OK] QEMU 安装完成，ARM64 模拟正常${NC}"
    else
        echo -e "${RED}[错误] QEMU 安装后验证失败${NC}"
        exit 1
    fi
fi

# ══════════════════════════════════════════════════════
# [3/7] 配置 Docker buildx
# ══════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[3/7] 配置 Docker buildx...${NC}"

docker buildx create --name mrrms-builder --use 2>/dev/null || \
    docker buildx use mrrms-builder 2>/dev/null || true

docker buildx inspect --bootstrap 2>/dev/null || true

# 验证 buildx 支持 ARM64
if docker buildx ls 2>/dev/null | grep -q "linux/arm64"; then
    echo -e "${GREEN}[OK] buildx 支持 linux/arm64${NC}"
else
    echo -e "${YELLOW}[警告] buildx 未显示 arm64 支持，构建可能失败${NC}"
fi

# ══════════════════════════════════════════════════════
# [4/7] 检查源码完整性
# ══════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[4/7] 检查源码完整性...${NC}"

REQUIRED_FILES=(
    "package.json"
    "package-lock.json"
    "frontend/package.json"
    "frontend/package-lock.json"
    "backend/requirements.txt"
    "backend/military-rural-backend.spec"
    "backend/start.py"
    "docker/Dockerfile.kylin-arm64"
    "scripts/build/build-kylin-arm64-full.sh"
    "build/linux/after-install.sh"
    "electron/main.js"
)

MISSING=0
for f in "${REQUIRED_FILES[@]}"; do
    if [ -f "$f" ]; then
        echo -e "  ${GREEN}✓${NC} $f"
    else
        echo -e "  ${RED}✗${NC} $f  (缺失!)"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo -e "${RED}[错误] 缺少 $MISSING 个关键文件${NC}"
    echo "  请确认源码打包和传输是否完整"
    exit 1
fi

# 检查后端数据目录
if [ ! -f "backend/data/rural_revitalization.db" ]; then
    echo -e "${YELLOW}[提示] 未找到初始数据库，将创建空数据库${NC}"
    mkdir -p backend/data
    touch backend/data/rural_revitalization.db
fi

echo -e "${GREEN}[OK] 源码完整${NC}"

# ══════════════════════════════════════════════════════
# [5/7] Docker 构建 ARM64 镜像
# ══════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[5/7] Docker 构建 ARM64 镜像（预计 30-60 分钟）...${NC}"
echo ""
echo "  构建步骤:"
echo "    1. 安装系统依赖 (Python, GTK, NSS 等)"
echo "    2. 安装 npm 依赖 (前端 + Electron)"
echo "    3. 安装 pip 依赖 (后端 Python 包)"
echo "    4. Vite 构建前端"
echo "    5. PyInstaller 打包后端"
echo "    6. 收集离线系统依赖"
echo "    7. electron-builder 打包 DEB"
echo ""

IMAGE_TAG="military-rural:kylin-arm64-${VERSION}"

docker buildx build \
    --platform linux/arm64 \
    -f docker/Dockerfile.kylin-arm64 \
    -t "$IMAGE_TAG" \
    --load \
    . || {
        echo ""
        echo -e "${RED}══════════════════════════════════════════════════${NC}"
        echo -e "${RED}  构建失败！${NC}"
        echo -e "${RED}══════════════════════════════════════════════════${NC}"
        echo ""
        echo "  常见排障:"
        echo "    1. QEMU 问题: docker run --rm --privileged multiarch/qemu-user-static --reset -p yes"
        echo "    2. 磁盘不足: docker system prune -a && df -h"
        echo "    3. 网络超时: 配置 npm/pip 镜像（见下方）"
        echo "    4. 内存不足: 给虚拟机分配更多内存（建议 8GB+）"
        echo ""
        echo "  配置镜像加速:"
        echo "    npm config set registry https://registry.npmmirror.com"
        echo "    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple"
        echo ""
        exit 1
    }

echo -e "${GREEN}[OK] Docker 镜像构建完成${NC}"

# ══════════════════════════════════════════════════════
# [6/7] 提取 .deb 安装包
# ══════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[6/7] 提取 .deb 安装包...${NC}"

OUTPUT_DIR="$ROOT/dist/electron"
mkdir -p "$OUTPUT_DIR"

# 创建临时容器提取产物
CONTAINER_ID=$(docker create "$IMAGE_TAG")

# 列出容器内的产物
echo "  容器内构建产物:"
docker run --rm "$IMAGE_TAG" ls -lh /project/dist/electron/ 2>/dev/null | grep '\.deb' || true

# 复制所有 .deb 文件
docker cp "${CONTAINER_ID}:/project/dist/electron/." "$OUTPUT_DIR/" 2>/dev/null || {
    echo -e "${RED}[错误] 从容器提取 DEB 失败${NC}"
    docker rm "$CONTAINER_ID" >/dev/null 2>&1 || true
    exit 1
}

docker rm "$CONTAINER_ID" >/dev/null 2>&1 || true

echo -e "${GREEN}[OK] 提取完成${NC}"

# ══════════════════════════════════════════════════════
# [7/7] 验证输出
# ══════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[7/7] 验证 .deb 安装包...${NC}"

BUILD_END=$(date +%s)
ELAPSED=$(( (BUILD_END - BUILD_START) / 60 ))

FOUND=0
for deb in "$OUTPUT_DIR"/*.deb; do
    if [ -f "$deb" ]; then
        DEB_SIZE=$(du -sh "$deb" | cut -f1)
        DEB_NAME=$(basename "$deb")
        FOUND=$((FOUND + 1))

        echo ""
        echo -e "  ${GREEN}━━━ ${DEB_NAME} ━━━${NC}"
        echo -e "  大小: ${CYAN}${DEB_SIZE}${NC}"
        echo -e "  路径: ${CYAN}$(realpath "$deb")${NC}"

        # 显示包信息
        if command -v dpkg-deb &> /dev/null; then
            echo ""
            dpkg-deb --info "$deb" 2>/dev/null | grep -E "Package|Version|Architecture|Installed-Size|Depends" | \
                sed 's/^/    /' || true
        fi
    fi
done

if [ $FOUND -eq 0 ]; then
    echo -e "${RED}[错误] 未找到 .deb 产物${NC}"
    ls -la "$OUTPUT_DIR/" 2>/dev/null || echo "  (目录不存在)"
    exit 1
fi

# ══════════════════════════════════════════════════════
# 输出结果
# ══════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ 构建成功！${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  版本:     ${CYAN}${VERSION}${NC}"
echo -e "  架构:     ${CYAN}arm64 (aarch64)${NC}"
echo -e "  耗时:     ${CYAN}${ELAPSED} 分钟${NC}"
echo -e "  产物:     ${CYAN}${FOUND} 个 .deb 文件${NC}"
echo -e "  输出目录: ${CYAN}${OUTPUT_DIR}${NC}"
echo ""
echo -e "${YELLOW}───────── 在麒麟 V10 ARM64 上安装 ─────────${NC}"
echo ""
echo "  # 将 .deb 文件复制到麒麟 V10 电脑后执行:"
echo "  sudo dpkg -i ${OUTPUT_DIR}/*.deb"
echo "  sudo apt-get install -f -y   # 如需修复依赖"
echo ""
echo -e "${YELLOW}───────── 默认登录 ─────────${NC}"
echo ""
echo "  用户名: admin"
echo "  密码:   admin123"
echo "  地址:   http://localhost:8000"
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""

exit 0
