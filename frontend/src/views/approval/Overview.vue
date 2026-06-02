<template>
  <div class="approval-overview">
    <div class="page-header">
      <h2 class="page-title">操作日志</h2>
      <p class="page-desc">记录系统重要操作，便于追溯和统计</p>
    </div>

    <!-- 统计仪表板 -->
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-num">{{ stats.total }}</div>
        <div class="stat-label">总记录数</div>
      </el-card>
      <el-card class="stat-card stat-pending">
        <div class="stat-num">{{ stats.today }}</div>
        <div class="stat-label">今日操作</div>
      </el-card>
      <el-card class="stat-card stat-approved">
        <div class="stat-num">{{ stats.dataChanges }}</div>
        <div class="stat-label">数据变更</div>
      </el-card>
      <el-card class="stat-card stat-rejected">
        <div class="stat-num">{{ stats.exports }}</div>
        <div class="stat-label">导出操作</div>
      </el-card>
      <el-card class="stat-card stat-overdue">
        <div class="stat-num">{{ stats.pending }}</div>
        <div class="stat-label">待处理项</div>
      </el-card>
    </div>

    <!-- 筛选 -->
    <el-card>
      <el-form :inline="true" :model="filters">
        <el-form-item label="操作类型">
          <el-select
            v-model="filters.status"
            clearable
            placeholder="全部"
            style="width: 130px"
          >
            <el-option label="数据变更" value="data_change" />
            <el-option label="数据导入" value="data_import" />
            <el-option label="数据导出" value="data_export" />
            <el-option label="系统设置" value="system" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作人">
          <el-input
            v-model="filters.applicant"
            placeholder="姓名"
            clearable
            style="width: 140px"
          />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            style="width: 260px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作日志列表 -->
    <el-card>
      <el-table v-loading="loading" :data="filteredTasks" stripe>
        <el-table-column prop="title" label="操作内容" min-width="200" />
        <el-table-column prop="applicant_name" label="操作人" width="100" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getTypeTagType(row.type)">
              {{ getTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="操作时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="reviewer_name" label="审批人" width="120" />
        <el-table-column prop="reviewed_at" label="处理时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.reviewed_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 单机版快捷操作 -->
    <el-card>
      <template #header>
        <span style="font-weight: 600; color: #1b4332">单机版快捷操作</span>
      </template>
      <el-form label-width="160px">
        <el-form-item label="一键审批所有待处理">
          <el-button
            type="success"
            :loading="autoApproving"
            :disabled="stats.pending === 0"
            @click="handleAutoApproveAll"
          >
            一键通过全部 {{ stats.pending }} 个待处理任务
          </el-button>
          <span style="margin-left: 8px; color: #888"
            >适用于单机版快速处理</span
          >
        </el-form-item>
        <el-form-item label="导出操作日志">
          <el-button type="primary" @click="handleExportLog">
            导出当前查询结果
          </el-button>
          <span style="margin-left: 8px; color: #888">导出为Excel文件</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 提醒规则设置 -->
    <el-card>
      <template #header>
        <span style="font-weight: 600; color: #1b4332">提醒规则设置</span>
      </template>
      <el-form :model="reminderConfig" label-width="160px">
        <el-form-item label="超时提醒天数">
          <el-input-number
            v-model="reminderConfig.overdueDays"
            :min="1"
            :max="30"
          />
          <span style="margin-left: 8px; color: #888">天未处理时发送提醒</span>
        </el-form-item>
        <el-form-item label="启用自动提醒">
          <el-switch v-model="reminderConfig.enabled" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveReminder">保存设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { getAllTasks, autoApproveAll, type ApprovalTask } from "@/api/approval";
import { exportUtil, format } from "@/utils";

const MS_PER_DAY = 86400000;
const loading = ref(false);
const autoApproving = ref(false);
const allTasks = ref<
  (ApprovalTask & {
    applicant_name?: string;
    reviewer_name?: string;
    reviewed_at?: string;
    type?: string;
  })[]
>([]);
const filters = reactive({ status: "", applicant: "", dateRange: null as any });
const reminderConfig = reactive({ overdueDays: 3, enabled: true });

const stats = computed(() => {
  const list = filteredTasks.value;
  const now = new Date();
  const nowMs = now.getTime();
  const todayStart = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  ).getTime();
  const overdueMs = reminderConfig.overdueDays * MS_PER_DAY;

  let pending = 0,
    approved = 0,
    rejected = 0,
    overdue = 0,
    today = 0,
    dataChanges = 0,
    exports = 0;

  for (const a of list) {
    const s = a.status;
    if (s === "pending") pending++;
    else if (s === "approved") approved++;
    else if (s === "rejected") rejected++;

    const createdMs = new Date(a.created_at).getTime();
    if (createdMs >= todayStart) today++;

    if (s === "pending" && nowMs - createdMs > overdueMs) overdue++;

    const type = (a.type || "").toLowerCase();
    const isExport = type.includes("export");
    if (isExport) exports++;
    // dataChanges 含导入、数据变更、导出（导出单独计数）
    if (type.includes("import") || type.includes("data") || isExport)
      dataChanges++;
  }

  return {
    total: list.length,
    pending,
    approved,
    rejected,
    overdue,
    today,
    dataChanges,
    exports,
  };
});

// 统一的标签映射（status 和 type 共用）
const _LABEL_MAP: Record<string, string> = {
  pending: "待处理",
  approved: "已完成",
  rejected: "已驳回",
  withdrawn: "已撤回",
  data_change: "数据变更",
  data_import: "数据导入",
  data_export: "数据导出",
  system: "系统设置",
};

const statusLabel = (s: string) => _LABEL_MAP[s] || s;

// statusLabel 与 typeLabel 共用同一映射表
const getTypeLabel = (type: string) => _LABEL_MAP[type] || type || "其他";

const statusTagType = (
  s: string,
): "success" | "warning" | "danger" | "info" | "primary" | undefined =>
  (
    ({
      pending: "warning",
      approved: "success",
      rejected: "danger",
      withdrawn: "info",
    }) as Record<string, "success" | "warning" | "danger" | "info" | "primary">
  )[s] || "info";

const getTypeTagType = (
  type: string,
): "success" | "warning" | "danger" | "info" | "primary" | undefined => {
  const t = (type || "").toLowerCase();
  if (t.includes("import") || t.includes("data_change")) return "primary";
  if (t.includes("export")) return "success";
  if (t.includes("system")) return "info";
  if (t.includes("pending")) return "warning";
  if (t.includes("approved") || t.includes("completed")) return "success";
  if (t.includes("rejected") || t.includes("failed")) return "danger";
  return "info" as const;
};

const formatDate = (d: string) => format.formatDateTimeLocale(d);

const filteredTasks = computed(() => {
  let list = allTasks.value;
  if (filters.applicant) {
    const q = filters.applicant.toLowerCase();
    list = list.filter((t) =>
      (t.applicant_name || "").toLowerCase().includes(q),
    );
  }
  if (filters.dateRange && filters.dateRange[0] && filters.dateRange[1]) {
    const start = new Date(filters.dateRange[0]).getTime();
    const end = new Date(filters.dateRange[1]).getTime() + MS_PER_DAY;
    list = list.filter((t) => {
      const ts = new Date(t.created_at).getTime();
      return ts >= start && ts < end;
    });
  }
  return list;
});

async function loadData() {
  loading.value = true;
  try {
    const params: Record<string, any> = {};
    if (filters.status) params.status = filters.status;
    allTasks.value = await getAllTasks(params);
  } catch {
    allTasks.value = [];
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.status = "";
  filters.applicant = "";
  filters.dateRange = null;
  loadData();
}
function saveReminder() {
  ElMessage.success("提醒规则已保存");
}

async function handleAutoApproveAll() {
  const pendingCount = stats.value.pending;
  if (pendingCount === 0) return;
  try {
    await ElMessageBox.confirm(
      `确定要一键处理所有 ${pendingCount} 个待处理任务吗？`,
      "一键全部处理",
      {
        type: "warning",
        confirmButtonText: "全部通过",
        cancelButtonText: "取消",
      },
    );
    autoApproving.value = true;
    const result = await autoApproveAll("单机版一键批量处理");
    ElMessage.success(
      `批量处理完成：成功 ${result.success.length}，失败 ${result.failed.length}`,
    );
    loadData();
  } catch {
    // 用户取消
  } finally {
    autoApproving.value = false;
  }
}

function handleExportLog() {
  const list = filteredTasks.value;
  if (list.length === 0) {
    ElMessage.warning("当前没有可导出的数据");
    return;
  }

  const timestamp = new Date().toISOString().slice(0, 10);
  const data = list.map((t) => ({
    操作内容: t.title || "",
    操作人: t.applicant_name || "",
    类型: getTypeLabel(t.type ?? ""),
    状态: statusLabel(t.status),
    操作时间: formatDate(t.created_at),
    处理人: t.reviewer_name ?? "",
    处理时间: formatDate(t.reviewed_at ?? ""),
  }));

  exportUtil.exportToCSV(data, `操作日志_${timestamp}`);
  ElMessage.success("操作日志已导出");
}

onMounted(loadData);
</script>

<style scoped>
.approval-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1b4332;
  margin: 0 0 4px;
}
.page-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}
.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}
.stat-card {
  text-align: center;
  padding: 16px;
}
.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #1b4332;
}
.stat-label {
  font-size: 13px;
  color: #888;
  margin-top: 4px;
}
.stat-pending .stat-num {
  color: #e6a23c;
}
.stat-approved .stat-num {
  color: #67c23a;
}
.stat-rejected .stat-num {
  color: #f56c6c;
}
.stat-overdue .stat-num {
  color: #e63946;
}
</style>
