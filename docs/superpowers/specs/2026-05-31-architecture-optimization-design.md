# 架构优化设计文档 — 军队乡村振兴管理系统

> **日期**: 2026-05-31
> **版本**: v1.0
> **状态**: 设计审批中
> **作者**: AI 架构分析 + 人工审批

---

## 1. 动机与背景

### 1.1 当前状态

系统规模：
- 54 个 SQLAlchemy 模型（86+ 数据表）
- 76 个服务文件（7 个子目录）
- 85 个 API 文件（644 条路由）
- 127 个前端页面
- 部署形态：单机 Electron + SQLite WAL + Vue3 SPA

### 1.2 通过深度代码扫描发现的核心问题

通过三个并行探索代理（共扫描 208 个文件）发现：

**数据模型层**:
- **Village-Fund-Project 三角紧耦合**: `fund_lifecycle.py` 中 8 个模型同时对 `funds.id` 和 `projects.id` 持有双向外键。Fund 已通过 `fund.project_id` 关联 Project，生命周期子表却冗余存储 `project_id`，存在数据不一致风险。
- **User 是"上帝模型"**: ~40 个模型通过外键指向 User 表（审计日志、历史记录、创建者追踪），任何 User 表结构变更影响面极大。
- **继承模式不一致**: 3 种模式混用（`Base` + 手动时间戳、`Base + TimestampMixin`、`BaseModel`），约 40+ 模型重复声明 `created_at`/`updated_at` 列。
- **未使用的 Mixin**: `SoftDeleteMixin` 和 `VersionMixin` 在 `base.py` 中定义但从未被任何模型使用。

**服务层**:
- **7 个桩服务**: `fund_service.py`、`supported_village_service.py`、`batch_service.py`、`report_export_service.py`、`metrics_service.py`、`async_export_service.py`、`import_export_history_service.py` 返回 `[]`/`None`/`{}`，迫使其他服务直接访问 ORM 模型。
- **重复 RBAC 实现**（CRITICAL）: `core/permissions.py` 和 `services/rbac_service.py` 各自维护完整的权限枚举和角色映射逻辑。
- **最严重分层违例**: `version_service.py:342` 从 `app.main`（应用入口点）导入 `_migrate_missing_columns`。
- **调度层依赖 HTTP 层**: `backup_scheduler.py` 从 `app.api.v1.system_config` 和 `app.api.v1.data.analytics` 导入。
- **服务依赖 FastAPI 类型**: `excel_importer_service.py` 方法签名使用 `fastapi.UploadFile`，无法在 CLI/后台任务中使用。
- **废弃 DDD 层**: `services/domain/` 下 28 个文件（聚合、仓储、领域服务、值对象），零引用，完全未接入应用。

**API 层**:
- **`fund_lifecycle.py`**（CRITICAL）: 44 个端点，~1926 行，7 阶段生命周期逻辑（初始化、推进、预算锁定、合规检查、合同管理、异常检测、结算）全部内联在路由处理器中，零服务委托。
- **`projects.py`**: 21 个路由，2129 行，内嵌 Excel 模板生成（500+ 行 openpyxl 代码）、导入解析、健康评分、文件管理、审计差异追踪、工作日志记录、仪表盘缓存失效。
- **`assessment.py`**: 441 行内嵌完整评分引擎、线性回归趋势预测、三维异常检测（收入下降/项目逾期/预算超支）。
- **死代码**: `data/` 顶层 7 个文件与 `data/data/` 子目录重复，`data/__init__.py` 仅委托到子目录。

### 1.3 约束条件

- **严格向后兼容**: 所有 API 端点签名不变、数据库 Schema 不可破坏性变更（Phase 2 需创建非破坏性迁移）、前端接口不变。
- **军队安全标准**: 数据加密、权限隔离、审计日志不可削弱。
- **单机运行**: SQLite WAL 模式，不可引入需要外部服务的依赖。
- **国产信创兼容**: 麒麟 Linux、国产 CPU 架构需保持兼容。
- **现有测试必须全部通过**: 后端 942 测试 + 前端 403 测试。

---

## 2. 设计方案

### 2.1 总体架构目标

```
┌─────────────────────────────────────────────┐
│              API Layer (Thin)                │
│  路由处理: 仅验证→调用→格式化响应           │
├─────────────────────────────────────────────┤
│          Service Layer (Domain)              │
│  领域服务: 业务逻辑、事务管理、权限检查     │
│  ┌──────────┬──────────┬──────────────────┐ │
│  │ Village  │  Fund    │  Project  •••    │ │
│  │ Domain   │  Domain  │  Domain          │ │
│  └──────────┴──────────┴──────────────────┘ │
├─────────────────────────────────────────────┤
│          Repository Layer                    │
│  数据访问: CRUD 封装、查询优化、缓存        │
├─────────────────────────────────────────────┤
│          Core Layer (Pure Infrastructure)    │
│  安全、配置、事件总线、日志、加密           │
└─────────────────────────────────────────────┘
```

目标分层规则：
- **API 层**: 仅做请求验证、调用服务、格式化响应。禁止直接 ORM 查询。
- **Service 层**: 包含所有业务逻辑。通过 Repository 访问数据。不依赖 HTTP 类型。
- **Repository 层**: 封装 ORM 操作。领域服务只通过 Repository 访问数据库。
- **Core 层**: 纯基础设施。不包含业务逻辑。

### 2.2 三阶段路线图

#### 阶段一：消除分层违例 & 清理死代码（低风险）

| ID | 任务 | 文件 | 变更类型 |
|----|------|------|----------|
| P1-1 | 提取 `_migrate_missing_columns` 到 core | `version_service.py`、新文件 `core/migration_helper.py` | 内部重构 |
| P1-2 | 解耦 backup_scheduler 与 API 层 | `backup_scheduler.py`、新文件 `core/constants.py` | 提取常量/函数 |
| P1-3 | 去 FastAPI 化 excel_importer | `excel_importer_service.py`、`import_export/import_data.py` | 接口重构 |
| P1-4 | 合并重复 RBAC 实现 | `core/permissions.py`、`services/rbac_service.py` | 统一到服务 |
| P1-5 | 清理 data/ 死代码 | `data/` 顶层 7 文件（analytics.py, dashboard.py, statistics.py, reports.py, data_reports.py, data_packages.py, data_quality.py — 均被 `data/data/` 子目录覆盖） | 删除/废弃警告 |
| P1-6 | 填充 7 个桩服务 | `fund_service.py` 等 | 实现基本CRUD |
| P1-7 | 修复 core/audit.py 直写DB | `core/audit.py`、`services/audit_service.py` | 委托调用 |
| P1-8 | 修复 project/__init__.py 缺失引用 | `project/__init__.py` | 修正导入 |
| P1-9 | 创建 Repository 基类和 FundRepository | 新文件 `services/repositories/` | 建立数据访问模式 |

**P1-7 详细设计（core/audit.py 直写DB）**:

当前问题：`core/audit.py` 的 `record_audit()` 函数直接通过 ORM 模型写数据库：
```python
# core/audit.py (当前实现)
async def record_audit(db: AsyncSession, user_id: int, action: str, ...):
    log = AuditLog(user_id=user_id, action=action, ...)
    db.add(log)
    await db.commit()
```

修复后：委托给已存在的 `AuditService`：
```python
# core/audit.py (修复后)
from app.services.audit_service import AuditService

async def record_audit(db: AsyncSession, user_id: int, action: str, ...):
    service = AuditService(db)
    await service.create_log(user_id=user_id, action=action, ...)
```
`AuditService.create_log()` 已存在于 `audit_service.py`（483行），`core/audit.py` 改为薄封装。

**P1-8 详细设计（project/__init__.py 缺失引用）**:

当前 `services/project/__init__.py` 引用 3 个不存在的模块：
```python
from .project_monitoring_service import ProjectMonitoringService       # 文件不存在
from .project_service import ProjectService                           # 文件不存在
from .effectiveness_evaluation_service import EffectivenessService    # 文件不存在
```
（注意：`effectiveness_service.py` 存在于顶层 `services/`，但不在 `services/project/` 下）

修复：移除不存在的引用，从正确位置导入：
```python
from app.services.effectiveness_service import EffectivenessService
# project_monitoring_service 和 project_service 暂由顶层服务覆盖，
# 在阶段三创建独立的 project 子服务后再添加
```

**P1-9 详细设计（Repository 基类，解决架构图中 Repository Layer 零实现问题）**:

建立数据访问模式，为阶段三领域服务迁移奠定基础：
```python
# services/repositories/__init__.py
from .base import BaseRepository
from .fund_repository import FundRepository

# services/repositories/base.py
class BaseRepository:
    """Repository 基类。
    领域服务通过 Repository 访问数据库，不直接使用 ORM Session/Model。
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, model, id): ...
    async def list(self, model, *, filters=None, order_by=None, page=None, page_size=None): ...
    async def create(self, model, **kwargs): ...
    async def update(self, instance, **kwargs): ...
    async def delete(self, instance, *, soft: bool = True): ...
    async def count(self, model, *, filters=None): ...

# services/repositories/fund_repository.py
class FundRepository(BaseRepository):
    """Fund 聚合根数据访问。封装所有 Fund + 生命周期子表的查询逻辑。"""
    async def get_with_attachments(self, fund_id: int) -> Fund: ...
    async def get_lifecycle_phases(self, fund_id: int) -> list[ProjectFundPhase]: ...
    async def get_transactions(self, fund_id: int, *, date_range=None) -> list[FundTransaction]: ...
    async def get_budget_baselines(self, fund_id: int) -> list[BudgetBaseline]: ...
    async def get_anomalies(self, fund_id: int, *, resolved: bool = None): ...
```

仅创建基类 + FundRepository 作为模式验证。其余领域（Village、Project、School 等）的 Repository 在阶段三按需创建。这确保了架构图定义与实现任务的一致性。

**风险**: 极低。所有变更都是内部重构，API 签名不变。
**验证**: 后端 942 测试全部通过；flake8 0 错误。

#### 阶段二：数据模型规范化（中风险）

| ID | 任务 | 文件 | 变更类型 |
|----|------|------|----------|
| P2-1 | 统一继承到 BaseModel | ~50 个模型文件 | Alembic 迁移 |
| P2-2 | 激活 SoftDeleteMixin | `SupportedVillage`、`Project`、`Fund` | Alembic 迁移 |
| P2-3 | 激活 VersionMixin | User、Fund 手动 version 列替换 | Alembic 迁移 |
| P2-4 | 移除 fund_lifecycle 冗余 project_id | 8 个生命周期模型 | Alembic 迁移 |
| P2-5 | 去重年度数据表 | Annual* 系列 vs *Support 系列 | 选择权威来源 |

**P2-5 详细设计（去重年度数据表，具体表清单）**:

系统中存在两组按年份存储的帮扶村数据，它们存在重叠：

| 年度数据表 (Annual*) | 对应业务表 (*Support) | 重叠字段 | 权威来源 |
|-----------------------|-----------------------|----------|----------|
| `AnnualIncome` (annual_income) | `VillageIncome` (village_incomes) | `amount`, `year`, `village_id` | **VillageIncome**（存储更细粒度的收入分类） |
| `AnnualIndustry` (annual_industry) | `IndustrySupport` (industry_supports) | `industry_type`, `output_value`, `year`, `village_id` | **IndustrySupport**（包含更完整的状态字段） |
| `AnnualInfrastructure` (annual_infrastructure) | `InfrastructureImprovement` (infrastructure_improvements) | `project_name`, `investment`, `year`, `village_id` | **InfrastructureImprovement**（包含进度 + 照片） |
| `AnnualPopulation` (annual_population) | `VillagePopulation` (village_populations) | `total_population`, `year`, `village_id` | **VillagePopulation**（更细粒度的人口分类） |

**决策**: 废弃全部 4 个 `Annual*` 表，以 `*Support`/`Village*` 表为权威来源。理由：
- `Annual*` 表字段是 `*Support` 表的子集
- `*Support` 表有更完整的业务上下文（状态、分类、附件、审批流程）
- 维护两套表导致数据不一致风险（同一村庄同一年数据可能不同）

**执行步骤**:
1. 编写数据迁移脚本：将 `Annual*` 中有而对应 `*Support` 表中缺失的年份数据合并
2. 验证迁移后数据完整性
3. 更新所有引用 `Annual*` 模型的 API 端点，改为查询对应 `*Support` 表
4. 创建 Alembic 迁移删除 4 个 `Annual*` 表
5. 从 `models/__init__.py` 移除 `Annual*` 导入

**P2-2 业务理由（SoftDeleteMixin）**:

当前系统通过应用层逻辑实现"删除"（前端不显示，但数据库记录未标记为删除），这导致：
- 数据恢复困难（无法区分"用户想删的"和"系统错误删的"）
- 审计追溯不完整（删除操作无标记）
- 数据同步时无法判断本地删除 vs 远程新增

`SoftDeleteMixin` 添加 `is_deleted` + `deleted_at` 列，配合索引覆盖，性能开销微小（~5% 额外过滤时间）。仅在以下核心实体上激活（需配合 `CREATE INDEX idx_{table}_is_deleted ON {table}(is_deleted) WHERE is_deleted = 0` 确保查询性能）：
- `SupportedVillage`（帮扶村）— 误删恢复需求高
- `Project`（帮扶项目）— 审计合规要求
- `Fund`（帮扶资金）— 财务数据不可物理删除

**P2-3 业务理由（VersionMixin）**:

当前 `User.token_version` 和 `Fund.budget_version` 手动维护版本号。`VersionMixin` 标准化乐观锁：
- 防止并发编辑覆盖（多用户场景下的数据安全）— 虽然当前是单机版，但多机数据同步场景下版本冲突检测至关重要
- 数据同步时用于判断"谁更新"（last-write-wins 退化为 version-compare）
- 统一版本管理（不再手动在各模型重复 `version` 列）

**P2-4 详细设计（双向外键问题）**:

当前问题：
```python
# FundTransferVoucher 同时持有 fund_id 和 project_id
# 但 fund.project_id 已指向对应 Project
class FundTransferVoucher(Base):
    fund_id = Column(Integer, ForeignKey("funds.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))  # 冗余!
```

修复后：
```python
class FundTransferVoucher(Base):
    fund_id = Column(Integer, ForeignKey("funds.id"))
    # project_id 移除，改为通过 fund.project_id 属性访问
    @property
    def project_id(self):
        return self.fund.project_id if self.fund else None
```

**风险**: 中。需要创建非破坏性 Alembic 迁移（先加列→迁移数据→删冗余列）。需在测试环境充分验证。
**验证**: 后端 942 测试 + 新迁移测试；数据完整性脚本验证。

#### 阶段三：服务层重构 & Fat Controller 拆分（中高风险）

| ID | 任务 | 文件 | 变更类型 |
|----|------|------|----------|
| P3-1 | 评估 DDD domain/ 层命运 | `services/domain/` 28 文件 → 评估后决定：激活、重写或删除 | 决策+执行 |
| P3-1a | （如激活）创建 Repository 层 | `services/repositories/` → Village/Fund/Project/School/Approval Repository | 数据访问封装 |
| P3-1b | （如删除）移除废弃 domain/ 文件 | `services/domain/` 28 文件删除 | 清理死代码 |
| P3-2 | 拆分 fund_lifecycle.py | 1个单体→7个子模块+领域服务 | 大规模提取 |
| P3-3 | 拆分 projects.py | 提取 ExcelService/FileService/AuditService | 提取委托 |
| P3-4 | 拆分 assessment.py | 441行→`services/assessment/` | 提取服务 |
| P3-5 | 瘦身超大服务 | data_validator(1174行)、data_package(994行)、data_sync(882行) | 拆分子服务 |
| P3-6 | 拆分 analytics_service.py | 707行→按报表类型拆为子服务 | 提取 |
| P3-7 | 拆分 message_template_service.py | 846行→分离模板CRUD和默认数据 | 提取 |

**P3-1 详细设计（DDD 层决策 + Repository 层创建）**:

当前状况：`services/domain/` 下 28 个文件（聚合、仓储、领域服务、值对象、事件处理器），零引用，完全未接入应用。这可能是以下两种情况的产物：
1. **被遗弃的重构尝试**: 架构方向改变了，DDD 层不再需要 → 应删除
2. **未完成的重构**: 有价值的设计但未能接入应用 → 应激活

**决策流程**:
```
评估 domain/ 文件质量
  ├── 聚合/值对象设计合理、与当前 Schema 匹配 → 激活（P3-1a）
  │     ├── 在 services/repositories/ 创建 Village/Fund/Project/School/Approval Repository
  │     ├── 将 domain/*_domain_service.py 桥接到 API 层
  │     └── 删除不再需要的顶层级联服务文件
  └── 设计过时、与 Schema 不匹配、质量低 → 删除（P3-1b）
        └── 移除 28 个文件，释放 ~50KB 代码负担
```

决策由人工执行（需理解业务需求），AI 提供每个文件的评估摘要（质量、匹配度、是否仍适用）。

**P3-1a（激活路径）Repository 创建**:
```
services/repositories/
  ├── __init__.py
  ├── base.py                    # BaseRepository（已在 P1-9 创建，P3-1a 直接复用）
  ├── fund_repository.py         # FundRepository（已在 P1-9 创建，P3-1a 直接复用）
  ├── village_repository.py      # VillageRepository → SupportedVillage + 19 子表（P3-1a 新建）
  ├── project_repository.py      # ProjectRepository → Project + milestones + files（P3-1a 新建）
  ├── school_repository.py       # SchoolRepository → School + attachments（P3-1a 新建）
  └── approval_repository.py     # ApprovalRepository → Workflow + tasks + records（P3-1a 新建）
```
注：`FundRepository` 和 `BaseRepository` 在 P1-9 已创建，P3-1a 不重复创建。
每个 Repository 封装对应聚合根及其所有子表的查询逻辑。

当前单体结构（44 端点，~1926 行）：
```
fund_lifecycle.py (当前)
├── Phase 1: 项目资金阶段初始化 (6 端点)
├── Phase 2: 预算基线管理 (6 端点)
├── Phase 3: 资金调拨凭证 (6 端点)
├── Phase 4: 合同管理 (7 端点)
├── Phase 5: 异常检测与处理 (6 端点)
├── Phase 6: 结算管理 (7 端点)
├── Phase 7: 资产核销 (6 端点)
└── 内联业务逻辑：预算聚合、合规检查、健康评分、阶段推进/回退
```

目标拆分结构：
```
fund_lifecycle.py (重构后，仅路由定义 ~400 行)
  → services/funding/phase_init_service.py      (阶段初始化)
  → services/funding/phase_budget_service.py    (预算基线)
  → services/funding/phase_transfer_service.py  (资金调拨)
  → services/funding/phase_contract_service.py  (合同管理)
  → services/funding/phase_anomaly_service.py   (异常检测)
  → services/funding/phase_settlement_service.py(结算管理)
  → services/funding/phase_verification_service.py(资产核销)
  → services/domain/funding/fund_domain_service.py (DDD 桥接)
```

**P3-3 详细设计（projects.py 拆分）**:

当前内联逻辑 → 提取目标：
- Excel 模板生成（500+ 行 openpyxl）→ `services/excel_template_service.py`（已存在，直接委托）
- 批量导入解析 + 枚举映射 → `services/excel_importer_service.py`（已存在）
- 健康评分计算 → `services/fund_health_service.py`（新建）
- 文件上传/下载/安全检查 → `services/file_management_service.py`（新建）
- 审计差异追踪 → `services/audit_enhancement_service.py`（已存在，直接委托）
- 工作日志记录 → `services/work_log_service.py`（已存在，直接委托）

**风险**: 中高。涉及大量文件变更，需逐个端点验证行为不变。
**验证**: 全部 942+403 测试；手动回归测试 fund_lifecycle 44 个端点。

---

### 2.3 Phase Gates（阶段门控 — 进入下一阶段的硬性条件）

每个阶段完成后，必须满足以下条件才能进入下一阶段：

| Gate | 条件 | 验证方式 |
|------|------|----------|
| **G1: 阶段一完成** | ① 后端 942 测试全绿（连续3次运行） ② 前端 403 测试全绿 ③ `flake8 app/ --max-line-length=120` = 0 ④ `npx vue-tsc --noEmit` = 0（仅检查已修复项） ⑤ 应用启动正常（`python start.py` + `npm run dev`） | 自动化CI脚本 |
| **G2: 阶段二完成** | ① G1 全部条件 ② Alembic 迁移可正向+反向执行（`alembic upgrade head` + `alembic downgrade -1`） ③ 数据完整性验证脚本通过（无孤立FK、无重复年度数据） ④ 性能回归：4 个 KPI 端点响应时间 ≤ 基线值 + 10% | 自动化CI + 人工审查 |
| **G3: 阶段三完成** | ① G2 全部条件 ② fund_lifecycle 44 端点逐个手动验证 ③ projects 21 端点逐个手动验证 ④ 所有新建服务有单元测试覆盖（≥ 80% 行覆盖） ⑤ 性能回归：4 个 KPI 端点响应时间 ≤ 基线值 + 20%（服务层增加有合理开销） | 自动化CI + 人工回归测试 |

---

### 2.4 性能基线测量方法

**测量工具**: Python `time.perf_counter()` + curl + 后端日志中间件

**测量协议**（阶段一开始前执行）:
1. **环境**: 本地 Windows 10, Python 3.11, SQLite WAL, 预热 3 次请求后测量
2. **每个端点**: 连续请求 10 次，取 P50 和 P95（排除首次冷启动）
3. **测试数据**: 使用当前数据库实际数据（不做人工数据规模假设）
4. **端点列表**:
   - `GET /api/v1/funds/?page=1&page_size=20` — 资金列表
   - `GET /api/v1/fund-lifecycle/phases/{fund_id}` — 生命周期阶段
   - `GET /api/v1/projects/?page=1&page_size=20` — 项目列表
   - `POST /api/v1/projects/` — 项目创建

**可接受偏差**:
- 阶段一后: 响应时间变化 ≤ 5%
- 阶段二后: 响应时间变化 ≤ 10%
- 阶段三后: 响应时间变化 ≤ 20%

---

## 3. 安全考量

| 关注点 | 保证措施 |
|--------|----------|
| 重构不引入安全漏洞 | 所有现有安全中间件（CSRF、加密、审计日志）不变 |
| 权限检查一致性 | RBAC 合并后使用统一的 `rbac_service.py`，所有权限检查点必须保持等效 |
| 数据加密不削弱 | `encryption_service.py`、`password_encryption_service.py`、`data_sync_encryption_service.py` 不修改 |
| SQLite 安全 | 所有数据库操作保持参数化查询，不引入 SQL 注入风险 |
| 单机数据安全 | 不影响现有的 `.env` 加密配置和数据库文件权限 |

---

## 4. 性能影响评估

| 变更 | 性能影响 | 说明 |
|------|----------|------|
| 服务层提取 | 中性/微正向 | 减少懒加载导入开销，但增加函数调用层数 |
| 统一 BaseModel | 中性 | `to_dict()` 方法已存在，没有额外开销 |
| 移除冗余 FK | 微正向 | 减少索引维护开销，简化 JOIN |
| 激活 SoftDeleteMixin | 微负向 | 每次查询需过滤 `is_deleted=False`，需确保索引覆盖 |
| Fat controller 拆分 | 中性 | 函数调用增加但懒加载减少，抵消 |

**关键性能指标基线**（阶段一前需记录）：
- `/api/v1/funds/` 列表查询响应时间
- `/api/v1/fund-lifecycle/` 各阶段端点响应时间
- `/api/v1/projects/` CRUD 响应时间
- 前后端启动时间

---

## 5. 测试策略

### 5.1 回归测试（每阶段必须）

```bash
cd backend && python -m pytest tests/ -v  # 942 测试全绿
cd frontend && npm test -- --run           # 403 测试全绿
python -m flake8 app/ --max-line-length=120  # 0 错误
```

### 5.2 新增测试（随重构添加）

- P1-4: RBAC 合并后新增权限一致性测试（~10 个）
- P1-6: 桩服务实现后新增服务单元测试（~15 个）
- P2-4: FK 迁移后新增数据完整性测试（~5 个）
- P3-2: fund_lifecycle 拆分为7个阶段后，每个阶段新增独立测试（~20 个）
- P3-3: projects.py 提取后新增各子服务测试（~10 个）

### 5.3 集成测试

- 审批流程端到端（ApprovalWorkflow → ApprovalTask → ApprovalRecord）
- 资金全生命周期（Phase 1→7 完整链路）
- 项目 CRUD → 文件上传 → 审计追踪

---

## 6. 回滚策略

每阶段通过 Git 分支隔离，每完成一个子任务提交一次：

```bash
# 阶段一分支
git checkout -b arch/phase1-eliminate-violations
# 子任务完成后
git commit -m "P1-1: extract _migrate_missing_columns to core/migration_helper"
# ...
# 阶段完成后合并
git checkout main && git merge arch/phase1-eliminate-violations
```

如果某子任务导致测试失败：
1. `git revert` 该子任务
2. 分析失败原因
3. 修复后重新提交

---

## 7. 交付物

| 阶段 | 交付物 |
|------|--------|
| 阶段一 | 8 个 commit，0 flake8 错误，942+403 测试通过 |
| 阶段二 | 3-5 个 Alembic 迁移脚本，新增数据完整性测试 |
| 阶段三 | 10-15 个新服务文件，fund_lifecycle 44 端点全部保持兼容 |

---

## 8. 附录：文件清单

### 需修改文件（阶段一）

1. `backend/app/services/version_service.py` — P1-1
2. `backend/app/services/backup_scheduler.py` — P1-2
3. `backend/app/services/excel_importer_service.py` — P1-3
4. `backend/app/core/permissions.py` — P1-4
5. `backend/app/services/rbac_service.py` — P1-4
6. `backend/app/api/v1/data/__init__.py` — P1-5
7. `backend/app/services/fund_service.py` — P1-6
8. `backend/app/services/supported_village_service.py` — P1-6
9. `backend/app/services/batch_service.py` — P1-6
10. `backend/app/services/report_export_service.py` — P1-6
11. `backend/app/services/metrics_service.py` — P1-6
12. `backend/app/services/async_export_service.py` — P1-6
13. `backend/app/services/import_export_history_service.py` — P1-6
14. `backend/app/core/audit.py` — P1-7
15. `backend/app/services/project/__init__.py` — P1-8

### 需新建文件（阶段一）

1. `backend/app/core/migration_helper.py` — P1-1
2. `backend/app/core/constants.py` — P1-2

### 需修改文件（阶段二）

1. `backend/app/models/base.py` — P2-1, P2-2, P2-3
2. ~50 个模型文件 — P2-1 统一继承
3. 8 个 fund_lifecycle 模型 — P2-4
4. Alembic 迁移脚本 — P2-1 到 P2-5

### 需修改文件（阶段三）

1. `backend/app/api/v1/fund_lifecycle.py` — P3-2
2. `backend/app/api/v1/projects.py` — P3-3
3. `backend/app/api/v1/assessment.py` — P3-4
4. `backend/app/services/data_validator_service.py` — P3-5
5. `backend/app/services/data_package_service.py` — P3-5
6. `backend/app/services/data_sync_service.py` — P3-5
7. `backend/app/services/domain/` — P3-1 桥接激活
