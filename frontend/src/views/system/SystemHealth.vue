<template>
  <div class="system-health-page">
    <el-page-header title="返回" content="系统健壮性" @back="$router.back()" />

    <!-- 健康概览 -->
    <el-row :gutter="16" class="overview-row">
      <el-col v-for="(check, key) in overview.checks" :key="key" :span="6">
        <el-card
          shadow="hover"
          :class="['health-card', `health-${check.status}`]"
        >
          <div class="health-title">
            {{ checkLabels[key as string] || key }}
          </div>
          <div class="health-status">
            <el-icon :size="24">
              <CircleCheckFilled v-if="check.status === 'ok'" />
              <WarningFilled v-else-if="check.status === 'warning'" />
              <CircleCloseFilled v-else />
            </el-icon>
            <span>{{ check.message }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作区 -->
    <el-card shadow="hover" class="section-card">
      <template #header><span>数据库维护操作</span></template>
      <el-space wrap>
        <el-button
          type="primary"
          :loading="checking"
          @click="runIntegrityCheck"
        >
          完整性校验
        </el-button>
        <el-button
          type="warning"
          :loading="checkpointing"
          @click="runCheckpoint"
        >
          WAL 检查点
        </el-button>
        <el-popconfirm
          title="VACUUM 操作可能耗时较长，确认执行？"
          @confirm="runVacuum"
        >
          <template #reference>
            <el-button type="danger" :loading="vacuuming">数据库压缩</el-button>
          </template>
        </el-popconfirm>
        <el-button @click="loadOverview">刷新状态</el-button>
      </el-space>

      <!-- 操作结果 -->
      <el-alert
        v-if="lastResult"
        :title="lastResult.title"
        :description="lastResult.detail"
        :type="lastResult.type"
        show-icon
        closable
        class="result-alert"
        @close="lastResult = null"
      />
    </el-card>

    <!-- 表统计 -->
    <el-card shadow="hover" class="section-card">
      <template #header>
        <div class="card-header">
          <span>数据库表统计</span>
          <el-tag
            >共 {{ tableStats.total_tables }} 张表 /
            {{ tableStats.total_rows }} 条记录</el-tag
          >
        </div>
      </template>
      <el-table
        :data="tableStats.tables"
        border
        stripe
        size="small"
        max-height="400"
      >
        <el-table-column prop="table" label="表名" min-width="200" />
        <el-table-column prop="rows" label="记录数" width="120" align="right">
          <template #default="{ row }">
            <el-tag v-if="row.error" type="danger" size="small">错误</el-tag>
            <span v-else>{{ row.rows.toLocaleString() }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from "vue";
import {
  CircleCheckFilled,
  WarningFilled,
  CircleCloseFilled,
} from "@element-plus/icons-vue";
import {
  systemHealthApi,
  type SystemOverview,
  type TableStat,
} from "@/api/systemHealth";

const checkLabels: Record<string, string> = {
  database: "数据库连接",
  disk: "磁盘空间",
  db_file: "数据库文件",
  wal: "WAL 日志",
};

const overview = ref<SystemOverview>({
  overall_status: "ok",
  checks: {},
  timestamp: "",
});
const tableStats = ref<{
  tables: TableStat[];
  total_tables: number;
  total_rows: number;
}>({ tables: [], total_tables: 0, total_rows: 0 });
const checking = ref(false);
const checkpointing = ref(false);
const vacuuming = ref(false);
const lastResult = ref<{
  title: string;
  detail: string;
  type: "success" | "warning" | "error";
} | null>(null);

async function loadOverview() {
  try {
    overview.value = await systemHealthApi.getOverview();
  } catch {
    // 静默
  }
}

async function loadTableStats() {
  try {
    tableStats.value = await systemHealthApi.getTableStats();
  } catch {
    // 静默
  }
}

async function runIntegrityCheck() {
  checking.value = true;
  try {
    const res = await systemHealthApi.runIntegrityCheck();
    lastResult.value = {
      title: res.status === "ok" ? "完整性校验通过" : "完整性校验发现问题",
      detail: `耗时 ${res.elapsed_seconds}s — ${res.messages.join(", ")}`,
      type: res.status === "ok" ? "success" : "error",
    };
  } catch {
    lastResult.value = {
      title: "校验失败",
      detail: "执行完整性校验时出错",
      type: "error",
    };
  } finally {
    checking.value = false;
  }
}

async function runCheckpoint() {
  checkpointing.value = true;
  try {
    const res = await systemHealthApi.runWalCheckpoint();
    lastResult.value = {
      title: "WAL 检查点完成",
      detail: `日志页: ${res.result?.log_pages ?? "N/A"}, 检查点页: ${res.result?.checkpointed_pages ?? "N/A"}`,
      type: "success",
    };
    loadOverview();
  } catch {
    lastResult.value = {
      title: "检查点失败",
      detail: "执行 WAL 检查点时出错",
      type: "error",
    };
  } finally {
    checkpointing.value = false;
  }
}

async function runVacuum() {
  vacuuming.value = true;
  try {
    const res = await systemHealthApi.runVacuum();
    lastResult.value = {
      title: "数据库压缩完成",
      detail: `压缩前: ${res.before_size_mb}MB → 压缩后: ${res.after_size_mb}MB (节省 ${res.saved_mb}MB)`,
      type: "success",
    };
    loadOverview();
  } catch {
    lastResult.value = {
      title: "压缩失败",
      detail: "执行 VACUUM 时出错",
      type: "error",
    };
  } finally {
    vacuuming.value = false;
  }
}

onMounted(() => {
  loadOverview();
  loadTableStats();
});
</script>

<style scoped>
.system-health-page {
  padding: 20px;
}
.overview-row {
  margin-top: 16px;
}
.health-card {
  text-align: center;
  padding: 8px;
}
.health-card.health-ok {
  border-left: 4px solid #67c23a;
}
.health-card.health-warning {
  border-left: 4px solid #e6a23c;
}
.health-card.health-error {
  border-left: 4px solid #f56c6c;
}
.health-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}
.health-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
}
.section-card {
  margin-top: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.result-alert {
  margin-top: 16px;
}
</style>
