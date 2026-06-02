#!/bin/bash
# Build backend executable with PyInstaller

set -e

echo "========================================"
echo "军队乡村振兴管理系统 - 后端打包"
echo "========================================"
echo

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
# Detect OS for Python venv path
if [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
    VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"
elif [ -f "$BACKEND_DIR/.venv/Scripts/python.exe" ]; then
    VENV_PYTHON="$BACKEND_DIR/.venv/Scripts/python.exe"
else
    echo "错误: 未找到Python可执行文件"
    echo "请先创建虚拟环境: cd backend && python -m venv .venv"
    exit 1
fi

echo "项目根目录: $PROJECT_ROOT"
echo "后端目录: $BACKEND_DIR"
echo "Python路径: $VENV_PYTHON"
echo

echo "[1/4] 检查并安装依赖..."
cd "$BACKEND_DIR"
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt
"$VENV_PYTHON" -m pip install pyinstaller
echo "[完成] 依赖安装完成"
echo

echo "[2/4] 运行PyInstaller打包后端..."
# Clean previous build
if [ -d "dist/backend/windows" ]; then
    rm -rf "dist/backend/windows"
fi

"$VENV_PYTHON" -m PyInstaller military-rural-backend-full.spec --clean --noconfirm
if [ $? -ne 0 ]; then
    echo "[错误] 后端打包失败"
    exit 1
fi

# Create windows output directory
mkdir -p "dist/backend/windows"

# Copy executable
if [ -f "dist/military-rural-backend.exe" ]; then
    cp "dist/military-rural-backend.exe" "dist/backend/windows/"
    echo "[完成] 后端可执行文件已复制"
fi

if [ -d "dist/military-rural-backend" ]; then
    cp -r "dist/military-rural-backend" "dist/backend/windows/" 2>/dev/null || true
fi

echo "[完成] 后端打包完成"
echo

echo "[3/4] 检查前端构建..."
cd "$PROJECT_ROOT/frontend"
if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
    echo "前端未构建，正在构建..."
    npm run build
    if [ $? -ne 0 ]; then
        echo "[错误] 前端构建失败"
        exit 1
    fi
    echo "[完成] 前端构建完成"
else
    echo "[跳过] 前端已构建"
fi
echo

echo "[4/4] 生成安装包..."
cd "$PROJECT_ROOT"
npm run build:only
if [ $? -ne 0 ]; then
    echo "[错误] Electron打包失败"
    exit 1
fi

echo "[完成] Windows安装包生成完成"
echo

echo "========================================"
echo "打包完成！"
echo "========================================"
echo
echo "输出文件位置:"
ls -la "$PROJECT_ROOT/dist/electron/"*.exe 2>/dev/null || echo "未找到安装包"
echo
echo "安装包位于: $PROJECT_ROOT/dist/electron/"
echo

# Show file info
for exe in "$PROJECT_ROOT/dist/electron/"*.exe; do
    if [ -f "$exe" ]; then
        echo "文件名: $(basename "$exe")"
        echo "大小: $(stat -c%s "$exe" 2>/dev/null || echo "unknown") 字节"
        echo "SHA256: $(sha256sum "$exe" 2>/dev/null | cut -d' ' -f1 || echo "unknown")"
        echo
    fi
done

echo "打包流程全部完成！"
echo