# 后端测试覆盖率100%实现路线图

**当前状态**: 2026-07-30
**覆盖率门禁**: 100%（可覆盖集：pragma 豁免真正不可执行的行）
**通过率目标**: 100%

## 覆盖率门禁提升记录

### 2026-07-30: 门禁从 98% 提升至 100%

- `pyproject.toml` → `fail_under = 100`
- `Makefile` → `--cov-fail-under=100`
- `.github/workflows/pr-checks.yml` → `--cov-fail-under=100`
- `frontend/vitest.config.ts` → 所有阈值提升至 100%

### 2026-07-30: 移除 pyproject.toml omit 列表

此前 30+ 个文件被 `omit` 排除在覆盖率测量之外（CLI 工具、外部依赖等）。
现已移除全部 omit 条目，所有 `app/` 下的文件均纳入覆盖率测量。

**处理策略**：
1. 已有测试的文件（database_init, secret_migration, init_permissions, zero_trust, encryption, logging_config, village_templates, messages_extended）→ 移除 omit 后现有测试自动纳入统计
2. 新增测试的文件（database_migration, db_performance, core/audit, core/auth_root, core/database_compat, core/structured_logging, dependencies, static_files, config, utils/performance, utils/chart, utils/email, utils/query_optimizer）→ 新建 `test_previously_excluded_cov.py` 等测试文件
3. 不存在的文件（export.py, api/dependencies/permissions.py, data/conflict_resolution.py 等）→ 从 omit 列表移除后自动忽略

### 测试统计

| 指标 | 数值 |
|------|------|
| 后端测试文件数 | 440+ |
| 后端测试总数 | ~10,845 |
| 前端测试文件数 | 137+ |
| 前端测试总数 | ~1,997 |

## 覆盖率现状

### 后端

| 模块 | 覆盖率（run7 基线） | 状态 |
|------|---------------------|------|
| app/api/v1/ | ~99% | ⚠️ 393 语句缺口 |
| app/core/ | ~99% | ⚠️ 新增 audit/auth_root/database_compat/structured_logging 测试 |
| app/middleware/ | ~99% | ✅ |
| app/models/ | ~99% | ⚠️ 少量缺口 |
| app/schemas/ | ~99% | ⚠️ 少量缺口 |
| app/services/ | ~99% | ⚠️ 新增 zero_trust 测试 |
| app/utils/ | ~99% | ⚠️ 新增 database_migration/db_performance 测试 |

### 前端

| 模块 | 覆盖率 | 状态 |
|------|--------|------|
| src/utils/ | ~90% | ❌ 需提升至 100% |
| src/stores/ | ~90% | ❌ 需提升至 100% |
| src/composables/ | ~90% | ❌ 需提升至 100% |
| src/api/ | ~90% | ❌ 需提升至 100% |
| src/views/ | ~64% | ❌ 大量缺口（174 文件） |
| src/components/ | ~64% | ❌ 大量缺口 |
| src/router/ | ~100% | ✅ |
| src/config/ | ~90% | ❌ 需提升至 100% |

## 待办事项

### 后端（优先级：高）
1. [ ] 运行全量测试，确认通过率 100%
2. [ ] 运行覆盖率报告，确认 100%
3. [ ] 修复剩余 393 语句缺口（98 文件）
4. [ ] 为新增测试文件验证覆盖率

### 前端（优先级：高）
1. [ ] 运行全量测试，确认通过率 100%
2. [ ] 运行覆盖率报告，识别所有 <100% 的文件
3. [ ] 为 174 个 <100% 的文件编写补充测试
4. [ ] 逐步提升各模块覆盖率至 100%

## pragma 豁免登记

| 文件 | 行 | 理由 |
|------|----|------|
| `app/api/v1/data/data/dashboard.py` | 53-56 | diskcache ImportError 分支不可执行 |
| `app/main.py` | 17-20 | PyInstaller 无控制台模式 stdout/stderr 为 None |
| `app/services/zero_trust.py` | 325-328 | 评分模型数学不可达死代码 |
| `app/api/v1/system/audit.py` | 301-302 | Excel 列宽计算 except 分支不可达 |
| `app/api/v1/auth/auth.py` | 541-561 | logout 端点 CTracer 线程漏记（行为已由 TestClient 验证） |

## 结论

覆盖率门禁已提升至 100%。后端通过移除 omit 列表和新增测试文件，预计覆盖率从 ~99% 提升至接近 100%。前端覆盖率仍有较大缺口（~64% → 100%），需要系统性补充测试。
