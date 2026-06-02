# 项目 A 设计文档：诊断问题修复

**日期**: 2026-05-31 | **状态**: 已批准 | **范围**: 后端安全模块 + 审批测试 + 前端错误反馈

## 概述

修复系统诊断报告中发现的 CRITICAL/HIGH 优先级问题，提升安全健壮性和测试覆盖。

## 修复项设计

### 1. 审批工作流测试 (`test_approval_workflow.py`)

**问题**: 当前文件为自动生成空壳，零测试覆盖。

**方案**: 使用 SQLite 内存数据库重写，覆盖6个核心场景：
- `test_normal_approval_flow` — 提交→审核→通过
- `test_reject_flow` — 提交→驳回→重新提交
- `test_withdraw_flow` — 提交→撤回
- `test_timeout_detection` — 超48小时检测
- `test_concurrent_submit` — 并发幂等
- `test_status_transitions` — 状态机完整性

Fixture: `test_db` (SQLite :memory:)

### 2. 安全模块异常处理 (`security.py`)

**#3 (line 36)**: `except Exception: pass` → 分层处理
- `ValueError` → debug日志（bcrypt版本兼容，预期行为）
- 其他 `Exception` → error日志+exc_info（记录但不崩溃）

**#4 (line 133)**: `except Exception: return False` → 区分处理
- `ValueError` → return False（passlib预期错误）
- 其他 `Exception` → critical日志 + raise（加密库故障不应静默）

### 3. 前端用户反馈 (`*.vue`)

**目标文件**: HomeSafe.vue, ForgotPassword.vue, Register.vue

**模式**: 在现有 `catch` 块中 `console.error` 之后添加 `ElMessage.error('操作失败，请重试')`

### 4. 差异追踪日志 (`projects.py`)

**修复**: `except: self.diff_summary = None` → 添加 `logger.warning("变更追踪失败", exc_info=True)`

### 5. 测试恢复

- `test_funds_enhanced.py`: 更新API路径（8个skip）
- `test_permission_utils.py`: 更新函数签名（7个skip）

## 不涉及

- 新增依赖
- 数据库 Schema 变更
- API 行为变更（仅异常处理从静默→日志）
- 前端新页面/组件

## 验收标准

- `python -m pytest tests/test_approval_workflow.py -v` 至少6个测试通过
- `python -m pytest tests/test_security_fixes.py -v` 通过
- `python -m pytest tests/test_funds_enhanced.py -v` 减少skip
- `python -m pytest tests/test_permission_utils.py -v` 减少skip
- `python -m flake8 backend/app/core/security.py --max-line-length=120` 无新增问题
