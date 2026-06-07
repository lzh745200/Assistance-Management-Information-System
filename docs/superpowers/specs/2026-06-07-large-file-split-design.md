# 大文件拆分 — 设计文档

**日期**: 2026-06-07
**状态**: 已确认

## 目标

将 4 个超大文件拆分为小模块，每个模块单一职责，可独立理解和测试。

## 拆分方案

### 前端

#### HomeSafe.vue（2601行 → 5 文件）

| 新文件 | 行数 | 职责 |
|--------|------|------|
| `views/dashboard/HomeSafe.vue` | ~200 | 主容器，编排子组件 |
| `views/dashboard/components/QuickActions.vue` | ~200 | 快捷操作入口 |
| `views/dashboard/components/RecentActivity.vue` | ~300 | 最近动态列表 |
| 复用 `dashboard/KpiCards.vue` | — | 已有组件 |
| 复用 `dashboard/ChartRow.vue` | — | 已有组件 |
| 复用 `dashboard/InfoRow.vue` | — | 已有组件 |

#### Task.vue（1933行 → 4 文件）

| 新文件 | 行数 | 职责 |
|--------|------|------|
| `views/ruralWorks/Task.vue` | ~200 | 主容器 |
| `views/ruralWorks/components/TaskForm.vue` | ~500 | 任务表单 |
| `views/ruralWorks/components/TaskList.vue` | ~400 | 任务列表 |
| `views/ruralWorks/components/TaskDetail.vue` | ~400 | 任务详情 |

### 后端

#### fund_lifecycle.py（2190行 → 4 文件）

| 新文件 | 行数 | 职责 |
|--------|------|------|
| `api/v1/fund_lifecycle/__init__.py` | ~20 | 导出 router |
| `api/v1/fund_lifecycle/router.py` | ~600 | API 端点 |
| `services/fund_lifecycle_service.py` | ~700 | 业务逻辑 |
| `api/v1/fund_lifecycle/schemas.py` | ~300 | Pydantic 模型 |

#### projects.py（2128行 → 4 文件）

| 新文件 | 行数 | 职责 |
|--------|------|------|
| `api/v1/projects/__init__.py` | ~20 | 导出 router |
| `api/v1/projects/router.py` | ~700 | API 端点 |
| `services/project_service.py` | ~600 | 业务逻辑 |
| `api/v1/projects/schemas.py` | ~300 | Pydantic 模型 |

## 原则

- 只拆不移：不修改业务逻辑，只做文件拆分
- 导入路径更新：所有 import 路径同步更新
- 测试保持通过：每步拆分后跑测试确认
- 先拆后端再拆前端：后端拆分对前端透明，风险更低

## 验证

```bash
cd backend && python -m pytest tests/ -q --tb=short
cd frontend && npx vitest run
cd frontend && npx tsc --noEmit
```
