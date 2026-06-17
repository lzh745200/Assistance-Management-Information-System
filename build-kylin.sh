#!/bin/bash
# 麒麟 ARM64 构建脚本

echo "=========================================="
echo "  帮扶管理信息系统 - 麒麟 ARM64 构建"
echo "=========================================="

# 清理旧产物
rm -rf output
mkdir -p output

# 构建 Docker 镜像
echo "步骤 1/3: 构建 Docker 镜像..."
docker build -f Dockerfile -t assistance-system:arm64 .

# 导出产物
echo "步骤 2/3: 导出安装包..."
docker build -f Dockerfile --target export -o output .

# 打包
echo "步骤 3/3: 打包安装包..."
cd output
tar -czf ../assistance-system-kylin-arm64-v1.2.0.tar.gz *
cd ..

echo "=========================================="
echo "构建完成！"
echo "产物位置: assistance-system-kylin-arm64-v1.2.0.tar.gz"
echo "=========================================="