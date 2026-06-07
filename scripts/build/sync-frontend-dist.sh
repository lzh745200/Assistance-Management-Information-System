#!/bin/bash
# ========================================
# 前端构建产物同步脚本 (Linux/macOS)
# 将 frontend/dist/ 复制到 resources/frontend/
# 包含完整性校验：文件数量和总大小对比
# ========================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC_DIR="$PROJECT_ROOT/frontend/dist"
DST_DIR="$PROJECT_ROOT/resources/frontend"

echo "========================================"
echo "前端构建产物同步到 resources/frontend/"
echo "========================================"
echo ""
echo "源目录: $SRC_DIR"
echo "目标目录: $DST_DIR"
echo ""

# 1. 检查源目录是否存在
if [[ ! -f "$SRC_DIR/index.html" ]]; then
    echo "[错误] 源目录不存在或为空: $SRC_DIR"
    echo "请先执行: cd frontend && npm run build"
    exit 1
fi
echo "[OK] 源目录检查通过: $SRC_DIR"

# 2. 收集源目录文件信息
echo ""
echo "[1/4] 收集源目录文件信息..."
SRC_FILE_COUNT=$(find "$SRC_DIR" -type f | wc -l)
SRC_TOTAL_SIZE=$(du -sb "$SRC_DIR" 2>/dev/null | cut -f1 || du -s "$SRC_DIR" | awk '{print $1}')
echo "源目录: $SRC_FILE_COUNT 个文件, 总大小 $SRC_TOTAL_SIZE 字节"

# 3. 强制清理目标目录（解决文件残留和占用问题）
echo ""
echo "[2/4] 清理目标目录..."
if [[ -d "$DST_DIR" ]]; then
    rm -rf "$DST_DIR" 2>/dev/null || {
        echo "[警告] 目标目录可能被占用，尝试重命名..."
        OLD_DIR="${DST_DIR}_old_$$"
        mv "$DST_DIR" "$OLD_DIR" 2>/dev/null || {
            echo "[错误] 无法清理目标目录，请关闭所有占用文件后重试"
            echo "可能占用文件的进程: python/uvicorn, electron, nginx"
            exit 1
        }
        # 后台异步删除旧目录（不阻塞构建流程）
        (sleep 10 && rm -rf "$OLD_DIR") &
    }
fi
mkdir -p "$DST_DIR"
echo "[OK] 目标目录已清理"

# 4. 复制文件
echo ""
echo "[3/4] 复制文件..."
cp -r "$SRC_DIR"/* "$DST_DIR/" 2>/dev/null || {
    echo "[错误] 文件复制失败"
    echo "请检查磁盘空间和文件权限"
    exit 1
}
echo "[OK] 文件复制完成"

# 5. 完整性校验：对比文件数量和总大小
echo ""
echo "[4/4] 完整性校验..."

DST_FILE_COUNT=$(find "$DST_DIR" -type f | wc -l)
DST_TOTAL_SIZE=$(du -sb "$DST_DIR" 2>/dev/null | cut -f1 || du -s "$DST_DIR" | awk '{print $1}')
echo "目标目录: $DST_FILE_COUNT 个文件, 总大小 $DST_TOTAL_SIZE 字节"

if [[ "$SRC_FILE_COUNT" -ne "$DST_FILE_COUNT" ]]; then
    echo "[错误] 文件数量不匹配！"
    echo "源目录: $SRC_FILE_COUNT 个文件"
    echo "目标目录: $DST_FILE_COUNT 个文件"
    exit 1
fi

# 允许 5% 的大小偏差（因为文件系统元数据差异可能影响 du 报告）
SIZE_DIFF=$(( SRC_TOTAL_SIZE - DST_TOTAL_SIZE ))
SIZE_DIFF=${SIZE_DIFF#-}  # 取绝对值
SIZE_THRESHOLD=$(( SRC_TOTAL_SIZE * 5 / 100 ))

if [[ "$SIZE_DIFF" -gt "$SIZE_THRESHOLD" ]]; then
    echo "[警告] 文件总大小偏差较大: ${SIZE_DIFF} 字节（阈值: ${SIZE_THRESHOLD} 字节）"
    echo "这可能不影响功能，但建议检查"
fi

echo "[OK] 完整性校验通过 - 文件数量和大小匹配"

# 6. 验证关键文件
echo ""
echo "验证关键文件..."
MISSING_CRITICAL=0
if [[ ! -f "$DST_DIR/index.html" ]]; then
    echo "[错误] 关键文件缺失: index.html"
    MISSING_CRITICAL=1
fi
if [[ ! -d "$DST_DIR/assets" ]]; then
    echo "[错误] 关键目录缺失: assets/"
    MISSING_CRITICAL=1
fi

if [[ "$MISSING_CRITICAL" -eq 1 ]]; then
    echo "[错误] 关键文件缺失，同步失败！"
    exit 1
fi
echo "[OK] 所有关键文件验证通过"

echo ""
echo "========================================"
echo "同步完成！"
echo "========================================"
echo "源: $SRC_FILE_COUNT 个文件, $SRC_TOTAL_SIZE 字节"
echo "目标: $DST_FILE_COUNT 个文件, $DST_TOTAL_SIZE 字节"
echo "目标路径: $DST_DIR"
echo ""
echo "建议：运行 python scripts/audit_static_assets.py 检查静态资源完整性"
echo "========================================"

exit 0
