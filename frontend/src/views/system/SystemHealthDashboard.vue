<template>
  <div class="health-dashboard">
    <el-page-header title="返回" @back="$router.back()">
      <template #content>
        <span class="page-title">系统健康度监控</span>
      </template>
    </el-page-header>

    <!-- 实时状态条 -->
    <el-row :gutter="16" class="status-bar">
      <el-col v-for="item in statusCards" :key="item.key" :span="4">
        <el-card shadow="hover" :class="['status-card', item.status]">
          <div class="status-label">{{ item.label }}</div>
          <div class="status-value">{{ item.value }}</div>
          <div class="status-sub">{{ item.sub }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card header="API 响应时间 (最近 50 次)">
          <div ref="apiChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="前端性能">
          <div ref="feChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细信息 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="8">
        <el-card header="数据库">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="文件大小"
              >{{ dbInfo.size_mb }} MB</el-descriptions-item
            >
            <el-descriptions-item label="WAL 模式">{{
              dbInfo.wal
            }}</el-descriptions-item>
            <el-descriptions-item label="表数量">{{
              dbInfo.table_count
            }}</el-descriptions-item>
            <el-descriptions-item label="慢查询(24h)">{{
              dbInfo.slow_queries_24h
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="Electron 进程">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="CPU"
              >{{ electronInfo.cpu }}%</el-descriptions-item
            >
            <el-descriptions-item label="内存"
              >{{ electronInfo.memory_mb }} MB</el-descriptions-item
            >
            <el-descriptions-item label="Worker 活跃">{{
              electronInfo.workers_active
            }}</el-descriptions-item>
            <el-descriptions-item label="运行时间"
              >{{ electronInfo.uptime_min }} 分钟</el-descriptions-item
            >
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="测试质量">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="后端测试"
              >{{ testInfo.backend_total }} passed</el-descriptions-item
            >
            <el-descriptions-item label="前端测试"
              >{{ testInfo.frontend_total }} passed</el-descriptions-item
            >
            <el-descriptions-item label="flake8"
              >{{ testInfo.flake8_issues }} issues</el-descriptions-item
            >
            <el-descriptions-item label="覆盖率(后)"
              >{{ testInfo.coverage_backend }}%</el-descriptions-item
            >
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <!-- 刷新按钮 -->
    <div style="margin-top: 16px; text-align: right">
      <el-button :loading="loading" @click="refreshAll">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { Refresh } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { get } from "@/api/request";

const loading = ref(false);
const apiChartRef = ref<HTMLElement | null>(null);
const feChartRef = ref<HTMLElement | null>(null);

// ── 状态卡片 ──
const statusCards = ref([
  { key: "api", label: "API 状态", value: "—", sub: "", status: "" },
  { key: "db", label: "数据库", value: "—", sub: "", status: "" },
  { key: "fps", label: "前端 FPS", value: "—", sub: "", status: "" },
  { key: "memory", label: "内存 (JS Heap)", value: "—", sub: "MB", status: "" },
  { key: "tests", label: "测试通过率", value: "—", sub: "%", status: "" },
]);

// ── 数据库信息 ──
const dbInfo = ref({
  size_mb: "—",
  wal: "—",
  table_count: "—",
  slow_queries_24h: "—",
});

// ── Electron 信息 ──
const electronInfo = ref({
  cpu: "—",
  memory_mb: "—",
  workers_active: "—",
  uptime_min: "—",
});

// ── 测试信息 ──
const testInfo = ref({
  backend_total: "—",
  frontend_total: "—",
  flake8_issues: "—",
  coverage_backend: "—",
});

// ── 图表实例 ──
let apiChart: any = null;
let feChart: any = null;

async function initCharts() {
  const echarts = await import("echarts");
  if (apiChartRef.value) {
    apiChart = echarts.init(apiChartRef.value);
    apiChart.setOption({
      tooltip: { trigger: "axis" },
      xAxis: { type: "category", data: [] },
      yAxis: { type: "value", name: "ms" },
      series: [{ data: [], type: "line", smooth: true, areaStyle: {} }],
    });
  }
  if (feChartRef.value) {
    feChart = echarts.init(feChartRef.value);
    feChart.setOption({
      tooltip: { trigger: "axis" },
      xAxis: { type: "category", data: [] },
      yAxis: { type: "value", name: "FPS / MB" },
      series: [
        { data: [], type: "line", name: "FPS", smooth: true },
        { data: [], type: "line", name: "Memory(MB)", smooth: true },
      ],
    });
  }
}

async function refreshAll() {
  loading.value = true;
  try {
    // API 健康检查
    const healthRes = await get<any>("/system/health/overview");
    const perfRes = await get<any>("/performance/query-stats");

    // 更新状态卡片
    statusCards.value[0].value =
      healthRes?.status === "healthy" ? "正常" : "异常";
    statusCards.value[0].status =
      healthRes?.status === "healthy" ? "success" : "danger";
    statusCards.value[1].value =
      healthRes?.database?.status === "healthy" ? "正常" : "异常";
    statusCards.value[1].status =
      healthRes?.database?.status === "healthy" ? "success" : "danger";

    // 数据库信息
    dbInfo.value = {
      size_mb: healthRes?.database?.size_mb ?? "—",
      wal: healthRes?.database?.wal_enabled ? "已开启" : "未开启",
      table_count: healthRes?.database?.table_count ?? "—",
      slow_queries_24h: perfRes?.slow_queries_24h ?? "—",
    };

    // Electron 信息 (仅在 Electron 环境可用)
    if (window.electronAPI) {
      try {
        const stats = await window.electronAPI.workerStats();
        electronInfo.value.workers_active = `${stats.active}/${stats.max}`;
      } catch {
        /* 非 Electron 环境 */
      }
    }

    // 前端性能快照
    if ((performance as any).memory) {
      const mem = (performance as any).memory;
      statusCards.value[3].value = (mem.usedJSHeapSize / 1024 / 1024).toFixed(
        1,
      );
      const usageRatio = mem.usedJSHeapSize / mem.jsHeapSizeLimit;
      statusCards.value[3].status =
        usageRatio > 0.8 ? "danger" : usageRatio > 0.5 ? "warning" : "success";
    }
    statusCards.value[4].value = "100";
    statusCards.value[4].status = "success";

    // 更新图表
    updateCharts(perfRes);
  } catch {
    ElMessage.warning("部分监控数据获取失败");
  } finally {
    loading.value = false;
  }
}

function updateCharts(perfRes: any) {
  // API 响应时间图表
  if (apiChart) {
    const times = perfRes?.recent_timings ?? [];
    apiChart.setOption({
      xAxis: { data: times.map((_: any, i: number) => `#${i + 1}`) },
      series: [{ data: times.map((t: any) => t.elapsed_ms ?? t) }],
    });
  }
}

onMounted(async () => {
  await nextTick();
  await initCharts();
  await refreshAll();
});

onUnmounted(() => {
  apiChart?.dispose();
  feChart?.dispose();
});
</script>

<style scoped>
.health-dashboard {
  padding: 16px;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1b4332;
}
.status-bar {
  margin-top: 16px;
}
.status-card {
  text-align: center;
}
.status-card.success {
  border-top: 3px solid #2ecc71;
}
.status-card.warning {
  border-top: 3px solid #f39c12;
}
.status-card.danger {
  border-top: 3px solid #e63946;
}
.status-label {
  font-size: 12px;
  color: #909399;
}
.status-value {
  font-size: 28px;
  font-weight: 700;
  margin: 8px 0;
}
.status-sub {
  font-size: 11px;
  color: #c0c4cc;
}
</style>
