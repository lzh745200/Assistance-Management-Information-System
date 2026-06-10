<template>
  <div class="system-monitor">
    <div class="page-header">
      <h2>系统健康检查</h2>
      <el-button-group>
        <el-button :icon="Refresh" :loading="checking" @click="runHealthCheck">
          运行检查
        </el-button>
        <el-button @click="exportReport">导出报告</el-button>
      </el-button-group>
    </div>

    <!-- 健康评分 -->
    <el-card class="health-score-card">
      <div class="health-score">
        <div class="score-circle" :class="scoreClass">
          <span class="score-value">{{ healthScore }}</span>
          <span class="score-label">/ 100</span>
        </div>
        <div class="score-details">
          <h3>系统健康评分</h3>
          <p>{{ scoreDescription }}</p>
          <el-tag :type="scoreTagType" size="large">{{ scoreTagText }}</el-tag>
        </div>
      </div>
    </el-card>

    <!-- 检查项 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>基础检查</span>
          </template>
          <div class="check-list">
            <div
              v-for="item in basicChecks"
              :key="item.name"
              class="check-item"
            >
              <el-icon :class="item.passed ? 'check-pass' : 'check-fail'">
                <component
                  :is="item.passed ? CircleCheckFilled : CircleCloseFilled"
                />
              </el-icon>
              <span class="check-name">{{ item.name }}</span>
              <span class="check-detail">{{ item.detail }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>性能检查</span>
          </template>
          <div class="check-list">
            <div
              v-for="item in performanceChecks"
              :key="item.name"
              class="check-item"
            >
              <el-icon :class="item.passed ? 'check-pass' : 'check-fail'">
                <component
                  :is="item.passed ? CircleCheckFilled : CircleCloseFilled"
                />
              </el-icon>
              <span class="check-name">{{ item.name }}</span>
              <span class="check-detail">{{ item.detail }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近检查结果 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <span>最近检查历史</span>
      </template>
      <el-table :data="checkHistory" stripe size="small">
        <el-table-column prop="time" label="检查时间" width="180" />
        <el-table-column prop="score" label="评分" width="80">
          <template #default="{ row }">
            <el-tag
              :type="
                row.score >= 80
                  ? 'success'
                  : row.score >= 60
                    ? 'warning'
                    : 'danger'
              "
              size="small"
            >
              {{ row.score }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="passed" label="通过项" width="80" />
        <el-table-column prop="failed" label="失败项" width="80" />
        <el-table-column prop="summary" label="摘要" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import {
  Refresh,
  CircleCheckFilled,
  CircleCloseFilled,
} from "@element-plus/icons-vue";

const checking = ref(false);
const healthScore = ref(0);

const basicChecks = ref([
  { name: "数据库连接", passed: false, detail: "未检查" },
  { name: "API 服务", passed: false, detail: "未检查" },
  { name: "认证服务", passed: false, detail: "未检查" },
  { name: "缓存服务", passed: false, detail: "未检查" },
  { name: "日志系统", passed: false, detail: "未检查" },
]);

const performanceChecks = ref([
  { name: "响应时间", passed: false, detail: "未检查" },
  { name: "内存使用", passed: false, detail: "未检查" },
  { name: "CPU 使用", passed: false, detail: "未检查" },
  { name: "磁盘空间", passed: false, detail: "未检查" },
  { name: "数据库大小", passed: false, detail: "未检查" },
]);

const checkHistory = ref<
  Array<{
    time: string;
    score: number;
    passed: number;
    failed: number;
    summary: string;
  }>
>([]);

const scoreClass = computed(() => {
  if (healthScore.value >= 80) return "score-good";
  if (healthScore.value >= 60) return "score-warning";
  return "score-danger";
});

const scoreDescription = computed(() => {
  if (healthScore.value >= 90) return "系统运行状态极佳，所有检查项均通过。";
  if (healthScore.value >= 80) return "系统运行状态良好，部分检查项需要关注。";
  if (healthScore.value >= 60) return "系统存在一些问题，建议尽快处理。";
  return "系统存在严重问题，请立即处理。";
});

const scoreTagType = computed(() => {
  if (healthScore.value >= 80) return "success";
  if (healthScore.value >= 60) return "warning";
  return "danger";
});

const scoreTagText = computed(() => {
  if (healthScore.value >= 90) return "极佳";
  if (healthScore.value >= 80) return "良好";
  if (healthScore.value >= 60) return "需关注";
  return "异常";
});

async function runHealthCheck() {
  checking.value = true;
  try {
    const response = await fetch("/api/v1/system/health");
    if (response.ok) {
      const data = await response.json();
      const score = data.score ?? 0;
      healthScore.value = score;

      if (data.checks) {
        // Update basic checks
        basicChecks.value = basicChecks.value.map((check) => {
          const result = data.checks[check.name];
          return result
            ? { ...check, passed: result.passed, detail: result.detail }
            : check;
        });
        // Update performance checks
        performanceChecks.value = performanceChecks.value.map((check) => {
          const result = data.checks[check.name];
          return result
            ? { ...check, passed: result.passed, detail: result.detail }
            : check;
        });
      }

      // Add to history
      const passedCount =
        basicChecks.value.filter((c) => c.passed).length +
        performanceChecks.value.filter((c) => c.passed).length;
      const failedCount =
        basicChecks.value.length + performanceChecks.value.length - passedCount;
      checkHistory.value.unshift({
        time: new Date().toLocaleString(),
        score,
        passed: passedCount,
        failed: failedCount,
        summary: `评分 ${score}，通过 ${passedCount} 项，失败 ${failedCount} 项`,
      });
      // Keep only last 20 records
      if (checkHistory.value.length > 20) {
        checkHistory.value = checkHistory.value.slice(0, 20);
      }
    }
  } catch (e) {
    console.error("Health check failed:", e);
  } finally {
    checking.value = false;
  }
}

function exportReport() {
  const report = {
    timestamp: new Date().toISOString(),
    score: healthScore.value,
    basicChecks: basicChecks.value,
    performanceChecks: performanceChecks.value,
    history: checkHistory.value,
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `health-report-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

onMounted(() => {
  runHealthCheck();
});
</script>

<style scoped>
.system-monitor {
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
.health-score-card {
  margin-bottom: 0;
}
.health-score {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 8px 0;
}
.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 5px solid;
  flex-shrink: 0;
}
.score-value {
  font-size: 40px;
  font-weight: 700;
  line-height: 1;
}
.score-label {
  font-size: 13px;
  color: #64748b;
}
.score-good {
  border-color: #67c23a;
}
.score-warning {
  border-color: #e6a23c;
}
.score-danger {
  border-color: #f56c6c;
}
.score-value {
  font-size: 32px;
  font-weight: 700;
}
.score-good .score-value {
  color: #67c23a;
}
.score-warning .score-value {
  color: #e6a23c;
}
.score-danger .score-value {
  color: #f56c6c;
}
.score-label {
  font-size: 12px;
  color: #909399;
}
.score-details h3 {
  margin: 0 0 8px;
}
.score-details p {
  margin: 0 0 12px;
  color: #606266;
}
.check-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.check-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  background: #fafafa;
}
.check-pass {
  color: #67c23a;
  font-size: 18px;
}
.check-fail {
  color: #f56c6c;
  font-size: 18px;
}
.check-name {
  font-weight: 500;
  min-width: 100px;
}
.check-detail {
  color: #909399;
  font-size: 13px;
}
</style>
