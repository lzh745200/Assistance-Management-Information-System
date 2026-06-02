<template>
  <div class="work-calendar-page">
    <el-page-header title="返回" content="工作日历" @back="$router.back()" />

    <div class="toolbar">
      <div class="toolbar-left">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button value="calendar">日历视图</el-radio-button>
          <el-radio-button value="list">列表视图</el-radio-button>
        </el-radio-group>
        <el-select
          v-model="logSource"
          placeholder="来源"
          clearable
          style="width: 130px; margin-left: 12px"
          @change="onSourceChange"
        >
          <el-option label="全部记录" value="" />
          <el-option label="自动记录" value="auto" />
          <el-option label="手动记录" value="manual" />
        </el-select>
      </div>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon> 新建日志
      </el-button>
    </div>

    <!-- 日历视图 -->
    <el-card v-if="viewMode === 'calendar'" shadow="hover" class="section-card">
      <el-calendar v-model="calendarDate">
        <template #date-cell="{ data }">
          <div class="calendar-cell" @click="onDateClick(data.day)">
            <span class="date-num">{{ data.day.split("-")[2] }}</span>
            <div v-if="getLogsForDate(data.day).length" class="log-dots">
              <el-tag
                v-for="log in getLogsForDate(data.day).slice(0, 2)"
                :key="log.id"
                size="small"
                :type="getLogTagType(log)"
                :class="['log-tag', log.is_auto ? 'log-tag-auto' : '']"
                @click.stop="onLogTagClick(log, $event)"
              >
                {{ log.title.substring(0, 6) }}
              </el-tag>
              <span
                v-if="getLogsForDate(data.day).length > 2"
                class="more-count"
              >
                +{{ getLogsForDate(data.day).length - 2 }}
              </span>
            </div>
          </div>
        </template>
      </el-calendar>
    </el-card>

    <!-- 列表视图 -->
    <el-card v-else shadow="hover" class="section-card">
      <div class="filter-row">
        <el-input
          v-model="keyword"
          placeholder="搜索日志..."
          clearable
          style="width: 200px"
          @clear="loadList"
          @keyup.enter="loadList"
        />
        <el-select
          v-model="filterType"
          placeholder="类型"
          clearable
          style="width: 120px"
          @change="loadList"
        >
          <el-option label="日常工作" value="daily" />
          <el-option label="调研" value="research" />
          <el-option label="会议" value="meeting" />
          <el-option label="走访" value="visit" />
          <el-option label="其他" value="other" />
        </el-select>
      </div>
      <el-table :data="logList" border stripe style="width: 100%">
        <el-table-column prop="work_date" label="日期" width="110" />
        <el-table-column prop="title" label="标题" min-width="150">
          <template #default="{ row }">
            <span class="log-title">
              {{ row.title }}
              <el-tag
                v-if="row.is_auto"
                type="info"
                size="small"
                style="margin-left: 4px"
                >自动</el-tag
              >
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="log_type" label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getLogTagType(row)" size="small">{{
              getLogTypeLabel(row.log_type)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="地点" width="120" />
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <template v-if="row.is_auto">
              <el-tag type="info" size="small">只读</el-tag>
            </template>
            <template v-else>
              <el-button text type="primary" size="small" @click="editLog(row)"
                >编辑</el-button
              >
              <el-popconfirm title="确认删除？" @confirm="deleteLog(row.id)">
                <template #reference>
                  <el-button text type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="totalLogs > 10"
        :total="totalLogs"
        :page-size="10"
        :current-page="currentPage"
        layout="total, prev, pager, next"
        style="margin-top: 12px; justify-content: flex-end"
        @current-change="onPageChange"
      />
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="selectedLog?.is_auto ? '自动记录详情' : '日志详情'"
      width="500px"
    >
      <el-descriptions :column="1" border>
        <el-descriptions-item label="日期">{{
          selectedLog?.work_date
        }}</el-descriptions-item>
        <el-descriptions-item label="来源">
          <el-tag
            :type="selectedLog?.is_auto ? 'info' : 'success'"
            size="small"
          >
            {{ selectedLog?.is_auto ? "系统自动记录" : "手动记录" }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="getLogTagType(selectedLog || undefined)" size="small">
            {{ getLogTypeLabel(selectedLog?.log_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="内容" label-class-name="content-label">
          <div class="log-content">{{ selectedLog?.content }}</div>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="showDetailDialog = false"
          >关闭</el-button
        >
      </template>
    </el-dialog>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="editingLog ? '编辑工作日志' : '新建工作日志'"
      width="600px"
      destroy-on-close
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="日志标题" />
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="form.work_date"
            type="date"
            placeholder="工作日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select
            v-model="form.log_type"
            placeholder="请选择日志类型"
            clearable
            style="width: 100%"
          >
            <el-option label="日常工作" value="daily" />
            <el-option label="调研" value="research" />
            <el-option label="会议" value="meeting" />
            <el-option label="走访" value="visit" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="form.location" placeholder="工作地点" />
        </el-form-item>
        <el-form-item label="参与人">
          <el-input v-model="form.participants" placeholder="参与人员" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="工作内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveLog"
          >保存</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { Plus } from "@element-plus/icons-vue";
import { workLogApi, type WorkLog } from "@/api/workLogs";
import { ElMessage } from "element-plus";

interface WorkLogEx extends WorkLog {
  is_auto?: boolean;
  category?: string;
}

const viewMode = ref<"calendar" | "list">("calendar");
const calendarDate = ref(new Date());
const calendarLogs = ref<WorkLogEx[]>([]);
const logList = ref<WorkLogEx[]>([]);
const totalLogs = ref(0);
const currentPage = ref(1);
const keyword = ref("");
const filterType = ref("");
const logSource = ref(""); // all | auto | manual
const showDialog = ref(false);
const showDetailDialog = ref(false);
const saving = ref(false);
const editingLog = ref<WorkLogEx | null>(null);
const selectedLog = ref<WorkLogEx | null>(null);

const form = ref({
  title: "",
  work_date: new Date().toISOString().slice(0, 10),
  log_type: "daily",
  content: "",
  location: "",
  participants: "",
});

function getLogTagType(log: WorkLogEx | undefined) {
  if (log?.is_auto) return "info";
  const map: Record<string, string> = {
    daily: "",
    research: "success",
    meeting: "warning",
    visit: "primary",
    other: "info",
  };
  return (map[log?.log_type || "daily"] || "info") as any;
}

function getLogTypeLabel(type: string | undefined) {
  if (type === "system_auto") return "自动";
  const map: Record<string, string> = {
    daily: "日常",
    research: "调研",
    meeting: "会议",
    visit: "走访",
    other: "其他",
  };
  return map[type || "daily"] || type || "";
}

function getLogsForDate(day: string) {
  return calendarLogs.value.filter((l) => l.work_date === day);
}

function onDateClick(day: string) {
  form.value = {
    title: "",
    work_date: day,
    log_type: "daily",
    content: "",
    location: "",
    participants: "",
  };
  editingLog.value = null;
  showDialog.value = true;
}

function onLogTagClick(log: WorkLogEx, event: Event) {
  event.stopPropagation();
  selectedLog.value = log;
  showDetailDialog.value = true;
}

function editLog(log: WorkLogEx) {
  if (log.is_auto) {
    selectedLog.value = log;
    showDetailDialog.value = true;
    return;
  }
  editingLog.value = log;
  form.value = {
    title: log.title,
    work_date: log.work_date || new Date().toISOString().slice(0, 10),
    log_type: log.log_type,
    content: log.content || "",
    location: log.location || "",
    participants: log.participants || "",
  };
  showDialog.value = true;
}

async function saveLog() {
  if (!form.value.title || !form.value.work_date) {
    ElMessage.warning("请填写标题和日期");
    return;
  }
  saving.value = true;
  try {
    if (editingLog.value) {
      await workLogApi.update(editingLog.value.id, form.value);
      ElMessage.success("更新成功");
    } else {
      await workLogApi.create(form.value);
      ElMessage.success("创建成功");
    }
    showDialog.value = false;
    loadCalendarData();
    if (viewMode.value === "list") loadList();
  } catch {
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
}

async function deleteLog(id: number) {
  try {
    await workLogApi.delete(id);
    ElMessage.success("删除成功");
    loadCalendarData();
    if (viewMode.value === "list") loadList();
  } catch {
    ElMessage.error("删除失败");
  }
}

async function loadCalendarData() {
  try {
    const d = calendarDate.value;
    const source = logSource.value as "auto" | "manual" | undefined;
    const res = await workLogApi.getCalendarView(
      d.getFullYear(),
      d.getMonth() + 1,
      source,
    );
    calendarLogs.value = (res.items || []).map((item: any) => ({
      ...item,
      is_auto: item.is_auto || item.category === "system_auto",
    }));
  } catch {
    // 静默
  }
}

async function loadList() {
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: 10,
    };
    if (keyword.value) params.keyword = keyword.value;
    if (filterType.value) params.log_type = filterType.value;
    if (logSource.value) params.source = logSource.value;
    const res = await workLogApi.list(params);
    logList.value = (res.items || []).map((item: any) => ({
      ...item,
      is_auto: item.is_auto || item.category === "system_auto",
    }));
    totalLogs.value = res.total || 0;
  } catch {
    // 静默
  }
}

function onSourceChange() {
  loadCalendarData();
  if (viewMode.value === "list") loadList();
}

function onPageChange(page: number) {
  currentPage.value = page;
  loadList();
}

watch(calendarDate, () => loadCalendarData());
watch(viewMode, (v) => {
  if (v === "list") loadList();
});

onMounted(() => {
  loadCalendarData();
});
</script>

<style scoped>
.work-calendar-page {
  padding: 20px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}
.toolbar-left {
  display: flex;
  align-items: center;
}
.section-card {
  margin-top: 12px;
}
.filter-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.calendar-cell {
  height: 100%;
  min-height: 60px;
  cursor: pointer;
}
.date-num {
  font-weight: 500;
}
.log-dots {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 2px;
}
.log-tag {
  cursor: pointer;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}
.log-tag-auto {
  background-color: #f0f9eb;
  border-color: #e1f3d8;
  color: #95d475;
}
.log-title {
  display: flex;
  align-items: center;
}
.log-content {
  white-space: pre-wrap;
  word-break: break-word;
  color: #606266;
  line-height: 1.6;
}
.more-count {
  font-size: 11px;
  color: #909399;
}
</style>
