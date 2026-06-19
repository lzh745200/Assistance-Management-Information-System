#!/bin/bash
# 帮扶管理信息系统 - 64-bit Python 迁移 (Linux/麒麟)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")/backend"

echo "========================================"
echo "  64-bit Python 迁移脚本"
echo "========================================"
echo ""

PYTHON_BIN=""
for candidate in python3.11 python3.10 python3; do
    if command -v "$candidate" &>/dev/null; then
        ARCH=$("$candidate" -c "import struct; print(struct.calcsize('P')*8)")
        if [ "$ARCH" = "64" ]; then
            PYTHON_BIN="$(command -v "$candidate")"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "[错误] 未找到 64-bit Python，请安装 Python 3.11+"
    exit 1
fi

echo "[1/3] 64-bit Python: $PYTHON_BIN ($("$PYTHON_BIN" --version))"

echo "[2/3] 备份旧虚拟环境..."
if [ -d "$BACKEND_DIR/.venv" ]; then
    rm -rf "$BACKEND_DIR/.venv.bak"
    mv "$BACKEND_DIR/.venv" "$BACKEND_DIR/.venv.bak"
    echo "[OK] 已备份"
fi

echo "[3/3] 创建 64-bit 虚拟环境..."
cd "$BACKEND_DIR"
"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo "[OK]"

echo ""
echo "========================================"
echo "  迁移成功！"
echo "========================================"
