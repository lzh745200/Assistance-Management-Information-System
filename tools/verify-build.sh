#!/bin/bash
# ========================================
# 军队乡村振兴管理系统 - 构建验证脚本
# ========================================

echo ""
echo "========================================"
echo "构建环境和文件验证"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 验证函数
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (缺失)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ (缺失)"
        return 1
    fi
}

check_command() {
    if command -v "$1" &> /dev/null; then
        version=$($1 --version 2>&1 | head -1)
        echo -e "${GREEN}✓${NC} $1: $version"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (未安装)"
        return 1
    fi
}

# 1. 检查构建工具
echo "[1] 构建工具"
check_command python
check_command node
check_command npm
echo ""

# 2. 检查图标文件
echo "[2] 圆形图标文件"
check_file "resources/icons/app-circle.ico"
check_file "resources/icons/bz-circle.png"
check_dir "resources/icons/circle"
check_file "resources/icons/circle/icon_256x256.png"
echo ""

# 3. 检查构建脚本
echo "[3] 构建脚本"
check_file "build-all-windows.bat"
check_file "build-all-arm64.sh"
check_file "build-all.sh"
check_file "scripts/create_circle_icon.py"
check_file "scripts/军队乡村振兴管理系统.bat"
echo ""

# 4. 检查配置文件
echo "[4] 配置文件"
check_file "build-config.json"
check_file "package.json"
check_file "docker/Dockerfile.arm64-unified"
echo ""

# 5. 检查文档
echo "[5] 文档"
check_file "BUILD.md"
check_file "REBUILD_REPORT.md"
echo ""

# 6. 检查项目结构
echo "[6] 项目结构"
check_dir "backend"
check_dir "frontend"
check_dir "electron"
check_dir "resources"
check_file "backend/military-rural-backend-full.spec"
check_file "electron/main.js"
echo ""

# 7. 检查虚拟环境
echo "[7] Python 虚拟环境"
check_file "backend/.venv/Scripts/activate.bat"
echo ""

# 8. 验证 package.json 配置
echo "[8] package.json 配置验证"
if grep -q "app-circle.ico" package.json; then
    echo -e "${GREEN}✓${NC} Windows 图标路径已更新"
else
    echo -e "${RED}✗${NC} Windows 图标路径未更新"
fi

if grep -q "resources/icons/circle" package.json; then
    echo -e "${GREEN}✓${NC} Linux 图标路径已更新"
else
    echo -e "${RED}✗${NC} Linux 图标路径未更新"
fi

if grep -q "军队乡村振兴管理系统" package.json; then
    echo -e "${GREEN}✓${NC} 产品名称已统一"
else
    echo -e "${RED}✗${NC} 产品名称未统一"
fi
echo ""

# 9. 验证 electron/main.js
echo "[9] electron/main.js 配置验证"
if grep -q "app-circle.ico" electron/main.js; then
    echo -e "${GREEN}✓${NC} Electron 图标路径已更新"
else
    echo -e "${RED}✗${NC} Electron 图标路径未更新"
fi
echo ""

# 10. 显示图标文件大小
echo "[10] 图标文件信息"
if [ -f "resources/icons/app-circle.ico" ]; then
    ls -lh resources/icons/app-circle.ico
fi
if [ -f "resources/icons/bz-circle.png" ]; then
    ls -lh resources/icons/bz-circle.png
fi
if [ -d "resources/icons/circle" ]; then
    echo "多尺寸图标:"
    ls -lh resources/icons/circle/*.png | awk '{print "  " $9 " - " $5}'
fi
echo ""

echo "========================================"
echo "验证完成"
echo "========================================"
echo ""
echo "如果所有检查都通过，可以开始构建:"
echo "  Windows: build-all-windows.bat"
echo "  ARM64:   bash build-all-arm64.sh"
echo "  全部:    bash build-all.sh"
echo ""
