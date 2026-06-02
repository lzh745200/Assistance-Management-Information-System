#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
# 军队乡村振兴管理系统 — aarch64 后端构建脚本
# 在麒麟 V10 aarch64 物理机/虚拟机上执行
#
# 前置条件:
#   - Python 3.11+
#   - pip (python3-pip)
#   - 项目已 clone 到本地
#
# 用法:
#   cd /path/to/military-Rural-Revitalization-system
#   chmod +x scripts/build-backend-aarch64.sh
#   bash scripts/build-backend-aarch64.sh
# ──────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
DIST_DIR="$PROJECT_ROOT/dist/backend/linux-arm64"
SPEC_FILE="$BACKEND_DIR/military-rural-backend.spec"

echo "============================================"
echo " aarch64 后端构建脚本"
echo " 项目根目录: $PROJECT_ROOT"
echo " 目标架构: $(uname -m)"
echo "============================================"

# ─── 1. 架构检查 ───
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" ]]; then
    echo "⚠️  警告: 当前架构为 $ARCH，不是 aarch64/arm64。"
    echo "   PyInstaller 不支持交叉编译，产物可能无法在 aarch64 上运行。"
    read -p "   是否继续? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消。"
        exit 1
    fi
fi

# ─── 2. Python 版本检查 ───
PYTHON_CMD=""
for cmd in python3.11 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [[ "$major" -ge 3 && "$minor" -ge 10 ]]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo "❌ 未找到 Python 3.10+，请安装 Python 3.11"
    echo "   麒麟 V10: sudo apt install python3.11 python3.11-venv python3-pip"
    exit 1
fi

echo "✅ Python: $($PYTHON_CMD --version)"

# ─── 3. 检查 spec 文件 ───
if [[ ! -f "$SPEC_FILE" ]]; then
    echo "❌ PyInstaller spec 文件不存在: $SPEC_FILE"
    exit 1
fi

# ─── 4. 创建/激活虚拟环境 ───
VENV_DIR="$BACKEND_DIR/.venv-arm64"
if [[ ! -d "$VENV_DIR" ]]; then
    echo "📦 创建 Python 虚拟环境..."
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

echo "📦 激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# ─── 5. 安装依赖 ───
echo "📦 安装项目依赖..."
pip install --upgrade pip setuptools wheel
pip install -r "$BACKEND_DIR/requirements.txt"
pip install pyinstaller

echo "✅ PyInstaller: $(pyinstaller --version)"

# ─── 6. 清理旧构建产物 ───
echo "🧹 清理旧构建产物..."
rm -rf "$BACKEND_DIR/dist" "$BACKEND_DIR/build"
mkdir -p "$DIST_DIR"

# ─── 7. PyInstaller 打包 ───
echo "🔨 PyInstaller 打包中..."
cd "$BACKEND_DIR"
pyinstaller --clean --noconfirm "$SPEC_FILE"

# ─── 8. 验证并复制产物 ───
EXE_PATH="$BACKEND_DIR/dist/military-rural-backend"
if [[ ! -f "$EXE_PATH" ]]; then
    echo "❌ 后端可执行文件不存在: $EXE_PATH"
    echo "   请检查 PyInstaller 打包日志。"
    exit 1
fi

SIZE_MB=$(du -m "$EXE_PATH" | cut -f1)
echo "✅ 后端可执行文件大小: ${SIZE_MB}MB"

if [[ "$SIZE_MB" -lt 1 ]]; then
    echo "❌ 后端可执行文件过小 (<1MB)，可能打包失败"
    exit 1
fi

# 验证 ELF 架构
FILE_INFO=$(file "$EXE_PATH")
echo "   文件信息: $FILE_INFO"

cp "$EXE_PATH" "$DIST_DIR/military-rural-backend"
chmod +x "$DIST_DIR/military-rural-backend"

echo ""
echo "============================================"
echo " ✅ aarch64 后端构建完成！"
echo " 产物路径: $DIST_DIR/military-rural-backend"
echo " 文件大小: ${SIZE_MB}MB"
echo ""
echo " 下一步: 在项目根目录运行"
echo "   npm run build:linux-arm64"
echo " 或:"
echo "   npx electron-builder --linux deb --arm64"
echo "============================================"
