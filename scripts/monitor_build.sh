#!/bin/bash
# 监控PyInstaller构建进度

echo "正在监控PyInstaller构建进度..."
echo "构建日志: C:\military-Rural Revitalization-system\pyinstaller-build.log"
echo ""

LOG_FILE="C:\military-Rural Revitalization-system\pyinstaller-build.log"
BACKEND_EXE="C:\military-Rural Revitalization-system\backend\dist\military-rural-backend.exe"

while true; do
    if [ -f "$BACKEND_EXE" ]; then
        SIZE=$(stat -c%s "$BACKEND_EXE" 2>/dev/null || echo "0")
        SIZE_MB=$((SIZE / 1024 / 1024))
        echo "[$(date '+%H:%M:%S')] ✓ 构建完成！文件大小: ${SIZE_MB}MB"
        break
    fi

    if [ -f "$LOG_FILE" ]; then
        LINES=$(wc -l < "$LOG_FILE" 2>/dev/null || echo "0")
        LAST_LINE=$(tail -1 "$LOG_FILE" 2>/dev/null || echo "")
        echo "[$(date '+%H:%M:%S')] 构建中... (日志行数: $LINES)"
        if [ ! -z "$LAST_LINE" ]; then
            echo "  最新: $LAST_LINE"
        fi
    else
        echo "[$(date '+%H:%M:%S')] 等待构建开始..."
    fi

    sleep 10
done

echo ""
echo "构建完成！下一步："
echo "1. 测试新构建的后端"
echo "2. 更新安装包"
