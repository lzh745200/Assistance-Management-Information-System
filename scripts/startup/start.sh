#!/bin/bash
# 启动脚本 - Linux/Mac
# Feature: startup-optimization
# Requirements: 10.2

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 检测Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[ERROR] Python not found. Please install Python 3.8+"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# 检查Python版本
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

# 运行启动脚本
cd "$PROJECT_ROOT"
$PYTHON_CMD -m scripts.startup.start "$@"
