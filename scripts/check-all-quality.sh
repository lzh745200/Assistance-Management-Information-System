#!/bin/bash
# 一键运行所有代码质量检测
# 用法: bash scripts/check-all-quality.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "军队乡村振兴系统 - 代码质量全面检测"
echo "========================================="
echo ""
echo "项目路径: $PROJECT_ROOT"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 创建总报告目录
REPORT_DIR="$PROJECT_ROOT/quality-reports"
mkdir -p "$REPORT_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SUMMARY_FILE="$REPORT_DIR/summary_${TIMESTAMP}.txt"

echo "=========================================" > "$SUMMARY_FILE"
echo "代码质量检测汇总报告" >> "$SUMMARY_FILE"
echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$SUMMARY_FILE"
echo "=========================================" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

# 后端检测
echo "========================================="
echo "第一部分: 后端代码检测"
echo "========================================="
echo ""

if [ -f "$SCRIPT_DIR/check-backend-quality.sh" ]; then
    bash "$SCRIPT_DIR/check-backend-quality.sh" | tee -a "$SUMMARY_FILE"
else
    echo "⚠️  后端检测脚本不存在: $SCRIPT_DIR/check-backend-quality.sh"
fi

echo ""
echo "========================================="
echo "第二部分: 前端代码检测"
echo "========================================="
echo ""

cd "$PROJECT_ROOT/frontend" || exit 1

if [ -f "scripts/check-frontend-quality.js" ]; then
    node scripts/check-frontend-quality.js | tee -a "$SUMMARY_FILE"
else
    echo "⚠️  前端检测脚本不存在"
fi

cd "$PROJECT_ROOT"

# 生成最终汇总
echo "" >> "$SUMMARY_FILE"
echo "=========================================" >> "$SUMMARY_FILE"
echo "检测完成" >> "$SUMMARY_FILE"
echo "=========================================" >> "$SUMMARY_FILE"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

echo ""
echo "========================================="
echo "全部检测完成！"
echo "========================================="
echo ""
echo "📊 汇总报告: $SUMMARY_FILE"
echo "📁 详细报告: $REPORT_DIR/"
echo ""
echo "💡 下一步建议:"
echo "  1. 查看汇总报告了解整体质量状况"
echo "  2. 优先修复高危安全漏洞"
echo "  3. 逐步提升代码质量评分"
echo "  4. 定期运行此脚本监控代码质量"
echo ""
