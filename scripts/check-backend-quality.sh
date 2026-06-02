#!/bin/bash
# 后端代码质量检测脚本
# 用法: bash scripts/check-backend-quality.sh

set -e

echo "========================================="
echo "后端代码质量检测开始"
echo "========================================="
echo ""

# 切换到后端目录
cd "$(dirname "$0")/../backend" || exit 1

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 错误: 未找到虚拟环境，请先运行: python -m venv .venv"
    exit 1
fi

# 激活虚拟环境
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate  # Windows Git Bash
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate  # Linux/Mac
else
    echo "❌ 错误: 无法激活虚拟环境"
    exit 1
fi

# 检查开发依赖是否已安装
echo "📦 检查开发依赖..."
pip show bandit > /dev/null 2>&1 || {
    echo "⚠️  开发依赖未安装，正在安装..."
    pip install -r requirements-dev.txt
}
echo "✅ 开发依赖已就绪"
echo ""

# 创建报告目录
REPORT_DIR="quality-reports"
mkdir -p "$REPORT_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "========================================="
echo "1. 代码格式检查 (Black)"
echo "========================================="
black --check app/ || {
    echo "⚠️  代码格式不符合规范，运行 'black app/' 自动格式化"
}
echo ""

echo "========================================="
echo "2. 导入排序检查 (isort)"
echo "========================================="
isort --check-only app/ || {
    echo "⚠️  导入顺序不符合规范，运行 'isort app/' 自动修复"
}
echo ""

echo "========================================="
echo "3. 代码风格检查 (Flake8)"
echo "========================================="
flake8 app/ --max-line-length=120 --statistics --output-file="$REPORT_DIR/flake8_${TIMESTAMP}.txt" || true
echo "📄 报告已保存: $REPORT_DIR/flake8_${TIMESTAMP}.txt"
echo ""

echo "========================================="
echo "4. 类型检查 (MyPy)"
echo "========================================="
mypy app/ --ignore-missing-imports --no-strict-optional > "$REPORT_DIR/mypy_${TIMESTAMP}.txt" 2>&1 || true
echo "📄 报告已保存: $REPORT_DIR/mypy_${TIMESTAMP}.txt"
echo ""

echo "========================================="
echo "5. 代码质量检查 (Pylint)"
echo "========================================="
pylint app/ --rcfile=.pylintrc > "$REPORT_DIR/pylint_${TIMESTAMP}.txt" 2>&1 || true
PYLINT_SCORE=$(grep "Your code has been rated at" "$REPORT_DIR/pylint_${TIMESTAMP}.txt" | awk '{print $7}' | cut -d'/' -f1)
echo "📊 Pylint 评分: ${PYLINT_SCORE:-N/A}/10.00"
echo "📄 报告已保存: $REPORT_DIR/pylint_${TIMESTAMP}.txt"
echo ""

echo "========================================="
echo "6. 安全漏洞扫描 (Bandit)"
echo "========================================="
bandit -r app/ -f json -o "$REPORT_DIR/bandit_${TIMESTAMP}.json" || true
bandit -r app/ -f txt -o "$REPORT_DIR/bandit_${TIMESTAMP}.txt" || true
BANDIT_HIGH=$(grep -c "Severity: High" "$REPORT_DIR/bandit_${TIMESTAMP}.txt" || echo "0")
BANDIT_MEDIUM=$(grep -c "Severity: Medium" "$REPORT_DIR/bandit_${TIMESTAMP}.txt" || echo "0")
BANDIT_LOW=$(grep -c "Severity: Low" "$REPORT_DIR/bandit_${TIMESTAMP}.txt" || echo "0")
echo "🔴 高危漏洞: $BANDIT_HIGH"
echo "🟡 中危漏洞: $BANDIT_MEDIUM"
echo "🟢 低危漏洞: $BANDIT_LOW"
echo "📄 报告已保存: $REPORT_DIR/bandit_${TIMESTAMP}.txt"
echo ""

echo "========================================="
echo "7. 依赖安全检查 (Safety)"
echo "========================================="
safety check --json > "$REPORT_DIR/safety_${TIMESTAMP}.json" 2>&1 || true
safety check > "$REPORT_DIR/safety_${TIMESTAMP}.txt" 2>&1 || true
echo "📄 报告已保存: $REPORT_DIR/safety_${TIMESTAMP}.txt"
echo ""

echo "========================================="
echo "8. 依赖审计 (pip-audit)"
echo "========================================="
pip-audit --format json > "$REPORT_DIR/pip-audit_${TIMESTAMP}.json" 2>&1 || true
pip-audit > "$REPORT_DIR/pip-audit_${TIMESTAMP}.txt" 2>&1 || true
echo "📄 报告已保存: $REPORT_DIR/pip-audit_${TIMESTAMP}.txt"
echo ""

echo "========================================="
echo "9. 代码复杂度分析 (Radon)"
echo "========================================="
echo "📊 圈复杂度分析:"
radon cc app/ -a -s > "$REPORT_DIR/radon_cc_${TIMESTAMP}.txt"
cat "$REPORT_DIR/radon_cc_${TIMESTAMP}.txt"
echo ""
echo "📊 可维护性指数:"
radon mi app/ -s > "$REPORT_DIR/radon_mi_${TIMESTAMP}.txt"
cat "$REPORT_DIR/radon_mi_${TIMESTAMP}.txt"
echo "📄 报告已保存: $REPORT_DIR/radon_cc_${TIMESTAMP}.txt, $REPORT_DIR/radon_mi_${TIMESTAMP}.txt"
echo ""

echo "========================================="
echo "10. 测试覆盖率"
echo "========================================="
pytest tests/ --cov=app --cov-report=html --cov-report=term > "$REPORT_DIR/coverage_${TIMESTAMP}.txt" 2>&1 || true
echo "📄 报告已保存: $REPORT_DIR/coverage_${TIMESTAMP}.txt"
echo "📄 HTML 报告: htmlcov/index.html"
echo ""

echo "========================================="
echo "检测完成！"
echo "========================================="
echo ""
echo "📊 汇总报告:"
echo "  - Pylint 评分: ${PYLINT_SCORE:-N/A}/10.00"
echo "  - 安全漏洞: 🔴 $BANDIT_HIGH 高危 | 🟡 $BANDIT_MEDIUM 中危 | 🟢 $BANDIT_LOW 低危"
echo ""
echo "📁 所有报告保存在: $REPORT_DIR/"
echo ""
echo "💡 建议:"
echo "  1. 优先修复高危安全漏洞"
echo "  2. 提升 Pylint 评分至 8.0 以上"
echo "  3. 保持测试覆盖率在 80% 以上"
echo "  4. 定期更新依赖包修复安全漏洞"
echo ""
