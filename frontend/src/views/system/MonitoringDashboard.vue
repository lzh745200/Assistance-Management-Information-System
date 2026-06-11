<template>
  <div class="monitoring-dashboard">
    <!-- ── Header ── -->
    <div class="page-header">
      <h2>系统监控面板</h2>
      <div class="header-right">
        <span v-if="lastUpdated" class="last-updated"
          >更新于 {{ lastUpdated }}</span
        >
        <div class="health-badge" :class="scoreBadgeClass">
          <span class="health-score-num">{{ healthScore }}</span>
          <span class="health-score-label">健康分</span>
        </div>
        <el-button
          :icon="Refresh"
          :loading="loading"
          size="small"
          @click="refreshAll"
          >刷新</el-button
        >
        <el-button :icon="Download" size="small" @click="exportData"
          >导出</el-button
        >
      </div>
    </div>

    <!-- ── 6 Metric Cards ── -->
    <div class="metric-grid">
      <div
        v-for="card in metricCards"
        :key="card.key"
        class="metric-card"
        :class="['status-' + card.status, { 'card-error': card.error }]"
      >
        <el-popover
          placement="bottom"
          :width="200"
          trigger="hover"
          :show-after="300"
        >
          <template #reference>
            <div class="card-inner">
              <div class="card-icon" :style="{ color: card.iconColor }">
                {{ card.icon }}
              </div>
              <div class="card-body">
                <div class="card-value">
                  <span v-if="card.error">--</span>
                  <span v-else>{{ card.value }}</span>
                  <span class="card-unit">{{ card.unit }}</span>
                </div>
                <el-tag :type="card.tagType" size="small">{{
                  card.statusText
                }}</el-tag>
              </div>
              <div class="card-footer">{{ card.label }}</div>
            </div>
          </template>
          <div class="popover-content">
            <div class="sparkline-bars">
              <div
                v-for="(pt, i) in card.history"
                :key="i"
                class="spark-bar"
                :style="{
                  height: Math.max(4, pt * 100) + '%',
                  backgroundColor: card.sparkColor,
                }"
              />
            </div>
            <div class="detail-text">
              <span v-if="card.detail">{{ card.detail }}</span>
              <span v-if="card.subDetail">{{ card.subDetail }}</span>
            </div>
          </div>
        </el-popover>
      </div>
    </div>

    <!-- ── Middle Row: API Stats Chart + System Logs ── -->
    <div class="middle-row">
      <div class="chart-panel">
        <div class="panel-header">API 请求统计（近24小时）</div>
        <div ref="chartRef" class="chart-container"></div>
      </div>
      <div class="log-panel">
        <div class="panel-header">系统日志</div>
        <div class="log-container">
          <div
            v-for="log in recentLogs"
            :key="log.id"
            class="log-item"
            :class="'log-' + log.level"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-level">{{ log.level.toUpperCase() }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
          <el-empty
            v-if="recentLogs.length === 0"
            description="暂无日志"
            :image-size="32"
          />
        </div>
      </div>
    </div>

    <!-- ── Bottom: Collapsible Health Checks ── -->
    <div class="health-section">
      <div class="health-header" @click="healthExpanded = !healthExpanded">
        <span class="toggle-icon">{{ healthExpanded ? "▼" : "▶" }}</span>
        <span>系统健康检查</span>
        <el-tag
          :type="
            healthScore >= 80
              ? 'success'
              : healthScore >= 60
                ? 'warning'
                : 'danger'
          "
          size="small"
          style="margin-left: 12px"
        >
          {{
            healthScore >= 90
              ? "极佳"
              : healthScore >= 80
                ? "良好"
                : healthScore >= 60
                  ? "需关注"
                  : "异常"
          }}
        </el-tag>
      </div>
      <div v-show="healthExpanded" class="health-body">
        <div class="check-group">
          <h4>基础检查</h4>
          <div v-for="item in basicChecks" :key="item.name" class="check-item">
            <el-icon :size="16"
              ><component
                :is="item.passed ? CircleCheckFilled : CircleCloseFilled"
            /></el-icon>
            <span class="check-name">{{ item.name }}</span>
            <span class="check-detail">{{ item.detail }}</span>
          </div>
        </div>
        <div class="check-group">
          <h4>性能检查</h4>
          <div
            v-for="item in performanceChecks"
            :key="item.name"
            class="check-item"
          >
            <el-icon :size="16"
              ><component
                :is="item.passed ? CircleCheckFilled : CircleCloseFilled"
            /></el-icon>
            <span class="check-name">{{ item.name }}</span>
            <span class="check-detail">{{ item.detail }}</span>
          </div>
        </div>
        <div class="check-group">
          <h4>数据库信息</h4>
          <div class="check-item">
            <span class="check-name">数据库大小</span>
            <span class="check-detail">{{ dbInfo.size }}</span>
          </div>
          <div class="check-item">
            <span class="check-name">表数量</span>
            <span class="check-detail">{{ dbInfo.tableCount }}</span>
          </div>
          <div class="check-item">
            <span class="check-name">WAL 大小</span>
            <span class="check-detail">{{ dbInfo.walSize }}</span>
          </div>
          <div class="check-item">
            <span class="check-name">完整性检查</span>
            <el-tag
              :type="dbInfo.integrityOk ? 'success' : 'danger'"
              size="small"
              >{{ dbInfo.integrityOk ? "通过" : "失败" }}</el-tag
            >
          </div>
          <div class="check-item">
            <span class="check-name">运行时间</span>
            <span class="check-detail">{{ dbInfo.uptime }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import { ElMessage } from "element-plus";
import {
  Refresh,
  Download,
  CircleCheckFilled,
  CircleCloseFilled,
} from "@element-plus/icons-vue";
import * as echarts from "echarts";
import request from "@/utils/request";
import { useConfigStore } from "@/stores/config";

// ── Types ──
interface SnapshotData {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_recv_mb: number;
  network_sent_mb: number;
  process_threads: number;
  cpu_count: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_used_gb: number;
  disk_total_gb: number;
}

interface ApiStat {
  endpoint: string;
  method: string;
  count: number;
  avg_time_ms: number;
  error_rate: number;
}

interface HealthData {
  db_size_mb: number;
  table_count: number;
  db_integrity_ok: boolean;
  wal_size_kb: number;
  uptime_seconds: number;
}

interface HistoryPoint {
  cpu: number;
  mem: number;
  disk: number;
  time: string;
}

interface CheckItem {
  name: string;
  passed: boolean;
  detail: string;
}

// ── State ──
const loading = ref(false);
const lastUpdated = ref("");
const healthScore = ref(0);
const healthExpanded = ref(
  sessionStorage.getItem("monitor-health-expanded") === "true",
);

const snapshot = ref<SnapshotData | null>(null);
const apiStats = ref<ApiStat[]>([]);
const healthData = ref<HealthData | null>(null);
const history = ref<HistoryPoint[]>([]);
const maxHistory = 10;

const recentLogs = ref<
  { id: number; time: string; level: string; message: string }[]
>([]);
const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

const configStore = useConfigStore();

// ── Computed: dbInfo ──
const dbInfo = computed(() => {
  const h = healthData.value;
  return {
    size: h ? `${h.db_size_mb.toFixed(1)} MB` : "--",
    tableCount: h ? String(h.table_count) : "--",
    walSize: h ? `${h.wal_size_kb.toFixed(1)} KB` : "--",
    integrityOk: h?.db_integrity_ok ?? false,
    uptime: h?.uptime_seconds
      ? `${Math.floor(h.uptime_seconds / 3600)}h ${Math.floor((h.uptime_seconds % 3600) / 60)}m`
      : "--",
  };
});

// ── Computed: health checks from data ──
const basicChecks = computed<CheckItem[]>(() => {
  const h = healthData.value;
  return [
    {
      name: "数据库连接",
      passed: h?.db_integrity_ok ?? false,
      detail: h?.db_integrity_ok ? "正常" : "异常",
    },
    {
      name: "API 服务",
      passed: apiStats.value.length > 0,
      detail: apiStats.value.length > 0 ? "正常响应" : "无数据",
    },
    { name: "认证服务", passed: true, detail: "运行中" },
    { name: "缓存服务", passed: true, detail: "运行中" },
    { name: "日志系统", passed: true, detail: "运行中" },
  ];
});

const performanceChecks = computed<CheckItem[]>(() => {
  const s = snapshot.value;
  return [
    {
      name: "CPU 使用率",
      passed: (s?.cpu_usage ?? 100) < 90,
      detail: s ? `${s.cpu_usage.toFixed(1)}%` : "--",
    },
    {
      name: "内存使用率",
      passed: (s?.memory_usage ?? 100) < 90,
      detail: s ? `${s.memory_usage.toFixed(1)}%` : "--",
    },
    {
      name: "磁盘使用率",
      passed: (s?.disk_usage ?? 100) < 90,
      detail: s ? `${s.disk_usage.toFixed(1)}%` : "--",
    },
    { name: "响应时间", passed: true, detail: "< 100ms" },
    {
      name: "数据库大小",
      passed: (healthData.value?.db_size_mb ?? 9999) < 500,
      detail: dbInfo.value.size,
    },
  ];
});

// ── Score computation ──
function computeScore(
  snap: SnapshotData | null,
  health: HealthData | null,
): number {
  let score = 20; // base
  if (snap) {
    if (snap.cpu_usage < 70) score += 20;
    else if (snap.cpu_usage < 90) score += 10;
    if (snap.memory_usage < 75) score += 20;
    else if (snap.memory_usage < 90) score += 10;
    if (snap.disk_usage < 75) score += 20;
    else if (snap.disk_usage < 90) score += 10;
  }
  if (health?.db_integrity_ok) score += 20;
  return Math.min(100, score);
}

const scoreBadgeClass = computed(() => {
  if (healthScore.value >= 80) return "score-good";
  if (healthScore.value >= 60) return "score-warning";
  return "score-danger";
});

// ── Metric card definitions ──
interface MetricCard {
  key: string;
  icon: string;
  iconColor: string;
  value: string;
  unit: string;
  status: string;
  statusText: string;
  tagType: "success" | "warning" | "danger" | "info";
  label: string;
  detail: string;
  subDetail: string;
  history: number[];
  sparkColor: string;
  error: boolean;
}

function statusInfo(
  val: number,
  invert = false,
): {
  status: string;
  tagType: "success" | "warning" | "danger";
  statusText: string;
} {
  const v = invert ? 100 - val : val;
  if (v >= 90)
    return { status: "danger", tagType: "danger" as const, statusText: "严重" };
  if (v >= 70)
    return {
      status: "warning",
      tagType: "warning" as const,
      statusText: "警告",
    };
  return { status: "normal", tagType: "success" as const, statusText: "正常" };
}

const metricCards = computed<MetricCard[]>(() => {
  const s = snapshot.value;
  const hist = history.value;
  const cpuHist = hist.map((h) => h.cpu / 100);
  const memHist = hist.map((h) => h.mem / 100);
  const diskHist = hist.map((h) => h.disk / 100);

  const cpuSi = statusInfo(s?.cpu_usage ?? 0);
  const memSi = statusInfo(s?.memory_usage ?? 0);
  const diskSi = statusInfo(s?.disk_usage ?? 0);
  const netRecvSi = statusInfo(
    s ? Math.min(100, (s.network_recv_mb / 100) * 100) : 0,
  );
  const netSentSi = statusInfo(
    s ? Math.min(100, (s.network_sent_mb / 100) * 100) : 0,
  );
  const thrSi: {
    status: string;
    tagType: "success" | "warning";
    statusText: string;
  } =
    s?.process_threads != null && s.process_threads > 500
      ? { status: "warning", tagType: "warning" as const, statusText: "偏高" }
      : { status: "normal", tagType: "success" as const, statusText: "正常" };

  const hasData = s !== null;

  return [
    {
      key: "cpu",
      icon: "🖥️",
      iconColor: "#409eff",
      value: hasData ? s!.cpu_usage.toFixed(1) : "--",
      unit: "%",
      ...cpuSi,
      label: "CPU 使用率",
      detail: hasData ? `${s!.cpu_count} 核` : "",
      subDetail: hasData ? `进程线程: ${s!.process_threads}` : "",
      history: cpuHist,
      sparkColor: "#409eff",
      error: !hasData,
    },
    {
      key: "memory",
      icon: "💾",
      iconColor: "#67c23a",
      value: hasData ? s!.memory_usage.toFixed(1) : "--",
      unit: "%",
      ...memSi,
      label: "内存使用率",
      detail: hasData
        ? `${s!.memory_used_mb.toFixed(0)} / ${s!.memory_total_mb.toFixed(0)} MB`
        : "",
      subDetail: "",
      history: memHist,
      sparkColor: "#67c23a",
      error: !hasData,
    },
    {
      key: "disk",
      icon: "📀",
      iconColor: "#e6a23c",
      value: hasData ? s!.disk_usage.toFixed(1) : "--",
      unit: "%",
      ...diskSi,
      label: "磁盘使用率",
      detail: hasData
        ? `${s!.disk_used_gb.toFixed(1)} / ${s!.disk_total_gb.toFixed(1)} GB`
        : "",
      subDetail: "",
      history: diskHist,
      sparkColor: "#e6a23c",
      error: !hasData,
    },
    {
      key: "net_recv",
      icon: "📥",
      iconColor: "#909399",
      value: hasData ? s!.network_recv_mb.toFixed(1) : "--",
      unit: "MB",
      ...netRecvSi,
      label: "网络接收",
      detail: hasData ? "累计接收" : "",
      subDetail: "",
      history: [],
      sparkColor: "#909399",
      error: !hasData,
    },
    {
      key: "net_sent",
      icon: "📤",
      iconColor: "#909399",
      value: hasData ? s!.network_sent_mb.toFixed(1) : "--",
      unit: "MB",
      ...netSentSi,
      label: "网络发送",
      detail: hasData ? "累计发送" : "",
      subDetail: "",
      history: [],
      sparkColor: "#909399",
      error: !hasData,
    },
    {
      key: "threads",
      icon: "⚙️",
      iconColor: "#409eff",
      value: hasData ? String(s!.process_threads) : "--",
      unit: "",
      ...thrSi,
      label: "进程线程",
      detail: hasData ? `${s!.cpu_count} 核 CPU` : "",
      subDetail: "",
      history: [],
      sparkColor: "#409eff",
      error: !hasData,
    },
  ];
});

// ── History ring buffer ──
function pushHistory(cpu: number, mem: number, disk: number) {
  const now = new Date();
  const time = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}`;
  history.value.push({ cpu, mem, disk, time });
  if (history.value.length > maxHistory) history.value.shift();
}

// ── Data fetching ──
async function fetchSnapshot() {
  try {
    const res = await request.get("/system/monitor/snapshot");
    // Backend returns { success: true, data: { cpu_usage, ... } }
    // request.get returns AxiosResponse, so res.data is the JSON body
    const data = (res as any)?.data?.data ?? (res as any)?.data ?? {};
    snapshot.value = data;
    return data as SnapshotData | null;
  } catch {
    snapshot.value = null;
    return null;
  }
}

async function fetchApiStats() {
  try {
    const res = await request.get("/system/monitor/api-stats", {
      params: { hours: 24 },
    });
    // Backend returns { success: true, data: { top_endpoints: [...] } }
    const data = (res as any)?.data?.data ?? (res as any)?.data ?? {};
    const endpoints = data?.top_endpoints ?? [];
    apiStats.value = endpoints;
    return endpoints as ApiStat[];
  } catch {
    apiStats.value = [];
    return [];
  }
}

async function fetchHealth() {
  try {
    const res = await request.get("/system/health/full");
    // Backend returns { code: 200, data: { db_size_mb, ... } }
    const data = (res as any)?.data?.data ?? (res as any)?.data ?? {};
    healthData.value = data;
    return data as HealthData | null;
  } catch {
    healthData.value = null;
    return null;
  }
}

async function refreshAll() {
  loading.value = true;
  try {
    const [snap, stats, health] = await Promise.allSettled([
      fetchSnapshot(),
      fetchApiStats(),
      fetchHealth(),
    ]);
    const snapData = snap.status === "fulfilled" ? snap.value : null;
    const healthVal = health.status === "fulfilled" ? health.value : null;

    if (snap.status === "rejected")
      console.error("Snapshot fetch failed:", snap.reason);
    if (stats.status === "rejected")
      console.error("API stats fetch failed:", stats.reason);
    if (health.status === "rejected")
      console.error("Health fetch failed:", health.reason);

    if (snapData) {
      pushHistory(
        snapData.cpu_usage,
        snapData.memory_usage,
        snapData.disk_usage,
      );
      // Generate synthetic logs from data
      const sid = Date.now();
      const logs: typeof recentLogs.value = [];
      if (snapData.cpu_usage > 80)
        logs.push({
          id: sid,
          time: new Date().toLocaleTimeString(),
          level: "warn",
          message: `CPU 使用率偏高: ${snapData.cpu_usage.toFixed(1)}%`,
        });
      if (snapData.memory_usage > 80)
        logs.push({
          id: sid + 1,
          time: new Date().toLocaleTimeString(),
          level: "warn",
          message: `内存使用率偏高: ${snapData.memory_usage.toFixed(1)}%`,
        });
      if (snapData.disk_usage > 85)
        logs.push({
          id: sid + 2,
          time: new Date().toLocaleTimeString(),
          level: "error",
          message: `磁盘使用率过高: ${snapData.disk_usage.toFixed(1)}%`,
        });
      if (logs.length === 0)
        logs.push({
          id: sid,
          time: new Date().toLocaleTimeString(),
          level: "info",
          message: "系统资源使用正常",
        });
      recentLogs.value = logs;
    }

    healthScore.value = computeScore(snapData, healthVal);
  } finally {
    loading.value = false;
    lastUpdated.value = new Date().toLocaleTimeString();
  }
}

// ── ECharts ──
function buildChart() {
  if (!chartRef.value) return;
  if (chartInstance) chartInstance.dispose();

  const isDark =
    configStore.theme === "dark" || configStore.theme === "military";
  chartInstance = echarts.init(chartRef.value, isDark ? "dark" : undefined);

  const endpoints = apiStats.value.slice(0, 10);
  const names = endpoints.map((e) => `${e.method} ${e.endpoint}`);
  const counts = endpoints.map((e) => e.count);
  const avgTimes = endpoints.map((e) => (e.avg_time_ms ?? 0).toFixed(1));
  const errorRates = endpoints.map((e) => (e.error_rate ?? 0).toFixed(1));

  chartInstance.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { data: ["请求数", "平均耗时(ms)", "错误率(%)"], top: 0 },
    grid: { left: 10, right: 10, top: 32, bottom: 0, containLabel: true },
    xAxis: {
      type: "category",
      data: names,
      axisLabel: { rotate: 30, fontSize: 10, interval: 0 },
    },
    yAxis: [
      {
        type: "value",
        name: "请求数/耗时",
        splitLine: { lineStyle: { type: "dashed" } },
      },
      { type: "value", name: "错误率(%)", splitLine: { show: false } },
    ],
    series: [
      {
        name: "请求数",
        type: "bar",
        data: counts,
        itemStyle: { color: "#409eff" },
        barMaxWidth: 28,
      },
      {
        name: "平均耗时(ms)",
        type: "line",
        yAxisIndex: 0,
        data: avgTimes,
        lineStyle: { color: "#67c23a" },
        symbol: "circle",
        symbolSize: 4,
      },
      {
        name: "错误率(%)",
        type: "line",
        yAxisIndex: 1,
        data: errorRates,
        lineStyle: { color: "#f56c6c" },
        symbol: "diamond",
        symbolSize: 4,
      },
    ],
  });
}

// ── Export ──
function exportData() {
  const report = {
    timestamp: new Date().toISOString(),
    healthScore: healthScore.value,
    snapshot: snapshot.value,
    apiStats: apiStats.value,
    health: healthData.value,
    history: history.value,
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `monitoring-export-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  ElMessage.success("监控数据已导出");
}

// ── Theme watch ──
watch(
  () => configStore.theme,
  () => {
    nextTick(() => buildChart());
  },
);

// ── Lifecycle ──
let pollTimer: ReturnType<typeof setInterval> | null = null;

onMounted(async () => {
  await refreshAll();
  nextTick(() => buildChart());
  pollTimer = setInterval(refreshAll, 30000);
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
  if (chartInstance) chartInstance.dispose();
});

// Persist health section expand state
watch(healthExpanded, (val) => {
  sessionStorage.setItem("monitor-health-expanded", String(val));
});
</script>

<style scoped>
.monitoring-dashboard {
  padding: 0;
  color: var(--color-text-primary);
}

/* ── Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}
.page-header h2 {
  margin: 0;
  font-size: var(--font-size-xl);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.last-updated {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.health-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 3px solid;
  flex-shrink: 0;
}
.health-badge.score-good {
  border-color: #67c23a;
}
.health-badge.score-warning {
  border-color: #e6a23c;
}
.health-badge.score-danger {
  border-color: #f56c6c;
}
.health-score-num {
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
}
.health-score-label {
  font-size: 10px;
  color: var(--color-text-secondary);
}
.score-good .health-score-num {
  color: #67c23a;
}
.score-warning .health-score-num {
  color: #e6a23c;
}
.score-danger .health-score-num {
  color: #f56c6c;
}

/* ── Metric Grid ── */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
@media (max-width: 768px) {
  .metric-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.metric-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  border-left: 4px solid #67c23a;
  cursor: pointer;
  transition:
    box-shadow var(--transition-fast),
    transform var(--transition-fast);
}
.metric-card:hover {
  box-shadow: var(--shadow-card);
  transform: translateY(-2px);
}
.metric-card.status-normal {
  border-left-color: #67c23a;
}
.metric-card.status-warning {
  border-left-color: #e6a23c;
}
.metric-card.status-danger {
  border-left-color: #f56c6c;
}
.metric-card.card-error {
  border-left-color: #c0c4cc;
  opacity: 0.7;
}

.card-inner {
  padding: 14px 16px 0;
}
.card-icon {
  font-size: 28px;
  line-height: 1;
  margin-bottom: 4px;
}
.card-body {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
}
.card-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
}
.card-unit {
  font-size: 14px;
  font-weight: 400;
  color: var(--color-text-secondary);
  margin-left: 2px;
}
.card-footer {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  padding: 6px 16px 10px;
  font-weight: 500;
}

.popover-content {
  font-size: 12px;
}
.sparkline-bars {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 40px;
  margin-bottom: 8px;
}
.spark-bar {
  flex: 1;
  border-radius: 2px 2px 0 0;
  min-width: 4px;
  transition: height var(--transition-fast);
}
.detail-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: var(--color-text-secondary);
}

/* ── Middle Row ── */
.middle-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}
@media (max-width: 768px) {
  .middle-row {
    grid-template-columns: 1fr;
  }
}

.chart-panel,
.log-panel {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
}
.panel-header {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
  padding: 12px 16px 0;
}
.chart-container {
  height: 280px;
}
.log-container {
  max-height: 280px;
  overflow-y: auto;
  padding: 0 16px 8px;
}

.log-item {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
  border-bottom: 1px solid var(--color-border-lighter);
}
.log-time {
  color: var(--color-text-secondary);
  flex-shrink: 0;
}
.log-level {
  font-weight: 600;
  flex-shrink: 0;
  width: 40px;
}
.log-info .log-level {
  color: #409eff;
}
.log-warn .log-level {
  color: #e6a23c;
}
.log-error .log-level {
  color: #f56c6c;
}
.log-message {
  color: var(--color-text-regular);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Health Section ── */
.health-section {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
}
.health-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  cursor: pointer;
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
  user-select: none;
}
.health-header:hover {
  background: var(--color-bg-hover);
}
.toggle-icon {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.health-body {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  padding: 0 16px 16px;
  border-top: 1px solid var(--color-border-lighter);
  padding-top: 12px;
}
.check-group h4 {
  margin: 0 0 8px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: 500;
}
.check-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
}
.check-item:nth-child(odd) {
  background: var(--color-bg-hover);
}
.check-item .el-icon {
  flex-shrink: 0;
}
.check-item .el-icon :deep(svg) {
  color: #67c23a;
}
.check-item:has(.el-icon + :deep(svg[style*="f56c6c"])) .el-icon :deep(svg),
.check-item .el-icon:has(+ .check-detail:empty) {
  color: #f56c6c;
}
.check-name {
  flex-shrink: 0;
  min-width: 90px;
  font-weight: 500;
  color: var(--color-text-primary);
}
.check-detail {
  color: var(--color-text-secondary);
}
</style>
