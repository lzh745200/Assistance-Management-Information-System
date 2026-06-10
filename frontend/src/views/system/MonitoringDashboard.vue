<template>
  <div class="monitoring-dashboard">
    <div class="page-header">
      <h2>系统监控面板</h2>
      <el-button :icon="Refresh" :loading="loading" @click="refreshData"
        >刷新</el-button
      >
    </div>

    <!-- 概览卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon cpu-icon">🖥️</div>
            <div class="stat-info">
              <div class="stat-value">{{ systemStats.cpuUsage }}%</div>
              <div class="stat-label">CPU 使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon mem-icon">💾</div>
            <div class="stat-info">
              <div class="stat-value">{{ systemStats.memoryUsage }}%</div>
              <div class="stat-label">内存使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon disk-icon">📀</div>
            <div class="stat-info">
              <div class="stat-value">{{ systemStats.diskUsage }}%</div>
              <div class="stat-label">磁盘使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon uptime-icon">⏱️</div>
            <div class="stat-info">
              <div class="stat-value">{{ systemStats.uptime }}</div>
              <div class="stat-label">运行时间</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细监控 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :xs="24" :sm="12">
        <el-card>
          <template #header>
            <span>API 请求统计</span>
          </template>
          <el-table :data="apiStats" stripe size="small">
            <el-table-column prop="endpoint" label="接口" />
            <el-table-column prop="method" label="方法" width="80" />
            <el-table-column prop="count" label="请求数" width="80" />
            <el-table-column prop="avgTime" label="平均耗时" width="100" />
            <el-table-column prop="errorRate" label="错误率" width="80">
              <template #default="{ row }">
                <el-tag
                  :type="row.errorRate > 5 ? 'danger' : 'success'"
                  size="small"
                >
                  {{ row.errorRate }}%
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card>
          <template #header>
            <span>系统日志</span>
          </template>
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
            <div v-if="recentLogs.length === 0" class="empty-logs">
              <el-empty description="暂无日志" :image-size="40" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据库状态 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <span>数据库状态</span>
      </template>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="数据库大小">{{
          dbStats.size
        }}</el-descriptions-item>
        <el-descriptions-item label="表数量">{{
          dbStats.tableCount
        }}</el-descriptions-item>
        <el-descriptions-item label="连接数">{{
          dbStats.connections
        }}</el-descriptions-item>
        <el-descriptions-item label="完整性检查">
          <el-tag :type="dbStats.integrity === 'ok' ? 'success' : 'danger'">
            {{ dbStats.integrity }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { ElMessage } from "element-plus";
import { Refresh } from "@element-plus/icons-vue";
import request from "@/utils/request";

const loading = ref(false);

const systemStats = ref({
  cpuUsage: 0,
  memoryUsage: 0,
  diskUsage: 0,
  uptime: "0h 0m",
});

const apiStats = ref([
  {
    endpoint: "/api/v1/auth/login",
    method: "POST",
    count: 0,
    avgTime: "0ms",
    errorRate: 0,
  },
  {
    endpoint: "/api/v1/projects",
    method: "GET",
    count: 0,
    avgTime: "0ms",
    errorRate: 0,
  },
  {
    endpoint: "/api/v1/funds",
    method: "GET",
    count: 0,
    avgTime: "0ms",
    errorRate: 0,
  },
  {
    endpoint: "/api/v1/system/health",
    method: "GET",
    count: 0,
    avgTime: "0ms",
    errorRate: 0,
  },
]);

const recentLogs = ref<
  Array<{ id: number; time: string; level: string; message: string }>
>([]);

const dbStats = ref({
  size: "-",
  tableCount: "-",
  connections: "-",
  integrity: "-",
});

let refreshTimer: ReturnType<typeof setInterval> | null = null;

async function refreshData() {
  loading.value = true;
  try {
    // Fetch system health from API
    const res = await request.get("/system/health/full");
    const data = res?.data?.data ?? res?.data ?? res ?? {};
    systemStats.value = {
      cpuUsage: data.cpu_usage ?? 0,
      memoryUsage: data.memory_usage ?? 0,
      diskUsage: data.disk_free_gb ?? 0,
      uptime: data.uptime_seconds ? `${Math.floor(data.uptime_seconds / 3600)}h ${Math.floor((data.uptime_seconds % 3600) / 60)}m` : "0h 0m",
    };
    dbStats.value = {
      size: data.db_size_mb ? `${data.db_size_mb} MB` : "-",
      tableCount: String(data.table_count ?? "-"),
      connections: data.db_integrity_ok !== undefined ? (data.db_integrity_ok ? "ok" : "error") : "-",
      integrity: data.db_integrity_ok !== undefined ? (data.db_integrity_ok ? "PASS" : "FAIL") : "-",
    };
  } catch (e) {
    console.error("Failed to fetch monitoring data:", e);
    ElMessage.error("监控数据获取失败，请稍后重试");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  refreshData();
  refreshTimer = setInterval(refreshData, 30000);
});

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>

<style scoped>
.monitoring-dashboard {
  padding: 0;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
}
.stats-row { margin-bottom: 24px; }
.stats-row :deep(.el-card) { min-height: 140px; display: flex; align-items: center; }
.stats-row :deep(.el-card__body) { width: 100%; padding: 30px 36px !important; }
.stat-card { display: flex; align-items: center; gap: 30px; min-width: 0; }
.stat-icon { font-size: 60px; flex-shrink: 0; line-height: 1; }
.stat-info { flex: 1; min-width: 0; }
.stat-value { font-size: 40px; font-weight: 800; color: #303133; white-space: nowrap; line-height: 1.1; }
.stat-label { font-size: 16px; color: #475569; margin-top: 6px; font-weight: 600; }
.log-container {
  max-height: 300px;
  overflow-y: auto;
}
.log-item {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
  border-bottom: 1px solid #f0f0f0;
}
.log-time {
  color: #909399;
  flex-shrink: 0;
}
.log-level {
  font-weight: 600;
  flex-shrink: 0;
  width: 50px;
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
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty-logs {
  padding: 20px 0;
}
</style>
