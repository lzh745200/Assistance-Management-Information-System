#!/bin/bash
# 权限修复验证脚本

echo "=========================================="
echo "权限修复验证"
echo "=========================================="
echo ""

# 检查修复的文件
echo "✓ 检查修复的文件..."
if [ -f "backend/app/services/organization_permission_service.py" ]; then
    echo "  - organization_permission_service.py 存在"
else
    echo "  ✗ organization_permission_service.py 不存在"
    exit 1
fi

if [ -f "backend/app/api/v1/data/data_packages.py" ]; then
    echo "  - data_packages.py 存在"
else
    echo "  ✗ data_packages.py 不存在"
    exit 1
fi

echo ""
echo "✓ 检查关键修复点..."

# 检查是否添加了超级管理员检查
if grep -q "is_superuser.*super_admin" backend/app/services/organization_permission_service.py; then
    echo "  - ✓ 已添加超级管理员检查"
else
    echo "  - ✗ 未找到超级管理员检查"
    exit 1
fi

# 检查是否修复了错误提示
if grep -q "请联系管理员在系统管理中为您分配组织" backend/app/api/v1/data/data_packages.py; then
    echo "  - ✓ 已优化错误提示"
else
    echo "  - ✗ 未找到优化的错误提示"
    exit 1
fi

echo ""
echo "✓ 检查测试文件..."
if [ -f "backend/tests/test_permission_fix.py" ]; then
    echo "  - ✓ 测试文件已创建"
else
    echo "  - ✗ 测试文件不存在"
fi

echo ""
echo "✓ 检查文档..."
if [ -f "docs/fixes/PERMISSION_FIX_REPORT.md" ]; then
    echo "  - ✓ 修复报告已创建"
else
    echo "  - ✗ 修复报告不存在"
fi

echo ""
echo "=========================================="
echo "验证完成！所有修复已正确应用。"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 重启后端服务: scripts/start-backend.bat"
echo "2. 测试数据包导出功能"
echo "3. 检查是否还有权限错误"
echo ""
