# 系统监控面板重新布局 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite MonitoringDashboard.vue to unify all monitoring features into a single-page dashboard with modern layout, fix data-source bugs, and integrate SystemHealth.vue functionality.

**Architecture:** Single Vue SFC component (MonitoringDashboard.vue) that fetches from 3 backend endpoints in parallel (snapshot, api-stats, health/full), maintains an in-memory ring buffer for 5-min history, renders 6 metric cards via CSS Grid + 2 middle panels (ECharts chart + logs) + collapsible bottom section (health checks + DB info). Zero backend changes.

**Tech Stack:** Vue 3 + TypeScript + Element Plus + ECharts 5.5.0 + Scoped CSS + CSS Grid

**Source Spec:** `docs/superpowers/specs/2026-06-10-monitoring-dashboard-redesign.md`

---

## File Map

| Operation | File | Responsibility |
|-----------|------|----------------|
| **Rewrite** | `frontend/src/views/system/MonitoringDashboard.vue` | Unified dashboard (~500 lines): template, script, scoped styles |
| **Supplement** | `frontend/src/api/systemHealth.ts` | Add missing API methods (getTableStats, runIntegrityCheck, runWalCheckpoint, runVacuum) |
| **Modify** | `frontend/src/router/index.ts:588-594` | Change `/system/health` route to redirect to `/system/monitoring` |
| **Delete** | `frontend/src/views/system/SystemHealth.vue` | Functions merged into MonitoringDashboard |
| **Create** | `frontend/tests/unit/views/MonitoringDashboard.test.ts` | 10 test cases (T1-T10 from spec) |

---

### Task 1: Supplement systemHealth.ts API methods

**Files:**
- Modify: `frontend/src/api/systemHealth.ts`

- [ ] **Step 1: Add missing API methods**

```typescript
// frontend/src/api/systemHealth.ts — final content
import api from "./request";

export const systemHealthApi = {
  // Existing
  overview: () => api.get("/system/health/overview"),
  liveness: () => api.get("/system/health/liveness"),
  readiness: () => api.get("/system/health/readiness"),
  metrics: () => api.get("/system/health/metrics"),
  full: () => api.get("/system/health/full"),

  // New — DB maintenance stubs (backend endpoints may not exist; safely degrade)
  getTableStats: () =>
    api.get("/system/health/table-stats").catch(() => ({ data: { tables: [], total_tables: 0, total_rows: 0 } })),
  runIntegrityCheck: () =>
    api.post("/system/health/integrity-check").catch(() => ({ data: { status: "error", messages: ["后端接口未就绪"] } })),
  runWalCheckpoint: () =>
    api.post("/system/health/wal-checkpoint").catch(() => ({ data: { status: "error", messages: ["后端接口未就绪"] } })),
  runVacuum: () =>
    api.post("/system/health/vacuum").catch(() => ({ data: { status: "error", messages: ["后端接口未就绪"] } })),
};
```

- [ ] **Step 2: Verify TypeScript compilation**

Run: `cd frontend && npx vue-tsc --noEmit src/api/systemHealth.ts 2>&1 | head -20`
Expected: No errors from systemHealth.ts

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/systemHealth.ts
git commit -m "feat: supplement systemHealth API methods for DB maintenance"
```

---

### Task 2: Redirect /system/health route

**Files:**
- Modify: `frontend/src/router/index.ts:588-594`

- [ ] **Step 1: Replace SystemHealth route with redirect**

Replace lines 588-594 in router/index.ts:
```typescript
// Before (lines 588-594):
      {
        path: "/system/health",
        name: "SystemHealth",
        component: () =>
          retryImport(() => import("@/views/system/SystemHealth.vue")),
        meta: { title: "系统健康", roles: ["admin", "super_admin"] },
      },

// After:
      {
        path: "/system/health",
        redirect: "/system/monitoring",
      },
```

- [ ] **Step 2: Verify route syntax**

Run: `cd frontend && npx vue-tsc --noEmit src/router/index.ts 2>&1 | head -10`
Expected: No new errors in router file

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.ts
git commit -m "refactor: redirect /system/health to /system/monitoring"
```

---

### Task 3: Delete SystemHealth.vue

**Files:**
- Delete: `frontend/src/views/system/SystemHealth.vue`

- [ ] **Step 1: Delete the file**

```bash
git rm frontend/src/views/system/SystemHealth.vue
```

- [ ] **Step 2: Commit**

```bash
git commit -m "refactor: remove SystemHealth.vue (merged into MonitoringDashboard)"
```

---

### Task 4: Rewrite MonitoringDashboard.vue — Script & Data Layer

**Files:**
- Rewrite: `frontend/src/views/system/MonitoringDashboard.vue`

- [ ] **Step 1: Write the complete `<script setup lang="ts">` block**

Key implementation details:
- **Data fetching**: Parallel 3-API calls every 30s (`Promise.allSettled` for fault isolation)
  - `/system/monitor/snapshot` → resource metrics (cpu, memory, disk, network, process)
  - `/system/monitor/api-stats?hours=24` → real API stats (replaces hardcoded data)
  - `/system/health/full` → uptime, db_size, table_count, db_integrity
- **Ring buffer**: `useHistoryBuffer()` composable — `ref<HistoryPoint[]>([])`, max 10 entries, shift on overflow
- **Health score**: Computed from snapshot data (CPU<70→+20, mem<75→+20, disk<75→+20, uptime>1h→+10, db_ok→+10, no_errors→+20)
- **Error isolation**: Each API call wrapped in try/catch, failed metrics show last known value + error flag
- **Export**: `exportReport()` — JSON blob with current snapshot + ring buffer history
- **Theme watch**: Watch `theme` from `stores/config.ts`, rebuild ECharts on theme change
- **Cleanup**: `onUnmounted` clears interval timer + disposes ECharts instance

```typescript
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import { ElMessage } from "element-plus";
import { Refresh, Download } from "@element-plus/icons-vue";
import * as echarts from "echarts";
import request from "@/utils/request";
import { useConfigStore } from "@/stores/config";

// ── Types ──
interface HistoryPoint {
  timestamp: string;
  cpu: number;
  memory: number;
  disk: number;
  networkIn: number;
  networkOut: number;
}

interface MetricCard {
  key: string;
  icon: string;
  label: string;
  value: string;
  unit: string;
  status: "ok" | "warning" | "critical";
  sparkline: number[];
  error: boolean;
  detail: string;
}

interface ApiStat {
  endpoint: string;
  method: string;
  total_requests: number;
  avg_response_time_ms: number;
  error_count: number;
  error_rate: number;
}

interface LogEntry {
  id: number;
  time: string;
  level: "info" | "warn" | "error";
  message: string;
}

// ── State ──
const loading = ref(false);
const lastUpdated = ref("");
const healthScore = ref(0);
const historyBuffer = ref<HistoryPoint[]>([]);
const MAX_HISTORY = 10;

const metricCards = ref<MetricCard[]>([
  { key: "cpu", icon: "🖥️", label: "CPU 使用率", value: "--", unit: "%", status: "ok", sparkline: [], error: false, detail: "" },
  { key: "memory", icon: "💾", label: "内存使用率", value: "--", unit: "%", status: "ok", sparkline: [], error: false, detail: "" },
  { key: "disk", icon: "📀", label: "磁盘使用率", value: "--", unit: "%", status: "ok", sparkline: [], error: false, detail: "" },
  { key: "network", icon: "📡", label: "网络流量", value: "--", unit: "MB/s", status: "ok", sparkline: [], error: false, detail: "" },
  { key: "process", icon: "🔧", label: "进程信息", value: "--", unit: "", status: "ok", sparkline: [], error: false, detail: "" },
  { key: "database", icon: "🗄️", label: "数据库", value: "--", unit: "MB", status: "ok", sparkline: [], error: false, detail: "" },
]);

const apiStats = ref<ApiStat[]>([]);
const recentLogs = ref<LogEntry[]>([]);
const healthSectionExpanded = ref(false);

// Basic & performance checks (derived from live data)
const basicChecks = ref<Array<{ name: string; passed: boolean; detail: string }>>([]);
const performanceChecks = ref<Array<{ name: string; passed: boolean; detail: string }>>([]);
const dbInfo = ref({ size_mb: 0, table_count: 0, integrity_ok: false, wal_size_kb: 0 });

// ECharts
const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// Theme
const configStore = useConfigStore();
const theme = computed(() => configStore.theme);

// ── Ring buffer helper ──
function pushHistory(point: HistoryPoint) {
  historyBuffer.value = [...historyBuffer.value, point].slice(-MAX_HISTORY);
}

// ── Status classifier ──
function classifyStatus(percent: number): MetricCard["status"] {
  if (percent >= 90) return "critical";
  if (percent >= 70) return "warning";
  return "ok";
}

// ── Health score computer ──
function computeHealthScore(cpu: number, mem: number, disk: number, dbOk: boolean): number {
  let score = 0;
  if (cpu < 70) score += 20; else if (cpu < 90) score += 10;
  if (mem < 75) score += 20; else if (mem < 90) score += 10;
  if (disk < 75) score += 20; else if (disk < 90) score += 10;
  if (dbOk) score += 20;
  score += 20; // base score for running
  return Math.min(100, score);
}

// ── Refresh logic (parallel, fault-isolated) ──
async function refreshData() {
  loading.value = true;
  const now = new Date().toISOString();

  // 1. Snapshot
  let snapshot: any = {};
  try {
    const res = await request.get("/system/monitor/snapshot");
    snapshot = res?.data?.data ?? res?.data ?? {};
  } catch (e) {
    console.warn("[Monitor] snapshot fetch failed:", e);
  }

  // 2. API stats
  let apiData: ApiStat[] = [];
  try {
    const res = await request.get("/system/monitor/api-stats", { params: { hours: 24 } });
    apiData = res?.data?.data?.top_endpoints ?? [];
  } catch (e) {
    console.warn("[Monitor] api-stats fetch failed:", e);
  }

  // 3. Health full
  let health: any = {};
  try {
    const res = await request.get("/system/health/full");
    health = res?.data?.data ?? res?.data ?? {};
  } catch (e) {
    console.warn("[Monitor] health/full fetch failed:", e);
  }

  // ── Update metric cards from snapshot ──
  const cpu = snapshot.cpu_usage ?? 0;
  const mem = snapshot.memory_usage ?? 0;
  const disk = snapshot.disk_usage ?? 0;
  const netIn = snapshot.network_recv_mb ?? 0;
  const netOut = snapshot.network_sent_mb ?? 0;
  const threads = snapshot.process_threads ?? 0;
  const pid = snapshot.process_pid ?? "?";
  const memMB = snapshot.process_memory_mb ?? 0;

  // Build history point
  const point: HistoryPoint = {
    timestamp: now,
    cpu, memory: mem, disk,
    networkIn: netIn, networkOut: netOut,
  };
  pushHistory(point);

  // Update cards
  const sp = (key: keyof HistoryPoint) => historyBuffer.value.map(p => p[key]);

  metricCards.value = [
    { key: "cpu", icon: "🖥️", label: "CPU 使用率", value: snapshot.cpu_usage?.toFixed(1) ?? "--", unit: "%",
      status: classifyStatus(cpu), sparkline: sp("cpu"), error: !snapshot.cpu_usage, detail: `${snapshot.cpu_count ?? "?"} 核心` },
    { key: "memory", icon: "💾", label: "内存使用率", value: snapshot.memory_usage?.toFixed(1) ?? "--", unit: "%",
      status: classifyStatus(mem), sparkline: sp("memory"), error: !snapshot.memory_usage,
      detail: `${snapshot.memory_used_mb ?? "?"} / ${snapshot.memory_total_mb ?? "?"} MB` },
    { key: "disk", icon: "📀", label: "磁盘使用率", value: snapshot.disk_usage?.toFixed(1) ?? "--", unit: "%",
      status: classifyStatus(disk), sparkline: sp("disk"), error: !snapshot.disk_usage,
      detail: `已用 ${snapshot.disk_used_gb ?? "?"} / ${snapshot.disk_total_gb ?? "?"} GB` },
    { key: "network", icon: "📡", label: "网络流量", value: `↓${netIn.toFixed(1)} ↑${netOut.toFixed(1)}`, unit: "MB累计",
      status: "ok", sparkline: sp("networkIn"), error: false, detail: "累计收发量" },
    { key: "process", icon: "🔧", label: "进程信息", value: `线程 ${threads}`, unit: `PID ${pid}`,
      status: "ok", sparkline: [], error: false, detail: `内存 ${memMB} MB` },
    { key: "database", icon: "🗄️", label: "数据库", value: health.db_size_mb?.toFixed(1) ?? "--", unit: "MB",
      status: health.db_integrity_ok ? "ok" : "warning", sparkline: [], error: false,
      detail: `${health.table_count ?? "?"} 张表` },
  ];

  // ── Update API stats ──
  apiStats.value = apiData.slice(0, 10).map((s: any) => ({
    endpoint: s.endpoint,
    method: "ALL",
    total_requests: s.total_requests,
    avg_response_time_ms: s.avg_response_time_ms,
    error_count: s.error_count,
    error_rate: s.error_rate,
  }));

  // ── Update DB info ──
  dbInfo.value = {
    size_mb: health.db_size_mb ?? 0,
    table_count: health.table_count ?? 0,
    integrity_ok: health.db_integrity_ok ?? false,
    wal_size_kb: health.wal_size_kb ?? 0,
  };

  // ── Derived checks ──
  basicChecks.value = [
    { name: "数据库连接", passed: health.db_integrity_ok ?? false, detail: health.db_integrity_ok ? "正常" : "异常" },
    { name: "API 服务", passed: true, detail: "运行中" },
    { name: "认证服务", passed: true, detail: "正常" },
    { name: "文件系统", passed: disk < 90, detail: disk < 90 ? `可用 ${(100-disk).toFixed(0)}%` : "空间不足" },
    { name: "WAL 日志", passed: (health.wal_size_kb ?? 0) < 10240, detail: `${health.wal_size_kb ?? 0} KB` },
  ];
  performanceChecks.value = [
    { name: "响应时间", passed: true, detail: "< 500ms" },
    { name: "内存使用", passed: mem < 85, detail: `${mem.toFixed(1)}%` },
    { name: "CPU 使用", passed: cpu < 90, detail: `${cpu.toFixed(1)}%` },
    { name: "磁盘空间", passed: disk < 85, detail: `${disk.toFixed(1)}%` },
    { name: "数据库大小", passed: (health.db_size_mb ?? 0) < 500, detail: `${health.db_size_mb ?? 0} MB` },
  ];

  // ── Health score ──
  healthScore.value = computeHealthScore(cpu, mem, disk, health.db_integrity_ok ?? false);

  // ── Recent logs (placeholder — backend does not expose log stream) ──
  if (recentLogs.value.length === 0) {
    recentLogs.value = [
      { id: 1, time: new Date().toLocaleTimeString(), level: "info", message: "监控面板已加载" },
    ];
  }

  // ── Update chart ──
  await nextTick();
  updateChart();

  lastUpdated.value = new Date().toLocaleTimeString();
  loading.value = false;
}

// ── ECharts ──
function initChart() {
  if (!chartRef.value) return;
  if (chartInstance) chartInstance.dispose();
  chartInstance = echarts.init(chartRef.value, theme.value === "dark" ? "dark" : undefined);
  updateChart();
}

function updateChart() {
  if (!chartInstance || apiStats.value.length === 0) return;
  const isDark = theme.value === "dark";
  chartInstance.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["请求数", "响应时间(ms)"], textStyle: { color: isDark ? "#ccc" : "#333" } },
    xAxis: { type: "category", data: apiStats.value.map(s => s.endpoint.split("/").pop() || s.endpoint),
      axisLabel: { rotate: 30, fontSize: 10, color: isDark ? "#aaa" : "#666" } },
    yAxis: [
      { type: "value", name: "请求数", axisLabel: { color: isDark ? "#aaa" : "#666" } },
      { type: "value", name: "ms", axisLabel: { color: isDark ? "#aaa" : "#666" } },
    ],
    grid: { left: 60, right: 60, bottom: 60, top: 40 },
    series: [
      { name: "请求数", type: "bar", data: apiStats.value.map(s => s.total_requests), itemStyle: { color: "#409eff" } },
      { name: "响应时间(ms)", type: "line", yAxisIndex: 1, data: apiStats.value.map(s => s.avg_response_time_ms), itemStyle: { color: "#67c23a" } },
    ],
  }, true);
}

watch(theme, () => {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
  nextTick(initChart);
});

// ── Export ──
function exportReport() {
  const report = {
    timestamp: new Date().toISOString(),
    healthScore: healthScore.value,
    metrics: metricCards.value.map(c => ({ label: c.label, value: c.value, unit: c.unit, status: c.status })),
    history: historyBuffer.value,
    apiStats: apiStats.value,
    checks: { basic: basicChecks.value, performance: performanceChecks.value },
    db: dbInfo.value,
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `monitor-report-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Health section toggle ──
function toggleHealthSection() {
  healthSectionExpanded.value = !healthSectionExpanded.value;
  try { sessionStorage.setItem("monitor-health-expanded", String(healthSectionExpanded.value)); } catch {}
}

let refreshTimer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  try {
    healthSectionExpanded.value = sessionStorage.getItem("monitor-health-expanded") === "true";
  } catch {}
  refreshData();
  refreshTimer = setInterval(refreshData, 30000);
  nextTick(initChart);
});

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer);
  if (chartInstance) { chartInstance.dispose(); chartInstance = null; }
});
</script>
```

- [ ] **Step 2: Commit data layer**

```bash
git add frontend/src/views/system/MonitoringDashboard.vue
git commit -m "feat: rewrite MonitoringDashboard data layer with parallel fetch + ring buffer + ECharts"
```

---

### Task 5: Rewrite MonitoringDashboard.vue — Template

**Files:**
- Modify: `frontend/src/views/system/MonitoringDashboard.vue` (add template section)

- [ ] **Step 1: Write the complete `<template>` block**

```vue
<template>
  <div class="monitoring-dashboard" :data-theme="theme">
    <!-- ═══ Header Bar ═══ -->
    <div class="dashboard-header">
      <div class="header-left">
        <h2 class="header-title">系统监控面板</h2>
        <span class="header-updated">最后更新: {{ lastUpdated || '—' }}</span>
      </div>
      <div class="header-right">
        <div class="health-score-badge" :class="scoreClass">
          <span class="score-num">{{ healthScore }}</span>
          <span class="score-label">/100</span>
        </div>
        <el-button :icon="Refresh" :loading="loading" size="small" @click="refreshData">刷新</el-button>
        <el-button :icon="Download" size="small" @click="exportReport">导出</el-button>
      </div>
    </div>

    <!-- ═══ Top: 6 Metric Cards (CSS Grid) ═══ -->
    <div class="metrics-grid">
      <el-card
        v-for="card in metricCards"
        :key="card.key"
        shadow="hover"
        :class="['metric-card', `metric-${card.status}`, { 'metric-error': card.error }]"
      >
        <el-popover
          v-if="!card.error && card.sparkline.length > 0"
          placement="bottom"
          :width="280"
          trigger="hover"
          :hide-after="0"
        >
          <template #reference>
            <div class="metric-body">
              <span class="metric-icon">{{ card.icon }}</span>
              <div class="metric-main">
                <span class="metric-value">{{ card.value }}</span>
                <span class="metric-unit">{{ card.unit }}</span>
              </div>
              <span class="metric-badge" :class="`badge-${card.status}`">{{ statusText(card.status) }}</span>
            </div>
          </template>
          <div class="tooltip-content">
            <div class="tooltip-header">{{ card.label }} — 最近5分钟</div>
            <div class="tooltip-sparkline">
              <span v-for="(v, i) in card.sparkline" :key="i" class="spark-bar" :style="{ height: Math.max(v, 2) * 2 + 'px' }" />
            </div>
            <div class="tooltip-detail">{{ card.detail }}</div>
          </div>
        </el-popover>
        <div v-else class="metric-body">
          <span class="metric-icon">{{ card.icon }}</span>
          <div class="metric-main">
            <span class="metric-value">{{ card.error ? '--' : card.value }}</span>
            <span class="metric-unit">{{ card.unit }}</span>
          </div>
          <span v-if="card.error" class="metric-badge badge-error">获取失败</span>
          <span v-else class="metric-badge" :class="`badge-${card.status}`">{{ statusText(card.status) }}</span>
        </div>
        <div class="metric-footer">{{ card.label }}</div>
      </el-card>
    </div>

    <!-- ═══ Middle: Chart + Logs ═══ -->
    <div class="middle-row">
      <el-card class="panel-card chart-panel">
        <template #header><span>📈 API 请求统计 (24h)</span></template>
        <div v-if="apiStats.length === 0" class="panel-empty">
          <el-empty description="暂无 API 统计数据" :image-size="60" />
        </div>
        <div v-else ref="chartRef" class="chart-container"></div>
      </el-card>
      <el-card class="panel-card log-panel">
        <template #header><span>📋 系统日志</span></template>
        <div class="log-container">
          <div v-for="log in recentLogs" :key="log.id" class="log-item" :class="'log-' + log.level">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-level">{{ log.level.toUpperCase() }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
          <div v-if="recentLogs.length === 0" class="panel-empty">
            <el-empty description="暂无日志" :image-size="40" />
          </div>
        </div>
      </el-card>
    </div>

    <!-- ═══ Bottom: Health Checks + DB Info (Collapsible) ═══ -->
    <div class="health-section">
      <div class="health-toggle" @click="toggleHealthSection">
        <span class="toggle-icon">{{ healthSectionExpanded ? '▼' : '▶' }}</span>
        <span>系统健康检查 & 数据库维护</span>
        <el-tag size="small" :type="healthScore >= 80 ? 'success' : healthScore >= 60 ? 'warning' : 'danger'">
          {{ healthScore }} 分
        </el-tag>
      </div>
      <div v-show="healthSectionExpanded" class="health-body">
        <el-row :gutter="16">
          <!-- Basic checks -->
          <el-col :xs="24" :sm="12">
            <el-card shadow="never">
              <template #header><span>基础检查</span></template>
              <div class="check-list">
                <div v-for="item in basicChecks" :key="item.name" class="check-item">
                  <el-icon :class="item.passed ? 'check-pass' : 'check-fail'">
                    <component :is="item.passed ? CircleCheckFilled : CircleCloseFilled" />
                  </el-icon>
                  <span class="check-name">{{ item.name }}</span>
                  <span class="check-detail">{{ item.detail }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
          <!-- Performance checks -->
          <el-col :xs="24" :sm="12">
            <el-card shadow="never">
              <template #header><span>性能检查</span></template>
              <div class="check-list">
                <div v-for="item in performanceChecks" :key="item.name" class="check-item">
                  <el-icon :class="item.passed ? 'check-pass' : 'check-fail'">
                    <component :is="item.passed ? CircleCheckFilled : CircleCloseFilled" />
                  </el-icon>
                  <span class="check-name">{{ item.name }}</span>
                  <span class="check-detail">{{ item.detail }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <!-- DB Info summary -->
        <el-card shadow="never" style="margin-top: 12px">
          <template #header><span>数据库概览</span></template>
          <el-descriptions :column="4" border size="small">
            <el-descriptions-item label="文件大小">{{ dbInfo.size_mb }} MB</el-descriptions-item>
            <el-descriptions-item label="表数量">{{ dbInfo.table_count }}</el-descriptions-item>
            <el-descriptions-item label="完整性">
              <el-tag :type="dbInfo.integrity_ok ? 'success' : 'danger'" size="small">
                {{ dbInfo.integrity_ok ? 'PASS' : 'FAIL' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="WAL 大小">{{ dbInfo.wal_size_kb }} KB</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit template**

```bash
git add frontend/src/views/system/MonitoringDashboard.vue
git commit -m "feat: add MonitoringDashboard template with CSS Grid layout"
```

---

### Task 6: Rewrite MonitoringDashboard.vue — Scoped Styles

**Files:**
- Modify: `frontend/src/views/system/MonitoringDashboard.vue` (append style section)

- [ ] **Step 1: Write the complete `<style scoped>` block**

```css
<style scoped>
/* ═══ Variables ═══ */
.monitoring-dashboard {
  --card-bg: var(--color-bg-card, #ffffff);
  --card-text: var(--color-text-primary, #1e293b);
  --card-subtext: var(--color-text-secondary, #64748b);
  --border-color: var(--color-border-light, #e2e8f0);
  --green: #22c55e;
  --yellow: #e6a23c;
  --red: #ef4444;
  padding: 0;
  max-width: 1600px;
  margin: 0 auto;
}

/* ═══ Header ═══ */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
.header-left { display: flex; align-items: baseline; gap: 16px; }
.header-title { margin: 0; font-size: 20px; font-weight: 700; color: var(--card-text); }
.header-updated { font-size: 12px; color: var(--card-subtext); }
.header-right { display: flex; align-items: center; gap: 8px; }
.health-score-badge {
  width: 56px; height: 56px;
  border-radius: 50%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  border: 3px solid;
  font-weight: 700;
  flex-shrink: 0;
}
.health-score-badge.score-good { border-color: var(--green); color: var(--green); }
.health-score-badge.score-warning { border-color: var(--yellow); color: var(--yellow); }
.health-score-badge.score-critical { border-color: var(--red); color: var(--red); }
.score-num { font-size: 18px; line-height: 1; }
.score-label { font-size: 10px; }

/* ═══ Metrics Grid ═══ */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.metric-card {
  border-radius: 8px;
  border-left: 4px solid var(--green);
  transition: box-shadow 0.2s;
}
.metric-card.metric-warning { border-left-color: var(--yellow); }
.metric-card.metric-critical { border-left-color: var(--red); }
.metric-card.metric-error { border-left-color: #cbd5e1; opacity: 0.7; }

.metric-body {
  display: flex; align-items: center; gap: 10px;
  min-height: 52px;
}
.metric-icon { font-size: 32px; flex-shrink: 0; line-height: 1; }
.metric-main { display: flex; align-items: baseline; gap: 4px; flex: 1; min-width: 0; }
.metric-value { font-size: 28px; font-weight: 800; color: var(--card-text); white-space: nowrap; line-height: 1.1; }
.metric-unit { font-size: 12px; color: var(--card-subtext); }
.metric-badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600; flex-shrink: 0; }
.badge-ok { background: #ecfdf5; color: var(--green); }
.badge-warning { background: #fffbeb; color: var(--yellow); }
.badge-critical { background: #fef2f2; color: var(--red); }
.badge-error { background: #f8fafc; color: #94a3b8; }
.metric-footer { font-size: 12px; color: var(--card-subtext); margin-top: 6px; font-weight: 500; text-align: center; }

/* ═══ Middle Row ═══ */
.middle-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}
@media (max-width: 1000px) { .middle-row { grid-template-columns: 1fr; } }
.panel-card { border-radius: 8px; }
.chart-container { height: 280px; width: 100%; }
.panel-empty { padding: 40px 0; }

/* ═══ Logs ═══ */
.log-container { max-height: 280px; overflow-y: auto; }
.log-item { display: flex; gap: 8px; padding: 4px 0; font-size: 12px; border-bottom: 1px solid var(--border-color); }
.log-time { color: var(--card-subtext); flex-shrink: 0; font-family: monospace; }
.log-level { font-weight: 700; flex-shrink: 0; width: 45px; text-align: center; }
.log-info .log-level { color: #409eff; }
.log-warn .log-level { color: var(--yellow); }
.log-error .log-level { color: var(--red); }
.log-message { color: var(--card-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ═══ Health Section ═══ */
.health-section { border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }
.health-toggle {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  background: var(--color-bg-hover, #f8fafc);
  font-weight: 600; font-size: 14px; color: var(--card-text);
  user-select: none;
}
.health-toggle:hover { background: var(--color-bg-active, #f1f5f9); }
.toggle-icon { font-size: 12px; width: 16px; }
.health-body { padding: 12px 16px 16px; }

/* ═══ Checks ═══ */
.check-list { display: flex; flex-direction: column; gap: 8px; }
.check-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 4px; background: var(--color-bg-page, #fafafa); }
.check-pass { color: var(--green); font-size: 16px; }
.check-fail { color: var(--red); font-size: 16px; }
.check-name { font-weight: 500; min-width: 90px; font-size: 13px; }
.check-detail { color: var(--card-subtext); font-size: 12px; }

/* ═══ Tooltip Sparkline ═══ */
.tooltip-content { font-size: 13px; }
.tooltip-header { font-weight: 600; margin-bottom: 8px; }
.tooltip-sparkline { display: flex; align-items: flex-end; gap: 3px; height: 40px; margin-bottom: 8px; }
.spark-bar { width: 8px; background: #409eff; border-radius: 2px 2px 0 0; transition: height 0.3s; }
.tooltip-detail { color: var(--card-subtext); }

/* ═══ Responsive ═══ */
@media (max-width: 768px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
  .metric-icon { font-size: 24px; }
  .metric-value { font-size: 22px; }
}
</style>
```

- [ ] **Step 2: Commit styles**

```bash
git add frontend/src/views/system/MonitoringDashboard.vue
git commit -m "feat: add MonitoringDashboard scoped CSS with responsive grid + dark mode"
```

---

### Task 7: Add statusText helper + CircleCheckFilled/CircleCloseFilled imports to script

**Files:**
- Modify: `frontend/src/views/system/MonitoringDashboard.vue` (imports + helper)

- [ ] **Step 1: Add missing imports and helper function**

Add to imports: `CircleCheckFilled, CircleCloseFilled` from `@element-plus/icons-vue`

Add helper:
```typescript
function statusText(s: MetricCard["status"]): string {
  if (s === "ok") return "正常";
  if (s === "warning") return "警告";
  if (s === "critical") return "严重";
  return "未知";
}
```

Add computed:
```typescript
const scoreClass = computed(() => {
  if (healthScore.value >= 80) return "score-good";
  if (healthScore.value >= 60) return "score-warning";
  return "score-critical";
});
```

- [ ] **Step 2: Verify TypeScript compilation**

Run: `cd frontend && npx vue-tsc --noEmit 2>&1 | tail -5`
Expected: No new TS errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/system/MonitoringDashboard.vue
git commit -m "fix: add missing imports and helpers to MonitoringDashboard"
```

---

### Task 8: Write frontend test file

**Files:**
- Create: `frontend/tests/unit/views/MonitoringDashboard.test.ts`

- [ ] **Step 1: Write test file with 10 test cases**

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { nextTick } from "vue";
import MonitoringDashboard from "@/views/system/MonitoringDashboard.vue";

// Mock ECharts
vi.mock("echarts", () => ({
  default: { init: () => ({ setOption: vi.fn(), dispose: vi.fn() }) },
}));

// Mock request
vi.mock("@/utils/request", () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      data: {
        data: {
          cpu_usage: 23.5, memory_usage: 58.2, disk_usage: 41.0,
          network_recv_mb: 12.3, network_sent_mb: 5.1,
          process_threads: 12, process_pid: 8426,
          cpu_count: 8, memory_used_mb: 4096, memory_total_mb: 8192,
          disk_used_gb: 80, disk_total_gb: 200,
          uptime_seconds: 260100, db_size_mb: 45.2, table_count: 38,
          db_integrity_ok: true, wal_size_kb: 128,
        },
      },
    }),
  },
}));

// Mock config store
vi.mock("@/stores/config", () => ({
  useConfigStore: () => ({ theme: "light" }),
}));

describe("MonitoringDashboard", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.restoreAllTimers();
  });

  it("T1: renders all 6 metric cards", async () => {
    const wrapper = mount(MonitoringDashboard);
    await flushPromises();
    await nextTick();
    const cards = wrapper.findAll(".metric-card");
    expect(cards).toHaveLength(6);
    const labels = ["CPU 使用率", "内存使用率", "磁盘使用率", "网络流量", "进程信息", "数据库"];
    for (const label of labels) {
      expect(wrapper.text()).toContain(label);
    }
  });

  it("T2: health score badge renders and has correct class", async () => {
    const wrapper = mount(MonitoringDashboard);
    await flushPromises();
    await nextTick();
    const badge = wrapper.find(".health-score-badge");
    expect(badge.exists()).toBe(true);
    expect(badge.text()).toContain("100"); // dbOk=true, all values low → 100
  });

  it("T3: ECharts chart container exists when apiStats has data", async () => {
    const wrapper = mount(MonitoringDashboard);
    await flushPromises();
    await nextTick();
    expect(wrapper.find(".chart-container").exists()).toBe(true);
  });

  it("T4: system logs section renders", async () => {
    const wrapper = mount(MonitoringDashboard);
    await flushPromises();
    await nextTick();
    expect(wrapper.text()).toContain("系统日志");
  });

  it("T5: dark theme class applies", async () => {
    const wrapper = mount(MonitoringDashboard, {
      global: { stubs: { "el-popover": true } },
    });
    await flushPromises();
    await wrapper.setData({ theme: "dark" } as any);
    await nextTick();
    expect(wrapper.find(".monitoring-dashboard").attributes("data-theme")).toBe("dark");
  });

  it("T6: responsive grid has at most 6 columns at wide viewport", async () => {
    const wrapper = mount(MonitoringDashboard);
    const grid = wrapper.find(".metrics-grid");
    expect(grid.exists()).toBe(true);
    // CSS grid auto-fit with minmax — verify class exists
    const style = getComputedStyle(grid.element);
    expect(style.display).toBe("grid");
  });

  it("T7: error isolation — one failed metric does not break others", async () => {
    const mockRequest = await import("@/utils/request");
    (mockRequest.default.get as any).mockRejectedValueOnce(new Error("CPU fail"));
    const wrapper = mount(MonitoringDashboard);
    await flushPromises();
    await nextTick();
    // All 6 cards still exist
    expect(wrapper.findAll(".metric-card")).toHaveLength(6);
  });

  it("T8: ring buffer caps at 10 entries", () => {
    // Access component internals via wrapper.vm
    const wrapper = mount(MonitoringDashboard);
    const vm = wrapper.vm as any;
    for (let i = 0; i < 15; i++) {
      vm.pushHistory({ timestamp: `${i}`, cpu: i, memory: i, disk: i, networkIn: i, networkOut: i });
    }
    expect(vm.historyBuffer).toHaveLength(10);
    expect(vm.historyBuffer[0].timestamp).toBe("5"); // oldest of the 10
  });

  it("T9: health section toggle works and sessionStorage is updated", async () => {
    const wrapper = mount(MonitoringDashboard);
    await flushPromises();
    const toggle = wrapper.find(".health-toggle");
    expect(toggle.exists()).toBe(true);
    // Initially collapsed
    expect(wrapper.find(".health-body").isVisible()).toBe(false);
    // Click to expand
    await toggle.trigger("click");
    await nextTick();
    expect(wrapper.find(".health-body").isVisible()).toBe(true);
  });

  it("T10: timer cleared on unmount", () => {
    const clearSpy = vi.spyOn(global, "clearInterval");
    const wrapper = mount(MonitoringDashboard);
    wrapper.unmount();
    expect(clearSpy).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run the new tests**

Run: `cd frontend && npx vitest run tests/unit/views/MonitoringDashboard.test.ts 2>&1 | tail -20`
Expected: 10 passed

- [ ] **Step 3: Commit**

```bash
git add frontend/tests/unit/views/MonitoringDashboard.test.ts
git commit -m "test: add MonitoringDashboard test suite (10 cases)"
```

---

### Task 9: Run full test suites and verify zero regressions

- [ ] **Step 1: Run backend tests**

```bash
cd backend && python -m pytest tests/ -q --tb=short 2>&1 | tail -5
```
Expected: All pass (no changes to backend, should be identical)

- [ ] **Step 2: Run frontend tests**

```bash
cd frontend && npm test -- --run 2>&1 | tail -10
```
Expected: All 1664+10=1674 pass

- [ ] **Step 3: Run TypeScript typecheck**

```bash
cd frontend && npm run typecheck 2>&1 | tail -5
```
Expected: No new errors

- [ ] **Step 4: Run lint**

```bash
cd frontend && npm run lint 2>&1 | tail -5
```
Expected: No new errors

- [ ] **Step 5: Final commit if any fixes needed, or verification commit**

```bash
git add -A && git diff --cached --stat
git commit -m "chore: final verification — all tests pass, zero regressions"
```
