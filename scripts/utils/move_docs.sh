#!/bin/bash
set -e

echo "开始整理文档..."

# 01-快速开始
echo "[1/8] 整理快速开始文档..."
git mv QUICK_START.md docs/01-快速开始/ 2>/dev/null || true
git mv QUICK_START_ARM64.md docs/01-快速开始/ 2>/dev/null || true
git mv ARM64_QUICK_START.md docs/01-快速开始/ 2>/dev/null || true
git mv docs/快速启动指南.md docs/01-快速开始/ 2>/dev/null || true
git mv docs/启动指南.md docs/01-快速开始/ 2>/dev/null || true
git mv docs/单机版安装手册.md docs/01-快速开始/ 2>/dev/null || true
git mv docs/单机版安装手册_v1.0.3.md docs/01-快速开始/ 2>/dev/null || true

# 02-用户手册
echo "[2/8] 整理用户手册..."
git mv docs/使用指南.md docs/02-用户手册/ 2>/dev/null || true
git mv docs/经费管理模块操作说明.md docs/02-用户手册/ 2>/dev/null || true
[ -d "docs/用户手册" ] && git mv docs/用户手册/*.md docs/02-用户手册/ 2>/dev/null || true

# 04-部署文档
echo "[3/8] 整理部署文档..."
git mv BUILD_TEST_GUIDE.md docs/04-部署文档/ 2>/dev/null || true
git mv DEB_DEPLOYMENT_GUIDE.md docs/04-部署文档/ 2>/dev/null || true
git mv DEB_DEPLOYMENT_GUIDE_ARM64.md docs/04-部署文档/ 2>/dev/null || true
git mv DEB_PACKAGE_README.md docs/04-部署文档/ 2>/dev/null || true
git mv docs/麒麟V10_ARM64_部署指南.md docs/04-部署文档/ 2>/dev/null || true
git mv docs/部署安装手册.md docs/04-部署文档/ 2>/dev/null || true
git mv docs/技术文档/部署指南.md docs/04-部署文档/ 2>/dev/null || true
git mv docs/技术文档/构建打包指南.md docs/04-部署文档/ 2>/dev/null || true
git mv docs/技术文档/部署检查清单.md docs/04-部署文档/ 2>/dev/null || true

# 05-测试文档
echo "[4/8] 整理测试文档..."
[ -d "docs/测试方案" ] && git mv docs/测试方案/*.md docs/05-测试文档/ 2>/dev/null || true
git mv 系统验证测试报告.md docs/05-测试文档/ 2>/dev/null || true

# 06-构建文档
echo "[5/8] 整理构建文档..."
git mv BUILD_TEST_REPORT.md docs/06-构建文档/ 2>/dev/null || true
git mv BUILD_TEST_SUMMARY.md docs/06-构建文档/ 2>/dev/null || true
git mv BUILD_COMPLETION_SUMMARY.md docs/06-构建文档/ 2>/dev/null || true
git mv ARM64_BUILD_README.md docs/06-构建文档/ 2>/dev/null || true
git mv WINDOWS_BUILD_ARM64_GUIDE.md docs/06-构建文档/ 2>/dev/null || true

# 07-问题修复
echo "[6/8] 整理问题修复文档..."
git mv ISSUES_FIX_SUMMARY.md docs/07-问题修复/ 2>/dev/null || true
git mv SYSTEM_COMPREHENSIVE_CHECK_REPORT.md docs/07-问题修复/ 2>/dev/null || true
git mv CODE_QUALITY_REPORT.md docs/07-问题修复/ 2>/dev/null || true
git mv CRITICAL_ISSUES_FIX.md docs/07-问题修复/ 2>/dev/null || true
git mv LOGIN_FIX_GUIDE.md docs/07-问题修复/ 2>/dev/null || true
git mv WORK_CALENDAR_FIX_GUIDE.md docs/07-问题修复/ 2>/dev/null || true
git mv fix_401_issue.md docs/07-问题修复/ 2>/dev/null || true

# 08-项目管理
echo "[7/8] 整理项目管理文档..."
[ -d "docs/项目管理" ] && git mv docs/项目管理/*.md docs/08-项目管理/ 2>/dev/null || true
git mv 完整交付总结.md docs/08-项目管理/ 2>/dev/null || true
git mv PROJECT_CLEANUP_SUMMARY.md docs/08-项目管理/ 2>/dev/null || true
git mv PROJECT_FILE_INVENTORY.md docs/08-项目管理/ 2>/dev/null || true

# 归档过时文件
echo "[8/8] 归档过时文件..."
git mv DEPLOYMENT_CHECKLIST.md archive/deprecated_docs/ 2>/dev/null || true
git mv DEPLOYMENT_READINESS_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv DEPLOYMENT_READY_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv DEPLOYMENT_VERIFICATION_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv FINAL_DELIVERY_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv FINAL_DEPLOYMENT_SUMMARY.md archive/deprecated_docs/ 2>/dev/null || true
git mv FINAL_EXECUTION_SUMMARY.md archive/deprecated_docs/ 2>/dev/null || true
git mv FIELD_COMPATIBILITY_FIX_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv DATABASE_INDEX_GUIDE.md archive/deprecated_docs/ 2>/dev/null || true
git mv DEPENDENCY_UPDATE_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv MONITORING_INTEGRATION_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv RELEASE_NOTES_V1.0.4.md archive/deprecated_docs/ 2>/dev/null || true
git mv VERIFICATION_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv OPTIMIZATION_COMPLETE.md archive/deprecated_docs/ 2>/dev/null || true
git mv OPTIMIZATION_COMPLETE_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv OPTIMIZATION_IMPLEMENTATION_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv SYSTEM_CHECK_FINAL_REPORT.md archive/deprecated_docs/ 2>/dev/null || true
git mv "军队乡村振兴管理系统 - 全平台打包、版本统一、文档与PPT方案.md" archive/deprecated_docs/ 2>/dev/null || true

# 归档 backend 临时文件
git mv backend/DECIMAL_FIX_COMPLETE.md archive/deprecated_docs/ 2>/dev/null || true
git mv backend/ORGANIZATION_DELETE_COMPLETE.md archive/deprecated_docs/ 2>/dev/null || true
git mv backend/ORGANIZATION_DELETE_DIAGNOSIS.md archive/deprecated_docs/ 2>/dev/null || true
git mv backend/ORGANIZATION_DELETE_FINAL_FIX.md archive/deprecated_docs/ 2>/dev/null || true
git mv backend/ORGANIZATION_DELETE_PHYSICAL.md archive/deprecated_docs/ 2>/dev/null || true
git mv backend/RESTART_REQUIRED.md archive/deprecated_docs/ 2>/dev/null || true

echo "文档整理完成!"
