<template>
  <div class="cache-page">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="缓存后端" :value="status.backend || '-'" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="缓存键数" :value="metrics.keys" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="命中次数" :value="metrics.hits" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="未命中次数" :value="metrics.misses" />
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">缓存管理</span>
          <div>
            <el-button type="primary" :loading="loading" @click="refreshData"
              >刷新</el-button
            >
            <el-button type="danger" :loading="clearing" @click="clearAllCache"
              >清除全部缓存</el-button
            >
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="状态">
          <el-tag :type="status.status === 'healthy' ? 'success' : 'danger'">
            {{ status.status === "healthy" ? "正常" : "异常" }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="延迟"
          >{{ status.latency_ms }} ms</el-descriptions-item
        >
        <el-descriptions-item label="后端类型">{{
          status.backend || "memory"
        }}</el-descriptions-item>
        <el-descriptions-item label="命中率">
          {{ hitRate }}%
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import request from "@/api/request";

const loading = ref(false);
const clearing = ref(false);
const status = ref<any>({
  status: "unknown",
  latency_ms: 0,
  backend: "memory",
});
const metrics = ref<any>({ keys: 0, hits: 0, misses: 0 });

const hitRate = computed(() => {
  const total = (metrics.value.hits || 0) + (metrics.value.misses || 0);
  if (total === 0) return "0.0";
  return ((metrics.value.hits / total) * 100).toFixed(1);
});

async function refreshData() {
  loading.value = true;
  try {
    const [statusRes, metricsRes] = await Promise.all([
      request.get("/cache/status"),
      request.get("/cache/metrics"),
    ]);
    status.value = statusRes.data || {};
    metrics.value = metricsRes.data || {};
  } catch {
    ElMessage.error("加载缓存信息失败");
  } finally {
    loading.value = false;
  }
}

async function clearAllCache() {
  try {
    await ElMessageBox.confirm("确定清除全部缓存吗？", "警告", {
      type: "warning",
    });
    clearing.value = true;
    await request.delete("/cache/invalidate-all");
    ElMessage.success("缓存已清除");
    await refreshData();
  } catch (e: any) {
    if (e !== "cancel") ElMessage.error("清除失败");
  } finally {
    clearing.value = false;
  }
}

onMounted(() => refreshData());
</script>

<style scoped>
.cache-page {
  padding: 20px;
}
.stats-row {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title {
  font-size: 16px;
  font-weight: 600;
}
</style>
