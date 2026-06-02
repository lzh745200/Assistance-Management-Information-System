#!/bin/bash
# ============================================================
# 军队乡村振兴管理系统 - Docker 跨架构构建脚本
# 在 Windows 上运行，构建麒麟 V10 aarch64 DEB 安装包
#
# ⚠️ 已弃用 - 请在 ARM64 设备上使用原生构建:
#   bash scripts/build-kylin-arm64.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
DOCKERFILE="$PROJECT_ROOT/Dockerfile.kylin-arm64"
IMAGE_NAME="military-rural-build-arm64"
CONTAINER_NAME="military-rural-build"

echo "============================================"
echo " Docker 跨架构构建 (aarch64)"
echo "============================================"

# 检查 Docker
if ! command -v docker &>/dev/null; then
    echo "❌ 未找到 Docker，请安装 Docker Desktop"
    exit 1
fi

# 检查 buildx 支持
if ! docker buildx inspect &>/dev/null | grep -q "linux/arm64"; then
    echo "⚠️  Docker 不支持 linux/arm64 平台"
    echo "   请确保 Docker Desktop 已启用 containerd/RunLinuxContainer"
    exit 1
fi

# 检查项目文件
if [ ! -f "$DOCKERFILE" ]; then
    echo "❌ 未找到 Dockerfile: $DOCKERFILE"
    exit 1
fi

echo "✅ Docker 已就绪"
echo "✅ 支持 linux/arm64 平台"

# 创建临时目录排除 node_modules
TEMP_BUILD_DIR="$PROJECT_ROOT/.build-temp"
rm -rf "$TEMP_BUILD_DIR"
mkdir -p "$TEMP_BUILD_DIR"

echo "📦 复制项目文件..."

# 复制必要文件
rsync -a --exclude='node_modules' --exclude='.git' \
    --exclude='backend/dist' --exclude='backend/build' \
    --exclude='frontend/dist' --exclude='dist' \
    --exclude='.build-temp' \
    "$PROJECT_ROOT/" "$TEMP_BUILD_DIR/"

# 复制 node_modules (可能需要)
if [ -d "$PROJECT_ROOT/node_modules" ]; then
    cp -r "$PROJECT_ROOT/node_modules" "$TEMP_BUILD_DIR/"
fi

# 复制前端 node_modules
if [ -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    cp -r "$PROJECT_ROOT/frontend/node_modules" "$TEMP_BUILD_DIR/frontend/"
fi

cd "$TEMP_BUILD_DIR"

echo "🐳 构建 Docker 镜像..."

# 构建镜像
docker buildx build \
    --platform linux/arm64 \
    --tag "$IMAGE_NAME:latest" \
    -f "$DOCKERFILE" \
    --load \
    .

if [ $? -ne 0 ]; then
    echo "❌ Docker 镜像构建失败"
    exit 1
fi

echo "✅ Docker 镜像构建完成"

# 清理旧容器
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

echo "🚀 在 Docker 容器中构建..."

# 运行构建
docker run --rm \
    --platform=linux/arm64 \
    --name "$CONTAINER_NAME" \
    --privileged \
    -v "$TEMP_BUILD_DIR:/build" \
    -w /build \
    "$IMAGE_NAME:latest"

# 检查产物
echo ""
echo "============================================"
echo " 构建结果"
echo "============================================"

if [ -d "$TEMP_BUILD_DIR/dist/electron" ]; then
    ls -lh "$TEMP_BUILD_DIR/dist/electron/"*.deb 2>/dev/null || true
    ls -lh "$TEMP_BUILD_DIR/dist/electron/"*.AppImage 2>/dev/null || true
    
    # 复制产物到原项目目录
    cp -r "$TEMP_BUILD_DIR/dist/electron/" "$PROJECT_ROOT/dist/"
    echo ""
    echo "✅ 产物已复制到: $PROJECT_ROOT/dist/electron/"
else
    echo "⚠️  未找到构建产物"
    echo "   请检查 Docker 容器日志"
fi

# 清理临时目录
rm -rf "$TEMP_BUILD_DIR"

echo ""
echo "============================================"
echo " ✅ 构建完成！"
echo "============================================"
