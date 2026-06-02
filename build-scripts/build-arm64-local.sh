#!/bin/bash
# ========================================
# 军队乡村振兴管理系统 - ARM64 本地构建（不使用 buildx）
# 版本: 1.0.4
#
# ⚠️ 已弃用 - 请使用统一构建脚本:
#   bash scripts/build-kylin-arm64.sh
# ========================================

set -e

echo ""
echo "========================================"
echo "军队乡村振兴管理系统 - ARM64 本地构建"
echo "版本: 1.0.4"
echo "========================================"
echo ""

# 检查 Docker
echo "[检查] 验证 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "[错误] 未找到 Docker"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "[错误] Docker 未运行"
    exit 1
fi

echo "[✓] Docker 环境检查通过"
echo ""

# 清理旧构建
echo "[1/4] 清理旧构建文件..."
rm -rf dist/linux
mkdir -p dist/linux
echo "[✓] 清理完成"
echo ""

# 使用标准 docker build（不使用 buildx）
echo "[2/4] 构建 Docker 镜像..."
echo "[构建] 使用标准 docker build..."
echo ""

docker build \
    -f docker/Dockerfile.arm64-unified \
    -t military-rural-builder:local \
    .

if [ $? -ne 0 ]; then
    echo "[错误] Docker 构建失败"
    exit 1
fi

echo "[✓] Docker 镜像构建完成"
echo ""

# 提取 DEB 包
echo "[3/4] 提取 DEB 包..."
CONTAINER_ID=$(docker create military-rural-builder:local)
echo "[容器] ID: $CONTAINER_ID"

docker cp "$CONTAINER_ID:/build/military-rural-system_1.0.4_arm64.deb" dist/linux/
if [ $? -ne 0 ]; then
    echo "[错误] 提取 DEB 包失败"
    docker rm "$CONTAINER_ID"
    exit 1
fi

docker cp "$CONTAINER_ID:/build/military-rural-system_1.0.4_arm64.deb.sha256" dist/linux/ 2>/dev/null || true

docker rm "$CONTAINER_ID" > /dev/null
echo "[✓] DEB 包提取完成"
echo ""

# 显示构建结果
echo "[4/4] 构建完成！"
echo ""
echo "========================================"
echo "构建结果"
echo "========================================"
echo ""

if [ -f "dist/linux/military-rural-system_1.0.4_arm64.deb" ]; then
    echo "[DEB 包]"
    ls -lh dist/linux/*.deb
    echo ""

    if [ -f "dist/linux/military-rural-system_1.0.4_arm64.deb.sha256" ]; then
        echo "[SHA256 校验]"
        cat dist/linux/military-rural-system_1.0.4_arm64.deb.sha256
        echo ""
    fi

    echo "[包信息]"
    dpkg-deb -I dist/linux/military-rural-system_1.0.4_arm64.deb 2>/dev/null || echo "  (需要在 Linux 系统上查看详细信息)"
    echo ""
else
    echo "[警告] 未找到生成的 DEB 包"
fi

echo "========================================"
echo "构建流程完成"
echo "========================================"
echo ""
echo "注意: 此构建为当前平台架构，如需 ARM64 架构请在 ARM64 设备上运行"
echo ""
