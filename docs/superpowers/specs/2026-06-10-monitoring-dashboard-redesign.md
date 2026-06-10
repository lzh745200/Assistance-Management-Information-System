# 系统监控面板重新布局设计 — Spec

**日期**: 2026-06-10  
**状态**: 已确认  
**目标**: 在完全保留原有监控能力的前提下，通过布局优化让管理员一眼看全系统运行状况。

---

## 1. 范围与约束

### 纳入范围
- 重写 `frontend/src/views/system/MonitoringDashboard.vue` — 统一的监控仪表盘
- 补全 `frontend/src/api/systemHealth.ts` — 缺失的 DB 维护 API 方法
- 修改 `frontend/src/router/index.ts` — `/system/health` → redirect 到 `/system/monitoring`
- 新增 `frontend/tests/unit/views/MonitoringDashboard.test.ts` — 10 个测试用例

### 排除范围
- 所有后端文件（零后端改动）
- 外部图表库引入（使用已有 ECharts v5.5.0）
- `SystemMonitor.vue`（保留不动，孤儿页面无路由）
- `SystemHealth.vue`（删除，功能并入监控面板）

### 约束
- 不使用外部图表库（ECharts 已存在）
- 所有样式使用 Scoped CSS
- 不改变路由名称、菜单结构
- 页面加载时间增加 < 100ms
- 通过所有现有测试

---

## 2. 数据架构

### 后端 API（不改动）
| 端点 | 用途 | 调用于 |
|------|------|--------|
| `GET /system/health/full` | 基础元数据 (uptime, db_size, table_count, version) | 初始化 + 轮询 |
| `GET /system/monitor/snapshot` | 实时资源 (cpu%, mem%, disk%, network, process) | 轮询 |
| `GET /system/monitor/api-stats` | API 统计（替换硬编码假数据） | 轮询 |
| `GET /system/monitor/resources` | 详细资源（分区、SWAP） | 按需 |
| `GET /system/health/overview` | 健康概览 (DB/disk/file/WAL checks) | 按需 |
| `GET /system/monitor/alerts` | 告警规则 + 历史 | 按需 |
| `POST /system/health/*` | DB 维护操作 | 用户触发 |

### 前端数据流
```
API 响应 → MonitoringDashboard.vue
  ├─ useMonitorData()     数据获取 + 环形缓冲区 (30s轮询, 并行3请求)
  ├─ useHealthScore()     健康评分计算
  ├─ useTheme()           暗色/亮色自适应 (ECharts 重建)
  └─ useHistoryBuffer()   环形缓冲区 (最近10点, ~5分钟)
```

### 环形缓冲区
```ts
interface HistoryPoint {
  timestamp: string;
  cpu: number;
  memory: number;
  disk: number;
  networkIn: number;
  networkOut: number;
}
const MAX_POINTS = 10; // 5分钟 @ 30s间隔
// 固定长度环形队列，满时 shift() 最早元素
```

### 错误处理
- 每个数据区独立 try/catch，一个 API 失败不影响其他
- 失败卡片显示占位符 + 上次成功值（灰显）+ 错误图标
- 自动重试依赖 30s 轮询周期
- 首屏使用 `el-skeleton` 骨架屏

---

## 3. 布局设计

### 方案: 紧凑型单屏仪表盘 (方案A)

```
┌──────────────────────────────────────────────────────────────────┐
│  系统监控面板                          健康评分  92         [刷新] [导出]  │
│  最后更新: 2026-06-10 14:32:05        ●━━━━━━━○ /100                       │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│  CPU      │  内存     │  磁盘     │  网络     │  进程     │  数据库   │  ← 6列指标卡片
│  23%      │  58%      │  41%      │  ↓12 ↑5  │  线程:12  │  45.2 MB  │     CSS Grid
│  正常 🟢  │  正常 🟢  │  正常 🟢  │  正常 🟢  │  PID:8426 │  38 表    │     auto-fit
│  ▁▂▁▃▂▁  │  ▃▄▃▄▃▄  │  ▅▅▅▅▅▅  │  ▂▃▃▂▃▂  │          │          │     minmax
├────────────────────────────┬─────────────────────────────────────┤
│  API 请求趋势图 (ECharts)   │  系统日志 (最新10条)                 │
│  折线图: 请求数+响应时间     │  分级着色 error/warn/info            │
├────────────────────────────┴─────────────────────────────────────┤
│  ▼ 系统健康检查 & 数据库维护  [默认折叠, sessionStorage 记忆]       │
│  基础检查 (5项) + 性能检查 (5项) + DB维护按钮 + 表统计             │
└──────────────────────────────────────────────────────────────────┘
```

### 状态色标

| 指标 | 绿色 (正常) | 黄色 (警告) | 红色 (严重) |
|------|------------|------------|------------|
| CPU | < 70% | 70-90% | ≥ 90% |
| 内存 | < 75% | 75-90% | ≥ 90% |
| 磁盘 | < 75% | 75-90% | ≥ 90% |
| 错误率 | < 1% | 1-5% | ≥ 5% |

### 响应式断点
- **1920×1080 (宽屏)**: 6 列卡片 → 2 列图表 → 底部折叠区
- **1366×768 (笔记本)**: 卡片 3 列折行，sparkline 隐藏，图表高度缩减
- **<768px**: 单列堆叠，非核心内容折叠

### 暗色/亮色适配
- 复用 `tokens.scss` CSS 变量体系
- Card 背景、文字色跟随 `[data-theme]` 自动切换
- ECharts 实例在主题 watch 中 dispose + 重建

---

## 4. 交互设计

### Tooltip (hover 200ms)
- 触发: 鼠标悬停指标卡片
- 内容: Canvas 迷你趋势图 + 统计摘要 (当前/平均/最低/最高) + 元数据
- 实现: Element Plus `el-popover`

### 刷新机制
- 保留 30s `setInterval`（并行调用 3 个 API: snapshot + api-stats + full）
- 时间戳 HH:mm:ss，自动刷新时闪烁指示器
- 手动刷新按钮带 loading
- unmount 时 clearInterval

### 折叠区
- 默认折叠，`▼`/`▶` 箭头切换
- 展开状态记录 sessionStorage
- DB 维护操作: `el-loading` 遮罩 + `el-alert` 结果反馈

### 导出
- 导出当前快照 + 环形缓冲区 → JSON 文件

---

## 5. 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 重写 | `frontend/src/views/system/MonitoringDashboard.vue` | 统一监控面板 (~500行) |
| 补全 | `frontend/src/api/systemHealth.ts` | 补充 `getTableStats`, `runIntegrityCheck`, `runWalCheckpoint`, `runVacuum` |
| 修改 | `frontend/src/router/index.ts` | `/system/health` redirect |
| 删除 | `frontend/src/views/system/SystemHealth.vue` | 功能并入监控面板 |
| 新增 | `frontend/tests/unit/views/MonitoringDashboard.test.ts` | 10 个测试用例 |

---

## 6. 测试用例

| 编号 | 测试项 | 验证点 |
|------|--------|--------|
| T1 | 6 指标卡片渲染 | 所有卡片存在，数值非空 |
| T2 | 健康评分圆环 | 0-100 范围，颜色随分数变化 |
| T3 | API 趋势图初始化 | ECharts 实例存在，series 非空 |
| T4 | 系统日志渲染 | 分级着色，空状态占位符 |
| T5 | 暗色/亮色切换 | data-theme 变化后样式响应 |
| T6 | 响应式布局 | 1366×768 下卡片折行为 ≤3 列 |
| T7 | 错误隔离 | 单 API 失败不影响其他卡片 |
| T8 | 环形缓冲区 | 第 11 次 push 后长度 = 10 |
| T9 | 折叠区交互 | 展开/折叠 + sessionStorage |
| T10 | 定时器清理 | unmount 后无活跃 interval |

---

## 7. 性能基线

| 指标 | 原值 | 目标 |
|------|------|------|
| 首次渲染时间 | ~120ms | < +100ms |
| 单次刷新 | 1 API | 3 API 并行 |
| 组件规模 | ~280 行 | ~500 行 |
| CSS 体积 | ~40 行 | ~200 行 scoped |
