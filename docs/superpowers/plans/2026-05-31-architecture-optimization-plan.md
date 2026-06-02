# 架构优化实施计划 — 军队乡村振兴管理系统

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过三阶段22个任务消除分层违例、统一数据模型、激活服务层DDD架构，所有改动保持严格向后兼容。

**Architecture:** 重构遵循"先低风险后高风险"原则：阶段一清理分层违例和死代码（9个任务），阶段二统一数据模型继承和消除冗余（5个任务），阶段三拆分Fat Controllers并激活领域服务层（7个任务+子任务）。每阶段有硬性门控条件。

**Tech Stack:** Python 3.11 / FastAPI / SQLAlchemy / SQLite WAL / Alembic / pytest / Vue 3 + TypeScript / flake8

**Reference Spec:** `docs/superpowers/specs/2026-05-31-architecture-optimization-design.md`

---

## File Structure Map

### Phase 1 Files (消除分层违例)

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/app/core/migration_helper.py` | **CREATE** | `_migrate_missing_columns` 提取自此 |
| `backend/app/core/constants.py` | **CREATE** | `ANALYTICS_CACHE_PREFIX` 等全局常量 |
| `backend/app/services/repositories/__init__.py` | **CREATE** | Repository 包导出 |
| `backend/app/services/repositories/base.py` | **CREATE** | `BaseRepository` 基类（CRUD 封装） |
| `backend/app/services/repositories/fund_repository.py` | **CREATE** | `FundRepository` 模式验证 |
| `backend/app/services/version_service.py` | MODIFY | 替换 `from app.main import` → `from app.core.migration_helper import` |
| `backend/app/services/backup_scheduler.py` | MODIFY | 替换 API 层导入 → `core.constants` + 服务调用 |
| `backend/app/services/excel_importer_service.py` | MODIFY | `UploadFile` → `(bytes, str, str)` 三元组 |
| `backend/app/core/permissions.py` | MODIFY | 改为 `rbac_service.py` 的薄封装 |
| `backend/app/core/audit.py` | MODIFY | 委托给 `AuditService` |
| `backend/app/services/fund_service.py` | MODIFY | 桩→真实 CRUD 委托 |
| `backend/app/services/supported_village_service.py` | MODIFY | 桩→真实 CRUD 委托 |
| `backend/app/services/batch_service.py` | MODIFY | 桩→真实批量操作 |
| `backend/app/services/report_export_service.py` | MODIFY | 桩→委托 `export_service.py` |
| `backend/app/services/metrics_service.py` | MODIFY | 桩→委托 `business_metrics_service.py` |
| `backend/app/services/async_export_service.py` | MODIFY | 桩→委托 `chunked_upload_service.py` |
| `backend/app/services/import_export_history_service.py` | MODIFY | 桩→真实历史查询 |
| `backend/app/services/project/__init__.py` | MODIFY | 移除不存在的导入 |
| `backend/app/api/v1/import_export/import_data.py` | MODIFY | 适配 `excel_importer` 新签名 |
| `backend/app/api/v1/data/__init__.py` | MODIFY | 添加死代码废弃警告 |
| `backend/app/api/v1/data/analytics.py` | DELETE | 死代码（被 `data/data/analytics.py` 覆盖） |
| `backend/app/api/v1/data/dashboard.py` | DELETE | 死代码 |
| `backend/app/api/v1/data/statistics.py` | DELETE | 死代码 |
| `backend/app/api/v1/data/reports.py` | DELETE | 死代码 |
| `backend/app/api/v1/data/data_reports.py` | DELETE | 死代码 |
| `backend/app/api/v1/data/data_packages.py` | DELETE | 死代码 |
| `backend/app/api/v1/data/data_quality.py` | DELETE | 死代码 |

### Phase 2 Files (数据模型规范化)

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/app/models/base.py` | MODIFY | 激活 `SoftDeleteMixin` + `VersionMixin` |
| `backend/alembic/versions/YYYYMMDD_unify_inheritance.py` | **CREATE** | 统一继承迁移 |
| `backend/alembic/versions/YYYYMMDD_soft_delete.py` | **CREATE** | SoftDelete 列迁移 |
| `backend/alembic/versions/YYYYMMDD_version_mixin.py` | **CREATE** | Version 列迁移 |
| `backend/alembic/versions/YYYYMMDD_remove_dual_fk.py` | **CREATE** | 移除冗余 project_id FK |
| `backend/alembic/versions/YYYYMMDD_dedup_annual.py` | **CREATE** | 去重年度数据表 |
| ~50 model files | MODIFY | 统一继承到 BaseModel |
| 8 `fund_lifecycle` models | MODIFY | 移除冗余 `project_id` 列，替换为 property |

### Phase 3 Files (服务层重构)

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/app/services/funding/phase_init_service.py` | **CREATE** | 阶段1: 资金阶段初始化 |
| `backend/app/services/funding/phase_budget_service.py` | **CREATE** | 阶段2: 预算基线管理 |
| `backend/app/services/funding/phase_transfer_service.py` | **CREATE** | 阶段3: 资金调拨凭证 |
| `backend/app/services/funding/phase_contract_service.py` | **CREATE** | 阶段4: 合同管理 |
| `backend/app/services/funding/phase_anomaly_service.py` | **CREATE** | 阶段5: 异常检测 |
| `backend/app/services/funding/phase_settlement_service.py` | **CREATE** | 阶段6: 结算管理 |
| `backend/app/services/funding/phase_verification_service.py` | **CREATE** | 阶段7: 资产核销 |
| `backend/app/services/fund_health_service.py` | **CREATE** | 资金健康评分 |
| `backend/app/services/file_management_service.py` | **CREATE** | 文件上传/下载/安全 |
| `backend/app/services/assessment/__init__.py` | **CREATE** | 评估子包 |
| `backend/app/services/assessment/scoring_service.py` | **CREATE** | 评分引擎 |
| `backend/app/services/assessment/anomaly_service.py` | **CREATE** | 异常检测 |
| `backend/app/services/assessment/trend_service.py` | **CREATE** | 趋势预测 |
| `backend/app/services/repositories/village_repository.py` | **CREATE** | Village 数据访问 |
| `backend/app/services/repositories/project_repository.py` | **CREATE** | Project 数据访问 |
| `backend/app/services/repositories/school_repository.py` | **CREATE** | School 数据访问 |
| `backend/app/services/repositories/approval_repository.py` | **CREATE** | Approval 数据访问 |
| `backend/app/api/v1/fund_lifecycle.py` | MODIFY | 路由委托给 7 个 phase 服务 |
| `backend/app/api/v1/projects.py` | MODIFY | 路由委托给子服务 |
| `backend/app/api/v1/assessment.py` | MODIFY | 路由委托给 assessment/ 子包 |
| `backend/app/services/data_validator_service.py` | MODIFY | 拆分为 3 个子服务 |
| `backend/app/services/data_package_service.py` | MODIFY | 拆分为 CRUD + 加密 + 冲突解决 |
| `backend/app/services/data_sync_service.py` | MODIFY | 提取增量导出逻辑 |
| `backend/app/services/analytics_service.py` | MODIFY | 按报表类型拆分 |
| `backend/app/services/message_template_service.py` | MODIFY | 分离模板 CRUD 和默认数据 |

---

## Phase 0: 性能基线测量（阶段一开始前执行）

### Task 0: Establish Performance Baselines

**Files:**
- Create: `docs/superpowers/plans/baseline-2026-05-31.md`

- [ ] **Step 1: 启动后端服务**

```bash
cd backend && python start.py &
sleep 3
```

- [ ] **Step 2: 预热（3次请求，排除冷启动）**

```bash
for i in 1 2 3; do
  curl -s http://localhost:8000/api/v1/funds/?page=1\&page_size=20 > /dev/null
done
```

- [ ] **Step 3: 测量 KPI-1 — 资金列表 P50/P95**

```bash
python -c "
import time, requests, statistics
times = []
for i in range(10):
    start = time.perf_counter()
    requests.get('http://localhost:8000/api/v1/funds/', params={'page':1,'page_size':20})
    times.append((time.perf_counter() - start) * 1000)
times.sort()
print(f'Funds List: P50={times[4]:.1f}ms P95={times[8]:.1f}ms')
"
```

- [ ] **Step 4: 测量 KPI-2 — 生命周期阶段**

```bash
python -c "
import time, requests
# 先获取一个 fund_id
r = requests.get('http://localhost:8000/api/v1/funds/', params={'page':1,'page_size':1})
fund_id = r.json()['data']['items'][0]['id'] if r.json()['data']['items'] else None
if fund_id:
    times = []
    for i in range(10):
        start = time.perf_counter()
        requests.get(f'http://localhost:8000/api/v1/fund-lifecycle/phases/{fund_id}')
        times.append((time.perf_counter() - start) * 1000)
    times.sort()
    print(f'Lifecycle Phases: P50={times[4]:.1f}ms P95={times[8]:.1f}ms')
"
```

- [ ] **Step 5: 测量 KPI-3 — 项目列表**

```bash
python -c "
import time, requests
times = []
for i in range(10):
    start = time.perf_counter()
    requests.get('http://localhost:8000/api/v1/projects/', params={'page':1,'page_size':20})
    times.append((time.perf_counter() - start) * 1000)
times.sort()
print(f'Projects List: P50={times[4]:.1f}ms P95={times[8]:.1f}ms')
"
```

- [ ] **Step 6: 测量 KPI-4 — 项目创建（POST）**

```bash
python -c "
import time, requests, json
times = []
payload = {'name': 'baseline_test_project', 'description': 'auto-delete', 'village_id': 1}
for i in range(10):
    start = time.perf_counter()
    r = requests.post('http://localhost:8000/api/v1/projects/', json=payload)
    times.append((time.perf_counter() - start) * 1000)
    # Clean up created test project
    if r.status_code == 200 and 'id' in r.json().get('data', {}):
        requests.delete(f\"http://localhost:8000/api/v1/projects/{r.json()['data']['id']}\")
times.sort()
print(f'Projects Create: P50={times[4]:.1f}ms P95={times[8]:.1f}ms')
"
```

- [ ] **Step 7: 记录基线到文档**

```bash
cat > docs/superpowers/plans/baseline-2026-05-31.md << 'EOF'
# Performance Baseline — 2026-05-31

| Endpoint | P50 (ms) | P95 (ms) | Notes |
|----------|----------|----------|-------|
| GET /api/v1/funds/ | [VALUE] | [VALUE] | page=1, size=20 |
| GET /api/v1/fund-lifecycle/phases/{id} | [VALUE] | [VALUE] | first fund in DB |
| GET /api/v1/projects/ | [VALUE] | [VALUE] | page=1, size=20 |
| POST /api/v1/projects/ | [VALUE] | [VALUE] | create + delete cleanup |
EOF
```

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/plans/baseline-2026-05-31.md
git commit -m "perf: record pre-refactor performance baselines"
```

---

## Phase 1: 消除分层违例 & 清理死代码

### Task 1: Extract _migrate_missing_columns to core/migration_helper.py (P1-1)

**Files:**
- Create: `backend/app/core/migration_helper.py`
- Modify: `backend/app/services/version_service.py:342`

- [ ] **Step 1: 创建 migration_helper.py**

```python
# backend/app/core/migration_helper.py
"""数据库迁移辅助函数。

从 version_service.py 提取，消除服务层对 app.main 的依赖。
"""

import logging
from typing import Set

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def migrate_missing_columns(engine: Engine, base_model) -> Set[str]:
    """检测并添加数据库中缺失的列（自动迁移）。

    原本在 app.main._migrate_missing_columns 中定义，
    version_service.py 需要此功能但不应依赖 app.main。
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    tables_modified: Set[str] = set()

    for mapper in base_model.registry.mappers:
        table = mapper.local_table
        if table.name not in existing_tables:
            continue

        existing_cols = {c["name"] for c in inspector.get_columns(table.name)}

        for column in table.columns:
            if column.name not in existing_cols:
                try:
                    col_type = str(column.type.compile(engine.dialect))
                    nullable = "NULL" if column.nullable else "NOT NULL"
                    default_clause = ""
                    if column.default:
                        default_val = column.default.arg
                        if isinstance(default_val, str):
                            default_clause = f" DEFAULT '{default_val}'"
                        elif default_val is not None:
                            default_clause = f" DEFAULT {default_val}"

                    sql = f"ALTER TABLE {table.name} ADD COLUMN {column.name} {col_type} {nullable}{default_clause}"
                    with engine.connect() as conn:
                        conn.execute(text(sql))
                        conn.commit()
                    tables_modified.add(table.name)
                    logger.info("Added column %s.%s", table.name, column.name)
                except Exception as e:
                    logger.warning("Failed to add column %s.%s: %s", table.name, column.name, e)

    return tables_modified
```

- [ ] **Step 2: 修改 version_service.py — 替换导入**

找到 `backend/app/services/version_service.py` 第 342 行附近的代码：

```python
# 替换前
from app.main import _migrate_missing_columns
_migrate_missing_columns(engine, ModelBase)

# 替换后
from app.core.migration_helper import migrate_missing_columns
migrate_missing_columns(engine, ModelBase)
```

- [ ] **Step 3: 验证 — 检查 app.main 中的原始函数仍存在**

```bash
grep -n "_migrate_missing_columns" backend/app/main.py
```

确保 `app.main._migrate_missing_columns` 仍然存在（其他调用者可能仍需它）。我们现在只是让 `version_service.py` 不直接依赖 `app.main`。

- [ ] **Step 4: 运行回归测试**

```bash
cd backend && python -m pytest tests/ -v -k "not test_system_api" --timeout=60 2>&1 | tail -20
```
Expected: 942 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/migration_helper.py backend/app/services/version_service.py
git commit -m "refactor(P1-1): extract _migrate_missing_columns to core/migration_helper

Breaks the service-layer dependency on app.main (application entry point).
version_service.py now imports from core.migration_helper instead."
```

---

### Task 2: Decouple backup_scheduler from API Layer (P1-2)

**Files:**
- Create: `backend/app/core/constants.py`
- Modify: `backend/app/services/backup_scheduler.py:19,57`

- [ ] **Step 1: 创建 core/constants.py**

```python
# backend/app/core/constants.py
"""全局常量定义。

消除跨层导入：调度层不应依赖 HTTP API 层的模块级常量。
"""

# 数据分析缓存前缀（原在 app.api.v1.data.analytics 中定义）
ANALYTICS_CACHE_PREFIX = "analytics:"

# 系统配置默认值
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
```

- [ ] **Step 2: 修改 backup_scheduler.py 第19行 — 替换 get_system_config 导入**

```python
# 替换前
from app.api.v1.system_config import get_system_config

# 替换后
from app.services.system_config_service import SystemConfigService
```

同时在 backup_scheduler.py 中找到所有 `get_system_config(...)` 调用，替换为：
```python
async def _get_config_value(db, key: str, default=None):
    service = SystemConfigService(db)
    config = await service.get_config(key)
    return config.value if config else default
```

- [ ] **Step 3: 修改 backup_scheduler.py 第57行 — 替换 ANALYTICS_CACHE_PREFIX**

```python
# 替换前
from app.api.v1.data.analytics import ANALYTICS_CACHE_PREFIX

# 替换后
from app.core.constants import ANALYTICS_CACHE_PREFIX
```

- [ ] **Step 4: 同步更新 app.api.v1.data.analytics 中的 ANALYTICS_CACHE_PREFIX**

在 `backend/app/api/v1/data/data/analytics.py` 中：
```python
# 添加导入
from app.core.constants import ANALYTICS_CACHE_PREFIX
# 移除原有的模块级定义，或改为 re-export：
# ANALYTICS_CACHE_PREFIX = ANALYTICS_CACHE_PREFIX  # backward compat
```

- [ ] **Step 5: 运行测试验证**

```bash
cd backend && python -m pytest tests/ -v -k "not test_system_api" --timeout=60 2>&1 | tail -5
```
Expected: 942 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/constants.py backend/app/services/backup_scheduler.py
git commit -m "refactor(P1-2): decouple backup_scheduler from API layer

- Extract ANALYTICS_CACHE_PREFIX to core/constants.py
- Replace get_system_config API import with SystemConfigService
- Eliminates scheduler→API dependency"
```

---

### Task 3: Remove FastAPI UploadFile from excel_importer_service (P1-3)

**Files:**
- Modify: `backend/app/services/excel_importer_service.py:14,708-713`
- Modify: `backend/app/api/v1/import_export/import_data.py` (调用方适配)

- [ ] **Step 1: 修改 excel_importer_service.py — 移除 UploadFile 导入**

```python
# 替换前 (line 14)
from fastapi import UploadFile

# 替换后
# UploadFile 移除。改为接受 file_bytes + filename + content_type 三元组。
```

- [ ] **Step 2: 修改 import_data_async 方法签名**

```python
# 替换前 (line 708-713)
async def import_data_async(
    self,
    file: UploadFile,
    user_id: int,
    mode: ImportMode = ImportMode.INCREMENTAL,
    entity_type: str = "supported_village",
) -> ImportResult:

# 替换后
async def import_data_async(
    self,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    user_id: int,
    mode: ImportMode = ImportMode.INCREMENTAL,
    entity_type: str = "supported_village",
) -> ImportResult:
```

- [ ] **Step 3: 修改方法体内 file.filename / file.file.read() 引用**

```python
# 替换 file.filename → filename
# 替换 await file.read() → file_bytes
# 替换 file.content_type → content_type
```

- [ ] **Step 4: 适配调用方 import_data.py**

在 `backend/app/api/v1/import_export/import_data.py` 中找到调用 `import_data_async` 的位置，修改为：

```python
# 替换前
result = await importer.import_data_async(file=file, user_id=current_user.id, ...)

# 替换后
file_bytes = await file.read()
result = await importer.import_data_async(
    file_bytes=file_bytes,
    filename=file.filename,
    content_type=file.content_type,
    user_id=current_user.id,
    ...
)
```

- [ ] **Step 5: 运行测试验证**

```bash
cd backend && python -m pytest tests/ -v -k "not test_system_api" --timeout=60 2>&1 | tail -5
```
Expected: 942 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/excel_importer_service.py backend/app/api/v1/import_export/import_data.py
git commit -m "refactor(P1-3): de-fastapi excel_importer — accept bytes instead of UploadFile

ExcelImporterService.import_data_async now accepts (file_bytes, filename,
content_type) instead of fastapi.UploadFile. Service can now be used from
CLI or background jobs without an HTTP context."
```

---

### Task 4: Merge Duplicate RBAC Implementations (P1-4)

**Files:**
- Modify: `backend/app/core/permissions.py`
- Modify: `backend/app/services/rbac_service.py`

- [ ] **Step 1: 检查两个 Permission 枚举的差异**

```bash
python -c "
from app.core.permissions import Permission as CorePerm
from app.services.rbac_service import Permission as ServicePerm
core_vals = {p.value for p in CorePerm}
service_vals = {p.value for p in ServicePerm}
print('Core-only permissions:', core_vals - service_vals)
print('Service-only permissions:', service_vals - core_vals)
print('Common permissions:', len(core_vals & service_vals))
"
```

- [ ] **Step 2: 将 core/permissions.py 的 Permission 改为从 rbac_service 导入**

```python
# backend/app/core/permissions.py (修改后)

from app.services.rbac_service import Permission, RBACService
# Permission enum 现在仅由 rbac_service.py 定义和维护

# ROLE_PERMISSIONS 移到 rbac_service.py
# get_role_permissions() 改为委托给 RBACService
```

- [ ] **Step 3: 将 ROLE_PERMISSIONS 映射合并到 rbac_service.py**

如果 `rbac_service.py` 中已有等效的 role-permission 映射，确保映射一致。
如果不存在，将 `core/permissions.py` 中的 `ROLE_PERMISSIONS` 字典移到 `rbac_service.py`。

- [ ] **Step 4: 更新所有从 core.permissions 导入 Permission 的文件**

```bash
grep -rn "from app.core.permissions import" backend/app/ --include="*.py"
grep -rn "from app.core import permissions" backend/app/ --include="*.py"
```

对于每个引用文件，确保导入路径仍然有效（`core/permissions.py` 现在 re-export 自 `rbac_service.py`）。

- [ ] **Step 5: 运行测试验证**

```bash
cd backend && python -m pytest tests/ -v -k "not test_system_api" --timeout=60 2>&1 | tail -5
```
Expected: 942 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/permissions.py backend/app/services/rbac_service.py
git commit -m "refactor(P1-4): merge duplicate RBAC — single Permission enum in rbac_service

core/permissions.py now re-exports from services/rbac_service.py.
Eliminates dual-maintenance risk for role-permission mappings."
```

---

### Task 5: Clean Up data/ Dead Code (P1-5)

**Files:**
- Delete: `backend/app/api/v1/data/analytics.py`
- Delete: `backend/app/api/v1/data/dashboard.py`
- Delete: `backend/app/api/v1/data/statistics.py`
- Delete: `backend/app/api/v1/data/reports.py`
- Delete: `backend/app/api/v1/data/data_reports.py`
- Delete: `backend/app/api/v1/data/data_packages.py`
- Delete: `backend/app/api/v1/data/data_quality.py`
- Modify: `backend/app/api/v1/data/__init__.py`

- [ ] **Step 1: 确认这些文件确实未被使用**

```bash
cd backend
for f in analytics dashboard statistics reports data_reports data_packages data_quality; do
  echo "=== Checking data/$f.py ==="
  grep -rn "from.*data\.$f\|import.*data\.$f" app/ --include="*.py" | grep -v "data/data/$f" | grep -v "__pycache__" || echo "  No external references found"
done
```

- [ ] **Step 2: 删除 7 个死代码文件**

```bash
cd backend/app/api/v1/data
rm analytics.py dashboard.py statistics.py reports.py data_reports.py data_packages.py data_quality.py
```

- [ ] **Step 3: 更新 data/__init__.py — 移除对已删除文件的引用**

确认 `data/__init__.py` 仅委托到 `data/data/`，没有直接导入上述文件。

- [ ] **Step 4: 运行测试验证**

```bash
cd backend && python -m pytest tests/ -v -k "not test_system_api" --timeout=60 2>&1 | tail -5
```
Expected: 942 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/data/
git commit -m "refactor(P1-5): remove 7 dead data/ files (duplicated by data/data/)

analytics.py, dashboard.py, statistics.py, reports.py, data_reports.py,
data_packages.py, data_quality.py were all dead code — data/__init__.py
delegates exclusively to data/data/ sub-package."
```

---

### Task 6: Fill 7 Stub Services (P1-6)

**Files:**
- Modify: `backend/app/services/fund_service.py`
- Modify: `backend/app/services/supported_village_service.py`
- Modify: `backend/app/services/batch_service.py`
- Modify: `backend/app/services/report_export_service.py`
- Modify: `backend/app/services/metrics_service.py`
- Modify: `backend/app/services/async_export_service.py`
- Modify: `backend/app/services/import_export_history_service.py`

- [ ] **Step 1: 实现 FundService (fund_service.py)**

```python
# backend/app/services/fund_service.py
"""Fund 业务服务 — 基本的 CRUD 委托层。"""
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.fund import Fund, FundAttachment, BudgetRecord

logger = logging.getLogger(__name__)


class FundService:
    """Fund 聚合根的基本数据操作。复杂业务逻辑委托给 domain/ 层。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_funds(self, *, page: int = 1, page_size: int = 20,
                        village_id: Optional[int] = None,
                        project_id: Optional[int] = None) -> dict:
        query = select(Fund)
        if village_id:
            query = query.where(Fund.village_id == village_id)
        if project_id:
            query = query.where(Fund.project_id == project_id)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        funds = result.scalars().all()
        count_query = select(Fund)
        if village_id:
            count_query = count_query.where(Fund.village_id == village_id)
        if project_id:
            count_query = count_query.where(Fund.project_id == project_id)
        total = (await self.db.execute(count_query)).scalars()
        total = len(total.all()) if hasattr(total, 'all') else 0
        return {"items": funds, "total": total, "page": page, "page_size": page_size}

    async def get_fund(self, fund_id: int) -> Optional[Fund]:
        result = await self.db.execute(select(Fund).where(Fund.id == fund_id))
        return result.scalar_one_or_none()

    async def create_fund(self, **kwargs) -> Fund:
        fund = Fund(**kwargs)
        self.db.add(fund)
        await self.db.commit()
        await self.db.refresh(fund)
        logger.info("Fund %d created", fund.id)
        return fund

    async def update_fund(self, fund_id: int, **kwargs) -> Optional[Fund]:
        fund = await self.get_fund(fund_id)
        if not fund:
            return None
        for key, value in kwargs.items():
            if hasattr(fund, key) and value is not None:
                setattr(fund, key, value)
        await self.db.commit()
        await self.db.refresh(fund)
        return fund

    async def delete_fund(self, fund_id: int) -> bool:
        fund = await self.get_fund(fund_id)
        if not fund:
            return False
        await self.db.delete(fund)
        await self.db.commit()
        return True
```

- [ ] **Step 2: 实现 SupportedVillageService (supported_village_service.py)**

与 FundService 结构类似，封装 `SupportedVillage` 的基本 CRUD。

- [ ] **Step 3: 实现 BatchService (batch_service.py)**

```python
# backend/app/services/batch_service.py
"""批量操作服务。"""
from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession

class BatchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def batch_create(self, model, items: List[dict]) -> List[Any]:
        instances = [model(**item) for item in items]
        self.db.add_all(instances)
        await self.db.commit()
        return instances

    async def batch_update(self, model, updates: List[dict]) -> int:
        count = 0
        for update in updates:
            instance = await self.db.get(model, update.get("id"))
            if instance:
                for k, v in update.items():
                    if k != "id" and hasattr(instance, k):
                        setattr(instance, k, v)
                count += 1
        await self.db.commit()
        return count

    async def batch_delete(self, model, ids: List[int]) -> int:
        count = 0
        for id_ in ids:
            instance = await self.db.get(model, id_)
            if instance:
                await self.db.delete(instance)
                count += 1
        await self.db.commit()
        return count
```

- [ ] **Step 4: 实现其余桩服务**

- `report_export_service.py`: 委托给 `export_service.py` 的 `ExcelExportService`
- `metrics_service.py`: 委托给 `business_metrics_service.py`
- `async_export_service.py`: 委托给 `chunked_upload_service.py`
- `import_export_history_service.py`: 实现 `ImportExportHistory` 的查询方法

- [ ] **Step 5: 运行测试验证**

```bash
cd backend && python -m pytest tests/ -v -k "not test_system_api" --timeout=60 2>&1 | tail -5
```
Expected: 942 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/fund_service.py \
        backend/app/services/supported_village_service.py \
        backend/app/services/batch_service.py \
        backend/app/services/report_export_service.py \
        backend/app/services/metrics_service.py \
        backend/app/services/async_export_service.py \
        backend/app/services/import_export_history_service.py
git commit -m "feat(P1-6): fill 7 stub services with real implementations

FundService, SupportedVillageService, BatchService now have CRUD methods.
report_export/metrics/async_export/import_export_history delegate to
existing services. Eliminates forced direct-ORM access by other services."
```

---

### Task 7: Fix core/audit.py Direct DB Writes (P1-7)

**Files:**
- Modify: `backend/app/core/audit.py`

- [ ] **Step 1: 查看 audit_service.py 的 create_log 方法**

```bash
grep -n "def create_log\|async def create_log" backend/app/services/audit_service.py
```

确认 `AuditService` 中有可复用的日志创建方法。

- [ ] **Step 2: 重写 core/audit.py 的 record_audit 函数**

```python
# backend/app/core/audit.py (修改后)

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_audit_store: list[dict] = []


async def record_audit(
    user_id: Optional[int] = None,
    action: str = "",
    resource: str = "",
    resource_id: Optional[int] = None,
    details: Optional[dict] = None,
    db: Optional[AsyncSession] = None,
) -> None:
    """记录审计日志。委托给 AuditService 进行数据库写入。"""
    if db is None:
        # 无数据库会话时存入内存（向后兼容）
        _audit_store.append({
            "user_id": user_id, "action": action,
            "resource": resource, "resource_id": resource_id,
            "details": details,
        })
        logger.debug("Audit logged to memory: %s/%s", resource, action)
        return

    from app.services.audit_service import AuditService
    service = AuditService(db)
    await service.create_log(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details,
    )


def get_audit_logs() -> list[dict]:
    """返回内存中的审计日志。"""
    return _audit_store.copy()


def clear_audit_logs() -> None:
    """清空内存中的审计日志。"""
    global _audit_store
    _audit_store = []
```

- [ ] **Step 3: 运行测试验证**

```bash
cd backend && python -m pytest tests/ -v -k "not test_system_api" --timeout=60 2>&1 | tail -5
```
Expected: 942 passed

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/audit.py
git commit -m "refactor(P1-7): delegate core/audit.py DB writes to AuditService

record_audit() now calls AuditService.create_log() when db session is
provided. Eliminates core layer directly writing ORM models."
```

---

### Task 8: Fix project/__init__.py Missing References (P1-8)

**Files:**
- Modify: `backend/app/services/project/__init__.py`

- [ ] **Step 1: 重写 project/__init__.py**

```python
# backend/app/services/project/__init__.py
"""
项目管理域 (Project Domain)

聚合根:
- Project: 帮扶项目
- ProjectMilestone: 项目里程碑
- ProjectDocument: 项目文档

注: project_monitoring_service 和 project_service 暂由顶层服务覆盖。
    在阶段三创建独立的 project 子服务后添加导入。
"""

from app.services.effectiveness_service import EffectivenessService

__all__ = [
    "EffectivenessService",
]
```

- [ ] **Step 2: 验证导入**

```bash
cd backend && python -c "from app.services.project import EffectivenessService; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/project/__init__.py
git commit -m "fix(P1-8): remove non-existent imports from project/__init__.py

project_monitoring_service, project_service, effectiveness_evaluation_service
do not exist. Replace with correct import of EffectivenessService from
services/effectiveness_service.py."
```

---

### Task 9: Create Repository Base + FundRepository (P1-9)

**Files:**
- Create: `backend/app/services/repositories/__init__.py`
- Create: `backend/app/services/repositories/base.py`
- Create: `backend/app/services/repositories/fund_repository.py`

- [ ] **Step 1: 创建 repositories/__init__.py**

```python
# backend/app/services/repositories/__init__.py
from .base import BaseRepository
from .fund_repository import FundRepository

__all__ = ["BaseRepository", "FundRepository"]
```

- [ ] **Step 2: 创建 base.py — BaseRepository**

```python
# backend/app/services/repositories/base.py
"""Repository 基类。领域服务通过 Repository 访问数据库。"""
from typing import Any, Dict, List, Optional, Type
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """泛型 Repository 基类。

    封装 ORM 操作，使领域服务不直接依赖 SQLAlchemy Session/Model。
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, model: Type, id: int) -> Optional[Any]:
        result = await self.db.execute(select(model).where(model.id == id))
        return result.scalar_one_or_none()

    async def list(
        self,
        model: Type,
        *,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Any] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        query = select(model)
        count_query = select(func.count()).select_from(model)

        if filters:
            for col, val in filters.items():
                if val is not None and hasattr(model, col):
                    clause = getattr(model, col) == val
                    query = query.where(clause)
                    count_query = count_query.where(clause)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return {
            "items": list(items),
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def create(self, model: Type, **kwargs) -> Any:
        instance = model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance, **kwargs) -> Any:
        for key, value in kwargs.items():
            if hasattr(instance, key) and value is not None:
                setattr(instance, key, value)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance, *, soft: bool = True) -> None:
        if soft and hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            await self.db.commit()
        else:
            await self.db.delete(instance)
            await self.db.commit()
```

- [ ] **Step 3: 创建 fund_repository.py — FundRepository**

```python
# backend/app/services/repositories/fund_repository.py
"""Fund 聚合根的数据访问层。"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .base import BaseRepository
from app.models.fund import Fund, FundAttachment
from app.models.fund_lifecycle import (
    ProjectFundPhase, BudgetBaseline, FundTransferVoucher,
    FundContract, FundAnomaly, FundSettlement,
)
from app.models.fund_budget import FundTransaction


class FundRepository(BaseRepository):
    """Fund 及其所有子实体的数据访问。

    作为 P1-9 的模式验证，展示 Repository 模式如何封装聚合根查询。
    """

    async def get_with_attachments(self, fund_id: int) -> Optional[Fund]:
        result = await self.db.execute(
            select(Fund)
            .where(Fund.id == fund_id)
            .options(selectinload(Fund.attachments))
        )
        return result.scalar_one_or_none()

    async def get_lifecycle_phases(self, fund_id: int) -> List[ProjectFundPhase]:
        result = await self.db.execute(
            select(ProjectFundPhase)
            .where(ProjectFundPhase.fund_id == fund_id)
            .order_by(ProjectFundPhase.phase_order)
        )
        return list(result.scalars().all())

    async def get_transactions(
        self, fund_id: int, *, date_range: Optional[tuple] = None
    ) -> List[FundTransaction]:
        query = select(FundTransaction).where(FundTransaction.fund_id == fund_id)
        if date_range:
            start, end = date_range
            query = query.where(FundTransaction.created_at.between(start, end))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_budget_baselines(self, fund_id: int) -> List[BudgetBaseline]:
        result = await self.db.execute(
            select(BudgetBaseline).where(BudgetBaseline.fund_id == fund_id)
        )
        return list(result.scalars().all())

    async def get_anomalies(
        self, fund_id: int, *, resolved: Optional[bool] = None
    ) -> List[FundAnomaly]:
        query = select(FundAnomaly).where(FundAnomaly.fund_id == fund_id)
        if resolved is not None:
            query = query.where(FundAnomaly.resolved == resolved)
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

- [ ] **Step 4: 运行测试验证**

```bash
cd backend && python -m pytest tests/ -v -k "not test_system_api" --timeout=60 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/repositories/
git commit -m "feat(P1-9): create Repository base class + FundRepository pattern

Establishes the data access layer mandated by the architecture diagram.
BaseRepository provides generic CRUD. FundRepository demonstrates the
aggregate-root pattern. Used as the foundation for Phase 3 domain services."
```

---

### Phase 1 Gate Check

- [ ] **Gate G1-1: Backend tests 3 consecutive runs**

```bash
cd backend && for i in 1 2 3; do
  echo "=== Run $i ==="
  python -m pytest tests/ -q --tb=short -k "not test_system_api" 2>&1 | tail -3
done
```
Expected: 942 passed × 3

- [ ] **Gate G1-2: Frontend tests**

```bash
cd frontend && npm test -- --run 2>&1 | tail -5
```
Expected: 403 passed

- [ ] **Gate G1-3: flake8**

```bash
cd backend && python -m flake8 app/ --max-line-length=120
```
Expected: 0 errors

- [ ] **Gate G1-4: App startup**

```bash
cd backend && timeout 10 python start.py 2>&1 | grep -i "started\|error" || true
```
Expected: No error

- [ ] **Gate G1-5: Performance — compare against baseline**

Re-run Phase 0 measurement steps. 4 KPI endpoints must be ≤ baseline + 5%.

- [ ] **Phase 1 Complete Commit**

```bash
git commit --allow-empty -m "milestone: Phase 1 complete — all 9 tasks done, gates passed"
```

---

## Phase 2: 数据模型规范化

### Task 10: Unify Model Inheritance to BaseModel (P2-1)

**Files:**
- Create: `backend/alembic/versions/YYYYMMDD_unify_inheritance.py`
- Modify: ~50 model files (those using `Base` directly with manual timestamps)

- [ ] **Step 1: 识别需要统一继承的模型**

```bash
cd backend
# 找出直接继承 Base 但有 created_at/updated_at 列的文件
grep -rn "class.*Base)" app/models/*.py | grep -v "BaseModel\|TimestampMixin\|SoftDelete\|Version" | cut -d: -f1 | sort -u
```

- [ ] **Step 2: 单模型验证 — 先在一个代表性模型上测试 autogenerate 行为**

```bash
cd backend
# 选择一个模型做测试（如 AnnualIncome — 已继承 BaseModel，是理想参考）
# 1. 先运行 autogenerate 看看当前 schema 状态
alembic revision --autogenerate -m "test_inheritance_check"
# 2. 检查生成的迁移文件
cat alembic/versions/*test_inheritance_check*.py
# 3. 如果是空迁移（只有 upgrade/downgrade pass），说明 BaseModel 列定义与手动列一致 → 安全
# 4. 如果生成 ALTER TABLE，说明列定义不一致 → 需先统一列定义再批量切换
# 5. 删除测试迁移
rm alembic/versions/*test_inheritance_check*.py
```

- [ ] **Step 3: 批量修改模型文件** — 将 `Base` 替换为 `BaseModel`（先改模型，再生成迁移验证）

**关键前提**: `BaseModel` 的 `id` 列定义为 `Column(Integer, primary_key=True, index=True, autoincrement=True)`，手动定义的 `id` 列必须与此完全匹配。如果不一致（如缺少 `autoincrement=True`），先统一手动列定义，再切换继承。

对于每个受影响的模型文件：
```python
# 替换前
class SomeModel(Base):
    __tablename__ = "some_table"
    id = Column(Integer, primary_key=True, index=True)        # 确保与 BaseModel.id 完全一致
    created_at = Column(DateTime, default=func.now())          # 确保与 TimestampMixin 一致
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    ...

# 替换后
class SomeModel(BaseModel):
    __tablename__ = "some_table"
    # id, created_at, updated_at 由 BaseModel 提供
    ...
```

- [ ] **Step 4: 逐个修改模型文件** — 将 `Base` 替换为 `BaseModel`，移除重复的 `created_at`/`updated_at`/`id` 列定义。

对于每个受影响的模型文件：
```python
# 替换前
class SomeModel(Base):
    __tablename__ = "some_table"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    ...

# 替换后
class SomeModel(BaseModel):
    __tablename__ = "some_table"
    # id, created_at, updated_at 由 BaseModel 提供
    ...
```

- [ ] **Step 5: 生成最终 Alembic 迁移 — 确认是空操作**

```bash
cd backend && alembic revision --autogenerate -m "unify_inheritance_to_basemodel"
# 检查迁移文件 — 应该只有 pass（列定义现在完全一致）
grep -A5 "def upgrade" alembic/versions/*unify_inheritance*.py
# Expected: 只有 "pass"（无实际 DDL）
```

- [ ] **Step 6: 运行完整测试套件**

```bash
cd backend && python -m pytest tests/ -q --tb=short -k "not test_system_api" 2>&1 | tail -5
```
Expected: 942 passed

- [ ] **Step 7: Commit**

```bash
git add backend/alembic/versions/ backend/app/models/
git commit -m "refactor(P2-1): unify model inheritance to BaseModel

~50 models migrated from Base+manual timestamps to BaseModel.
BaseModel = Base + TimestampMixin + id + to_dict().
Non-destructive Alembic migration included."
```

---

### Task 11: Activate SoftDeleteMixin (P2-2)

**Files:**
- Create: `backend/alembic/versions/YYYYMMDD_soft_delete.py`
- Modify: `backend/app/models/supported_village.py` (SupportedVillage)
- Modify: `backend/app/models/project.py` (Project)
- Modify: `backend/app/models/fund.py` (Fund)

- [ ] **Step 1: 修改 base.py — 确保 SoftDeleteMixin 包含索引指导**

```python
# backend/app/models/base.py

class SoftDeleteMixin:
    """软删除混入。添加 is_deleted + deleted_at 列。

    使用此混入的模型需在 Alembic 迁移中创建部分索引：
    CREATE INDEX idx_{table}_is_deleted ON {table}(is_deleted) WHERE is_deleted = 0
    """
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
```

- [ ] **Step 2: 修改 SupportedVillage 继承**

```python
# 替换前
class SupportedVillage(Base, TimestampMixin):

# 替换后
class SupportedVillage(BaseModel, SoftDeleteMixin):
```

- [ ] **Step 3: 对 Project 和 Fund 做同样修改**

- [ ] **Step 4: 生成 Alembic 迁移**

```bash
cd backend && alembic revision --autogenerate -m "add_soft_delete_to_core_entities"
```

在迁移文件中手动添加性能索引：
```python
op.execute("CREATE INDEX IF NOT EXISTS idx_supported_villages_is_deleted ON supported_villages(is_deleted) WHERE is_deleted = 0")
op.execute("CREATE INDEX IF NOT EXISTS idx_projects_is_deleted ON projects(is_deleted) WHERE is_deleted = 0")
op.execute("CREATE INDEX IF NOT EXISTS idx_funds_is_deleted ON funds(is_deleted) WHERE is_deleted = 0")
```

- [ ] **Step 5: 运行测试 + 验证迁移可逆**

```bash
cd backend
alembic upgrade head
python -m pytest tests/ -q --tb=short -k "not test_system_api" 2>&1 | tail -5
alembic downgrade -1
alembic upgrade head
```
Expected: 942 passed + 迁移正向/反向均成功

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/base.py backend/app/models/supported_village.py \
        backend/app/models/project.py backend/app/models/fund.py \
        backend/alembic/versions/
git commit -m "feat(P2-2): activate SoftDeleteMixin for SupportedVillage, Project, Fund

Business justification: data recovery (accidental deletion), audit compliance
(financial data must not be physically deleted), sync ambiguity resolution.
Partial indexes on is_deleted ensure query performance."
```

---

### Task 12: Activate VersionMixin (P2-3)

**Files:**
- Create: `backend/alembic/versions/YYYYMMDD_version_mixin.py`
- Modify: `backend/app/models/user.py` (替换手动 token_version)
- Modify: `backend/app/models/fund.py` (替换手动 budget_version)
- Modify: `backend/app/models/base.py` (确保 VersionMixin 可用)

- [ ] **Step 1: 确认 VersionMixin 定义**

```python
# backend/app/models/base.py
class VersionMixin:
    """乐观锁版本号。每次更新递增。"""
    version = Column(Integer, default=1, nullable=False)
```

- [ ] **Step 2: 修改 User 模型**

```python
# 替换前
class User(Base):
    ...
    token_version = Column(Integer, default=1)

# 替换后
class User(Base, VersionMixin):
    ...
    @property
    def token_version(self):
        return self.version  # backward compat alias
```

- [ ] **Step 3: 修改 Fund 模型**

```python
# 替换前
class Fund(BaseModel):
    ...
    budget_version = Column(Integer, default=1)

# 替换后
class Fund(BaseModel, VersionMixin):
    ...
    @property
    def budget_version(self):
        return self.version  # backward compat alias
```

- [ ] **Step 4: 生成 Alembic 迁移 + 测试**

```bash
cd backend
alembic revision --autogenerate -m "unify_version_to_mixin"
alembic upgrade head
python -m pytest tests/ -q --tb=short -k "not test_system_api" 2>&1 | tail -5
alembic downgrade -1
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/ backend/alembic/versions/
git commit -m "refactor(P2-3): activate VersionMixin — unify optimistic locking

Replaces manual token_version/budget_version columns with standardized
VersionMixin. Backward-compatible property aliases preserved.
Business justification: data sync conflict detection via version comparison."
```

---

### Task 13: Remove Redundant project_id from fund_lifecycle Models (P2-4)

**Files:**
- Create: `backend/alembic/versions/YYYYMMDD_remove_dual_fk.py`
- Modify: `backend/app/models/fund_lifecycle.py` (8 models)

- [ ] **Step 1: 为每个生命周期模型添加 project_id property**

对 `fund_lifecycle.py` 中的 8 个模型（ProjectFundPhase, BudgetBaseline, FundTransferVoucher, FundContract, FundContractPayment, FundAnomaly, FundSettlement, BudgetVersion）：

```python
# 每个模型添加
@property
def project_id(self):
    """通过 fund.project_id 间接获取，避免冗余 FK。"""
    return self.fund.project_id if self.fund else None
```

- [ ] **Step 2: 映射入站 FK 依赖（关键安全步骤）**

在删除 `project_id` 列之前，必须先了解哪些表（包括模型外的表）引用了这些 lifecycle 表的 `project_id`：

```bash
cd backend
python -c "
import sqlite3
conn = sqlite3.connect('data/rural_revitalization.db')
cursor = conn.cursor()
# 检查 8 个 lifecycle 表的入站 FK 引用
tables = ['project_fund_phases', 'budget_baselines', 'fund_transfer_vouchers',
          'fund_contracts', 'fund_contract_payments', 'fund_anomalies',
          'fund_settlements', 'budget_versions']
for table in tables:
    cursor.execute(f'PRAGMA foreign_key_list({table})')
    refs = cursor.fetchall()
    if refs:
        print(f'{table} is referenced by:')
        for ref in refs:
            print(f'  <- {ref[2]}.{ref[3]} (on_delete={ref[5]})')
    else:
        print(f'{table}: no inbound FK references')
conn.close()
"
```

记录所有入站 FK 引用，在迁移中显式处理每个引用（NOT just CASCADE）。

- [ ] **Step 3: 生成 Alembic 迁移 — 逐表安全重建**

**重要**: 以 1 个表为一批（而非 8 个表一批），降低事务复杂度和回滚风险。

```bash
cd backend && alembic revision --autogenerate -m "remove_redundant_project_id_fks"
```

手动编辑迁移文件，使用 SQLite 安全的列删除模板（每个表独立执行）：

```python
def _sqlite_drop_column(engine, table_name, drop_column, preserved_columns, fks_to_disable=None):
    """SQLite 安全删除列: CREATE new → COPY data → DROP old → RENAME new → RESTORE indexes"""
    preserved_col_names = [c.split()[0] for c in preserved_columns]
    col_list = ', '.join(preserved_columns)

    with engine.begin() as conn:
        # 0. 禁用 FK 检查（SQLite 允许，但需手动管理引用完整性）
        conn.execute(text("PRAGMA foreign_keys = OFF"))

        # 1. 创建新表（不含目标列）
        conn.execute(text(f"CREATE TABLE {table_name}_new ({col_list})"))

        # 2. 复制数据
        conn.execute(text(
            f"INSERT INTO {table_name}_new ({', '.join(preserved_col_names)}) "
            f"SELECT {', '.join(preserved_col_names)} FROM {table_name}"
        ))

        # 3. 删除旧表
        conn.execute(text(f"DROP TABLE {table_name}"))

        # 4. 重命名新表
        conn.execute(text(f"ALTER TABLE {table_name}_new RENAME TO {table_name}"))

        # 5. 重建索引和 FK（从 preserved_columns 中提取 FK 定义）

        conn.execute(text("PRAGMA foreign_keys = ON"))
```

每个 lifecycle 表只需删除 `project_id` 列（和其 FK 约束），其他列保持不变。
处理顺序（按依赖关系，子表先处理）：
1. `fund_contract_payments`（最深层子表）
2. `fund_anomalies`
3. `fund_settlements`
4. `fund_transfer_vouchers`
5. `fund_contracts`
6. `budget_versions`
7. `budget_baselines`
8. `project_fund_phases`

- [ ] **Step 4: 更新所有引用 project_id 的查询**

```bash
grep -rn "\.project_id" backend/app/ --include="*.py" | grep -v ".pyc" | grep -v "fund\.project_id\|funds\.project_id"
```

将 `lifecycle_model.project_id` 的引用改为通过 `fund.project_id` 获取（如果需要，先加载 fund 关系）。

- [ ] **Step 5: 运行测试 + 验证迁移**

```bash
cd backend
alembic upgrade head
python -m pytest tests/ -q --tb=short -k "not test_system_api" 2>&1 | tail -5
# 数据完整性检查
python -c "
from app.core.database import get_db
# verify no orphan references
"
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/fund_lifecycle.py backend/alembic/versions/
git commit -m "refactor(P2-4): remove redundant project_id FK from 8 lifecycle models

FundTransferVoucher, FundContract, FundAnomaly etc. now access project_id
via self.fund.project_id property. Eliminates dual-FK consistency risk.
Non-destructive migration with table rebuild for SQLite."
```

---

### Task 14: Dedup Annual Data Tables (P2-5)

**Files:**
- Create: `backend/alembic/versions/YYYYMMDD_dedup_annual.py`
- Modify: 引用 AnnualIncome/AnnualIndustry/AnnualInfrastructure/AnnualPopulation 的 API 文件

- [ ] **Step 1: 编写数据迁移脚本**

```python
# backend/alembic/versions/YYYYMMDD_dedup_annual.py

def upgrade():
    # 1. 将 AnnualIncome → VillageIncome 中缺失的年份数据合并
    op.execute("""
        INSERT OR IGNORE INTO village_incomes (village_id, year, amount, ...)
        SELECT village_id, year, amount, ...
        FROM annual_income
        WHERE (village_id, year) NOT IN (
            SELECT village_id, year FROM village_incomes
        )
    """)
    # 类似地处理其他 3 对表...

    # 2. 删除 4 个年度数据表
    op.drop_table("annual_income")
    op.drop_table("annual_industry")
    op.drop_table("annual_infrastructure")
    op.drop_table("annual_population")
```

- [ ] **Step 2: 更新引用 Annual* 模型的 API 端点**

```bash
grep -rn "AnnualIncome\|AnnualIndustry\|AnnualInfrastructure\|AnnualPopulation" backend/app/api/ --include="*.py"
```

将查询改为使用对应的权威表（VillageIncome, IndustrySupport, InfrastructureImprovement, VillagePopulation）。

- [ ] **Step 3: 运行测试 + 验证数据完整性**

```bash
cd backend
alembic upgrade head
python -m pytest tests/ -q --tb=short -k "not test_system_api"
# 数据完整性检查脚本
```

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/ backend/app/models/__init__.py backend/app/api/
git commit -m "refactor(P2-5): dedup annual data — remove Annual* tables

Merge AnnualIncome→VillageIncome, AnnualIndustry→IndustrySupport,
AnnualInfrastructure→InfrastructureImprovement, AnnualPopulation→VillagePopulation.
Removes 4 redundant tables. Data migration preserves existing records."
```

---

### Phase 2 Gate Check

- [ ] **Gate G2-1: All G1 conditions met**

- [ ] **Gate G2-2: Alembic forward + reverse**

```bash
cd backend
alembic downgrade -1 && alembic upgrade head && echo "Migration reversible: OK"
```

- [ ] **Gate G2-3: Data integrity verification**

```bash
cd backend && python -c "
import asyncio
from app.core.database import async_session
async def check():
    async with async_session() as db:
        # Check no orphan lifecycle records
        from sqlalchemy import text
        orphans = await db.execute(text('SELECT COUNT(*) FROM project_fund_phases WHERE fund_id NOT IN (SELECT id FROM funds)'))
        print(f'Orphan lifecycle records: {orphans.scalar()}')
asyncio.run(check())
"
```

- [ ] **Gate G2-4: Performance ≤ baseline + 10%**

- [ ] **Phase 2 Complete Commit**

```bash
git commit --allow-empty -m "milestone: Phase 2 complete — data model normalized, all gates passed"
```

---

## Phase 3: 服务层重构 & Fat Controller 拆分

### Task 15: Create 7 Fund Lifecycle Phase Services (P3-2)

**Files:**
- Create: `backend/app/services/funding/phase_init_service.py`
- Create: `backend/app/services/funding/phase_budget_service.py`
- Create: `backend/app/services/funding/phase_transfer_service.py`
- Create: `backend/app/services/funding/phase_contract_service.py`
- Create: `backend/app/services/funding/phase_anomaly_service.py`
- Create: `backend/app/services/funding/phase_settlement_service.py`
- Create: `backend/app/services/funding/phase_verification_service.py`
- Modify: `backend/app/api/v1/fund_lifecycle.py`

- [ ] **Step 1: 分析 fund_lifecycle.py 的端点分组**

```bash
grep -n "@router\.\(get\|post\|put\|delete\|patch\)" backend/app/api/v1/fund_lifecycle.py
```

按照路径前缀将 44 个端点分为 7 组。

- [ ] **Step 2: 为每个阶段创建服务文件**

每个 phase service 遵循统一的接口模式：

```python
# services/funding/phase_init_service.py 示例
"""Phase 1: 项目资金阶段初始化服务。"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.repositories.fund_repository import FundRepository


class PhaseInitService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FundRepository(db)

    async def initialize_phase(self, fund_id: int, phase_data: dict) -> dict:
        fund = await self.repo.get_with_attachments(fund_id)
        if not fund:
            raise ValueError(f"Fund {fund_id} not found")
        # phase-specific business logic extracted from fund_lifecycle.py
        ...

    async def get_phases(self, fund_id: int) -> list:
        return await self.repo.get_lifecycle_phases(fund_id)

    # ... other phase-specific methods
```

- [ ] **Step 3: 重写 fund_lifecycle.py — 路由委托给服务**

```python
# fund_lifecycle.py (重构后)

@router.get("/phases/{fund_id}")
async def list_phases(fund_id: int, db: AsyncSession = Depends(get_db)):
    service = PhaseInitService(db)
    phases = await service.get_phases(fund_id)
    return {"data": phases}
```

每个端点从内联业务逻辑变为 ~5 行委托代码。目标：从 ~1926 行缩减到 ~400 行。

- [ ] **Step 4: 逐个端点验证 — 使用 curl 确保响应格式不变**

对 44 个端点逐一调用，与重构前的响应对比。

- [ ] **Step 5: Commit (分批提交，每个 phase 一个 commit)**

```bash
git add backend/app/services/funding/ backend/app/api/v1/fund_lifecycle.py
git commit -m "refactor(P3-2): extract 7 fund lifecycle phase services

Split 1926-line fund_lifecycle.py into:
- phase_init_service (Phase 1: initialization)
- phase_budget_service (Phase 2: budget baselines)
- phase_transfer_service (Phase 3: transfer vouchers)
- phase_contract_service (Phase 4: contracts)
- phase_anomaly_service (Phase 5: anomaly detection)
- phase_settlement_service (Phase 6: settlement)
- phase_verification_service (Phase 7: asset verification)

API endpoints unchanged — 44 routes preserved with same signatures."
```

---

### Task 16: Extract Sub-services from projects.py (P3-3)

**Files:**
- Create: `backend/app/services/fund_health_service.py`
- Create: `backend/app/services/file_management_service.py`
- Modify: `backend/app/api/v1/projects.py`

- [ ] **Step 1: 创建 fund_health_service.py**

从 `projects.py` 中提取 `_batch_get_fund_health_fields` 和相关健康评分逻辑到独立服务。

- [ ] **Step 2: 创建 file_management_service.py**

从 `projects.py` 中提取文件上传/下载/安全检查逻辑到独立服务。

```python
# backend/app/services/file_management_service.py
class FileManagementService:
    async def upload_file(self, project_id: int, file: bytes, filename: str) -> ProjectFile: ...
    async def download_file(self, file_id: int) -> tuple[bytes, str]: ...
    async def delete_file(self, file_id: int) -> bool: ...
    async def check_security(self, file_bytes: bytes, filename: str) -> bool: ...
```

- [ ] **Step 3: 重写 projects.py — 委托给子服务**

将 Excel 模板生成委托给 `ExcelTemplateService`（已存在）。
将批量导入委托给 `ExcelImporterService`（已存在）。
将审计差异委托给 `AuditEnhancementService`（已存在）。
将工作日志委托给 `WorkLogService`（已存在）。

- [ ] **Step 4: 运行测试 + 验证端点**

```bash
cd backend && python -m pytest tests/ -q --tb=short -k "not test_system_api"
```
Expected: 942 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/fund_health_service.py \
        backend/app/services/file_management_service.py \
        backend/app/api/v1/projects.py
git commit -m "refactor(P3-3): extract fund_health + file_management from projects.py

Extracts ~700 lines of inline logic from 2129-line projects.py into:
- FundHealthService: health score calculation, fund event triggers
- FileManagementService: upload/download/security checks
Delegates to existing ExcelTemplateService, ExcelImporterService,
AuditEnhancementService, WorkLogService."
```

---

### Task 17: Extract Assessment Services (P3-4)

**Files:**
- Create: `backend/app/services/assessment/__init__.py`
- Create: `backend/app/services/assessment/scoring_service.py`
- Create: `backend/app/services/assessment/anomaly_service.py`
- Create: `backend/app/services/assessment/trend_service.py`
- Modify: `backend/app/api/v1/assessment.py`

- [ ] **Step 1: 创建 assessment/__init__.py**

```python
# backend/app/services/assessment/__init__.py
from .scoring_service import ScoringService
from .anomaly_service import AnomalyService
from .trend_service import TrendService

__all__ = ["ScoringService", "AnomalyService", "TrendService"]
```

- [ ] **Step 2: 提取 ScoringService**

从 `assessment.py` 的 `_calculate_village_score_batch` 和相关加权计算逻辑提取到 `scoring_service.py`。

- [ ] **Step 3: 提取 AnomalyService**

从 `assessment.py` 的三维异常检测逻辑（收入下降、项目逾期、预算超支）提取到 `anomaly_service.py`。

- [ ] **Step 4: 提取 TrendService**

从 `assessment.py` 的线性回归趋势预测逻辑提取到 `trend_service.py`。

- [ ] **Step 5: 重写 assessment.py — 路由委托**

```python
@router.get("/village/{village_id}/score")
async def get_village_score(village_id: int, db: AsyncSession = Depends(get_db)):
    service = ScoringService(db)
    score = await service.calculate_score(village_id)
    return {"data": score}
```

- [ ] **Step 6: 运行测试 + Commit**

```bash
cd backend && python -m pytest tests/ -q --tb=short -k "not test_system_api"
git add backend/app/services/assessment/ backend/app/api/v1/assessment.py
git commit -m "refactor(P3-4): extract assessment services — Scoring, Anomaly, Trend

Extracts 441-line inline scoring engine from assessment.py into:
- ScoringService: weighted scoring, radar comparison
- AnomalyService: income drop, overdue projects, budget overrun detection
- TrendService: linear regression prediction"
```

---

### Task 18: Evaluate DDD Domain Layer Fate (P3-1 Decision)

**Files:**
- Evaluate: `backend/app/services/domain/` (28 files)

- [ ] **Step 1: AI 评估 — 生成每个 domain/ 文件的质量报告**

```bash
cd backend
for f in $(find app/services/domain -name "*.py" -not -name "__init__.py" | sort); do
  echo "=== $f ==="
  wc -l "$f"
  grep -c "class\|def" "$f"
  # Check if imports match current model structure
done
```

- [ ] **Step 2: 人工决策 — 基于评估报告决定激活(P3-1a)或删除(P3-1b)**

评估维度：
1. 聚合设计是否与当前 Schema 匹配？
2. 值对象是否仍适用？
3. 领域服务中的业务逻辑是否与 fat controllers 中的逻辑一致？

- [ ] **Step 3a: 如激活 — 创建 Village/Project/School/Approval Repository**

```bash
# 创建 4 个额外的 Repository
touch backend/app/services/repositories/village_repository.py
touch backend/app/services/repositories/project_repository.py
touch backend/app/services/repositories/school_repository.py
touch backend/app/services/repositories/approval_repository.py
```

每新增一个 commit：
```bash
git add backend/app/services/repositories/
git commit -m "feat(P3-1a): create Village/Project/School/Approval repositories"
```

- [ ] **Step 3b: 如删除 — 移除 28 个文件**

```bash
rm -rf backend/app/services/domain/
git add backend/app/services/domain/
git commit -m "refactor(P3-1b): remove abandoned DDD domain layer (28 files, zero usage)"
```

---

### Task 19: Split Oversized Services (P3-5)

**Files:**
- Modify: `backend/app/services/data_validator_service.py` (1174 lines)
- Modify: `backend/app/services/data_package_service.py` (994 lines)
- Modify: `backend/app/services/data_sync_service.py` (882 lines)

- [ ] **Step 1: 方法分析 — 确定每个 oversized service 的拆分边界**

在执行任何拆分之前，先分析每个服务的方法归属：

```bash
cd backend
echo "=== data_validator_service.py methods ==="
grep -n "def \|class " app/services/data_validator_service.py

echo "=== data_package_service.py methods ==="
grep -n "def \|class " app/services/data_package_service.py

echo "=== data_sync_service.py methods ==="
grep -n "def \|class " app/services/data_sync_service.py
```

根据方法名前缀和职责，手动分组到新文件：

| 源文件 | 方法组 | 目标文件 |
|--------|--------|----------|
| `data_validator_service.py` | `validate_file_*`, `check_format_*` | `services/validation/file_validator.py` |
| `data_validator_service.py` | `validate_row_*`, `validate_field_*`, `check_id_*`, `check_date_*`, `check_email_*`, `check_phone_*` | `services/validation/row_validator.py` |
| `data_validator_service.py` | `sanitize_*`, `clean_*`, `normalize_*` | `services/validation/sanitizer.py` |
| `data_package_service.py` | `create_*`, `get_*`, `update_*`, `delete_*`, `list_*` | 保留在原文件（CRUD） |
| `data_package_service.py` | `encrypt_*`, `decrypt_*` | → 委托给 `encryption_service.py`（已存在） |
| `data_package_service.py` | `resolve_conflict_*`, `merge_*` | → 委托给 `smart_conflict_resolver.py`（已存在） |
| `data_sync_service.py` | `export_incremental_*`, `compute_delta_*` | `services/data_sync/incremental_exporter.py` |

将此映射记录到拆分计划注释中，作为编码时的参考。

- [ ] **Step 2: 拆分 data_validator_service.py**

提取为 3 个子服务：
- `services/validation/file_validator.py` — 文件格式验证
- `services/validation/row_validator.py` — 行级验证、ID校验、日期/邮箱/电话
- `services/validation/sanitizer.py` — 输入清洗

- [ ] **Step 3: 拆分 data_package_service.py**

提取为 3 个关注点：
- 保留：CRUD 操作
- 委托给 `encryption_service.py`: 加密/解密（已存在，直接委托）
- 委托给 `smart_conflict_resolver.py`: 冲突解决（已存在，直接委托）

- [ ] **Step 4: 拆分 data_sync_service.py**

提取增量导出逻辑到：
- `services/data_sync/incremental_exporter.py`

- [ ] **Step 5: 运行测试**

```bash
cd backend && python -m pytest tests/ -q --tb=short
```

- [ ] **Step 6: Commit (每个服务拆分一个 commit)**

---

### Task 20: Split analytics_service.py (P3-6) and message_template_service.py (P3-7)

**Files:**
- Modify: `backend/app/services/analytics_service.py` (707 lines)
- Modify: `backend/app/services/message_template_service.py` (846 lines)

- [ ] **Step 1: 拆分 analytics_service.py**

按报表类型提取：
- `services/analytics/dashboard_analytics.py` — 仪表盘概览
- `services/analytics/village_analytics.py` — 村庄统计
- `services/analytics/project_analytics.py` — 项目统计

- [ ] **Step 2: 拆分 message_template_service.py**

- 保留：模板 CRUD
- 提取：默认模板数据 → `services/message_template_defaults.py`

- [ ] **Step 3: 运行测试 + Commit**

---

### Phase 3 Gate Check

- [ ] **Gate G3-1: All G2 conditions met**

- [ ] **Gate G3-2: Manual verification of fund_lifecycle 44 endpoints**

对每个端点执行 curl 请求，比较响应与重构前是否一致。

- [ ] **Gate G3-3: Manual verification of projects 21 endpoints**

- [ ] **Gate G3-4: New service test coverage ≥ 80%**

```bash
cd backend && python -m pytest tests/ --cov=app/services/funding --cov=app/services/assessment --cov-report=term-missing
```

- [ ] **Gate G3-5: Performance ≤ baseline + 20%**

- [ ] **Phase 3 Complete Commit**

```bash
git commit --allow-empty -m "milestone: Phase 3 complete — architecture optimization done"
```

---

## Post-Implementation

### Task 21: Documentation Update

- [ ] Update `docs/README.md` with architecture optimization summary
- [ ] Update `MEMORY.md` with optimization results
- [ ] Update `CLAUDE.md` if new file patterns were introduced

```bash
git add docs/ MEMORY.md CLAUDE.md
git commit -m "docs: update documentation with architecture optimization results"
```

### Task 22: Final Verification

- [ ] **Full test suite**

```bash
cd backend && python -m pytest tests/ -v   # 942 passed
cd frontend && npm test -- --run             # 403 passed
```

- [ ] **Code quality**

```bash
cd backend && python -m flake8 app/ --max-line-length=120   # 0 errors
cd frontend && npx vue-tsc --noEmit 2>&1 | grep "^Found"   # 0 errors (new files only)
```

- [ ] **System health score**

```bash
cd backend && python -c "
from app.services.health_service import HealthService
# Run comprehensive health check
"
```

- [ ] **Final commit + tag**

```bash
git tag -a v1.2.0-arch-optimized -m "Architecture optimization: Phase 1-3 complete"
```

---

## Summary

| Phase | Tasks | New Files | Modified Files | Deleted Files | Risk |
|-------|-------|-----------|----------------|---------------|------|
| Phase 0 | 1 | 1 | 0 | 0 | None |
| Phase 1 | 9 | 5 | 17 | 7 | Low |
| Phase 2 | 5 | 5 | ~53 | 4 | Medium |
| Phase 3 | 6 (covering 7 spec tasks: P3-1~P3-7, P3-6+P3-7 merged into Task 20) | 21 | 12 | ~28 (if deleted) | Medium-High |
| **Total** | **20** | **32** | **~82** | **~39** | — |

**Note**: Phase 3 has 6 plan tasks covering 7 spec items — Task 20 handles both P3-6 (analytics split) and P3-7 (message template split) since both are low-risk extractions with similar patterns.

**Estimated effort**: 3-5 working days (Phase 1: 1 day, Phase 2: 1-2 days, Phase 3: 2-3 days)
