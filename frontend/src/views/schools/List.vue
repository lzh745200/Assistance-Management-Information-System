<template>
  <div class="school-mgmt-list-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">帮扶学校管理</h2>
        <p class="page-desc">管理帮扶学校信息，跟踪教育帮扶进展</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" class="btn-create" @click="handleCreate">
          <el-icon><Plus /></el-icon>新增学校
        </el-button>
        <el-button type="success" plain @click="handleDownloadTemplate">
          <el-icon><Download /></el-icon>下载模板
        </el-button>
        <el-button type="warning" plain @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>导入
        </el-button>
        <el-button type="info" plain @click="handleExport">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-item" @click="filterByStatus('')">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">学校总数</div>
      </div>
      <div class="stat-item" @click="filterByStatus('active')">
        <div class="stat-value text-success">{{ stats.active }}</div>
        <div class="stat-label">帮扶中</div>
      </div>
      <div class="stat-item" @click="filterByStatus('completed')">
        <div class="stat-value text-primary">{{ stats.completed }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-item">
        <div class="stat-value text-warning">{{ stats.totalStudents }}</div>
        <div class="stat-label">学生总数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value text-info">{{ stats.totalTeachers }}</div>
        <div class="stat-label">教师总数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value text-project">{{ apiStats.project_count }}</div>
        <div class="stat-label">助学兴教项目</div>
      </div>
      <div class="stat-item">
        <div class="stat-value text-scholarship">
          {{ apiStats.scholarship_count }}
        </div>
        <div class="stat-label">资助学生数</div>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <div class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="学校名称">
          <el-input
            v-model="filterForm.keyword"
            placeholder="名称/编码/帮扶单位"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="学校类型">
          <el-select
            v-model="filterForm.type"
            placeholder="全部类型"
            clearable
            style="width: 130px"
          >
            <el-option label="小学" value="primary" />
            <el-option label="初中" value="middle" />
            <el-option label="高中" value="high" />
            <el-option label="职业学校" value="vocational" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="帮扶状态">
          <el-select
            v-model="filterForm.status"
            placeholder="全部状态"
            clearable
            style="width: 130px"
          >
            <el-option label="帮扶中" value="active" />
            <el-option label="未帮扶" value="inactive" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据表格 -->
    <div class="table-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="学校名称" min-width="180">
          <template #default="scope">
            <el-link type="primary" @click="handleView(scope.row)">{{
              scope.row.name
            }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100" align="center">
          <template #default="scope">
            <el-tag size="small">{{
              typeMap[scope.row.type] || scope.row.type || "-"
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="support_unit"
          label="帮扶单位"
          width="140"
          show-overflow-tooltip
        />
        <el-table-column
          prop="student_count"
          label="学生数"
          width="90"
          align="right"
        >
          <template #default="scope">
            {{ scope.row.student_count || scope.row.students || 0 }}
          </template>
        </el-table-column>
        <el-table-column
          prop="teacher_count"
          label="教师数"
          width="90"
          align="right"
        >
          <template #default="scope">
            {{ scope.row.teacher_count || scope.row.teachers || 0 }}
          </template>
        </el-table-column>
        <el-table-column
          prop="support_status"
          label="帮扶状态"
          width="100"
          align="center"
        >
          <template #default="scope">
            <el-tag
              :type="getStatusTagType(scope.row.support_status)"
              size="small"
            >
              {{ statusMap[scope.row.support_status] || "未帮扶" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="address"
          label="地址"
          min-width="160"
          show-overflow-tooltip
        />
        <el-table-column
          prop="created_at"
          label="创建时间"
          width="110"
          align="center"
        >
          <template #default="scope">
            {{
              scope.row.created_at
                ? String(scope.row.created_at).split("T")[0]
                : "-"
            }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleView(scope.row)"
              >查看</el-button
            >
            <el-button
              type="primary"
              link
              size="small"
              @click="handleEdit(scope.row)"
              >编辑</el-button
            >
            <el-popconfirm
              title="确定删除该学校吗？"
              @confirm="handleDelete(scope.row)"
            >
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入帮扶学校数据"
      width="520px"
      destroy-on-close
    >
      <div class="import-dialog-body">
        <el-alert
          title="请先下载模板，按模板格式填写学校数据后上传"
          type="info"
          show-icon
          :closable="false"
          style="margin-bottom: 16px"
        />
        <el-upload
          ref="importUploadRef"
          :action="importUrl"
          :headers="uploadHeaders"
          :before-upload="beforeImportUpload"
          :on-success="onImportSuccess"
          :on-error="onImportError"
          :limit="1"
          accept=".xlsx,.xls"
          drag
        >
          <el-icon class="el-icon--upload"><Upload /></el-icon>
          <div class="el-upload__text">
            将 Excel 文件拖到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">只支持 .xlsx / .xls 格式</div>
          </template>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="showImportDialog = false">关闭</el-button>
        <el-button type="success" plain @click="handleDownloadTemplate"
          >下载模板</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { logger } from "@/utils/logger";
import { AuthStorage } from "@/utils/authStorage";

import { ref, reactive, computed, onMounted, onActivated } from "vue";
import { useRouterSafe } from "@/composables/useRouterSafe";
import { ElMessage } from "element-plus";
import { Plus, Download, Upload, Search } from "@element-plus/icons-vue";
import request from "@/api/request";
import { schoolApi } from "@/api/schools";
import { downloadImportTemplate } from "@/api/import";

const { pushSafe } = useRouterSafe();
const tableData = ref<any[]>([]);
const loading = ref(false);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

const showImportDialog = ref(false);
const importUploadRef = ref();
defineExpose({ importUploadRef });

const filterForm = reactive({
  keyword: "",
  type: "",
  status: "",
});

// 上传相关
const baseUrl = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";
const importUrl = `${baseUrl}/schools/import/excel`;
const uploadHeaders = computed(() => {
  const token = AuthStorage.getToken() || "";
  return { Authorization: token ? `Bearer ${token}` : "" };
});

const typeMap: Record<string, string> = {
  primary: "小学",
  middle: "初中",
  high: "高中",
  vocational: "职业学校",
  other: "其他",
};
const statusMap: Record<string, string> = {
  active: "帮扶中",
  inactive: "未帮扶",
  completed: "已完成",
};

// 统计数据（优先使用服务端全量统计，回退到当前页数据）
const serverSchoolStats = ref<any>(null);
const stats = computed(() => {
  const s = serverSchoolStats.value;
  if (s) {
    return {
      total: s.total_schools ?? (total.value || tableData.value.length),
      active: s.active ?? 0,
      completed: s.completed ?? 0,
      totalStudents:
        s.total_students ??
        tableData.value.reduce(
          (sum: number, sc: any) =>
            sum + (sc.student_count || sc.students || 0),
          0,
        ),
      totalTeachers:
        s.total_teachers ??
        tableData.value.reduce(
          (sum: number, sc: any) =>
            sum + (sc.teacher_count || sc.teachers || 0),
          0,
        ),
    };
  }
  const list = tableData.value;
  return {
    total: total.value || list.length,
    active: list.filter((s) => s.support_status === "active").length,
    completed: list.filter((s) => s.support_status === "completed").length,
    totalStudents: list.reduce(
      (sum, s) => sum + (s.student_count || s.students || 0),
      0,
    ),
    totalTeachers: list.reduce(
      (sum, s) => sum + (s.teacher_count || s.teachers || 0),
      0,
    ),
  };
});

// API 统计数据（助学兴教）
const apiStats = ref({
  project_count: 0,
  project_total_budget: 0,
  scholarship_count: 0,
  scholarship_total_amount: 0,
});
async function loadApiStats() {
  try {
    const data = await schoolApi.getStatistics();
    apiStats.value = data;
    // 服务端返回的 total_schools/active/completed 是全量准确数据
    if (data) serverSchoolStats.value = data;
  } catch (error) {
    logger.error("Failed to load API stats:", error);
  }
}

function getStatusTagType(status: string) {
  if (status === "active") return "success";
  if (status === "completed") return "primary";
  return "info";
}

async function fetchData() {
  loading.value = true;
  try {
    const response = await request.get("/schools", {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        keyword: filterForm.keyword || undefined,
        type: filterForm.type || undefined,
        support_status: filterForm.status || undefined,
      },
    });
    const res = response;
    const inner = res.data || res;
    tableData.value = inner.items || (Array.isArray(inner) ? inner : []);
    total.value = inner.total || tableData.value.length;
  } catch (e) {
    logger.error("加载数据失败:", e);
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  currentPage.value = 1;
  fetchData();
}
function handleReset() {
  filterForm.keyword = "";
  filterForm.type = "";
  filterForm.status = "";
  currentPage.value = 1;
  fetchData();
}
function filterByStatus(status: string) {
  filterForm.status = status;
  currentPage.value = 1;
  fetchData();
}
function handleSizeChange() {
  currentPage.value = 1;
  fetchData();
}
function handlePageChange() {
  fetchData();
}
function handleCreate() {
  pushSafe("/schools/create");
}
function handleView(row: any) {
  if (!row?.id) return;
  pushSafe(`/schools/${row.id}`);
}
function handleEdit(row: any) {
  if (!row?.id) return;
  pushSafe(`/schools/${row.id}/edit`);
}
async function handleDelete(row: any) {
  if (!row?.id) return;
  try {
    await request.delete(`/schools/${row.id}`);
    ElMessage.success("删除成功");
    fetchData();
  } catch (error) {
    logger.error("Failed to delete school:", error);
  }
}
// 下载模板
async function handleDownloadTemplate() {
  try {
    const blob = await downloadImportTemplate("school");
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "学校导入模板.xlsx";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    // 模板下载成功 — 浏览器已确认
  } catch {
    ElMessage.error("模板下载失败");
  }
}

// 导入相关
function beforeImportUpload(file: any) {
  const isExcel = file.name.endsWith(".xlsx") || file.name.endsWith(".xls");
  if (!isExcel) {
    ElMessage.error("只能上传 Excel 文件");
    return false;
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error("文件大小不能超过 10MB");
    return false;
  }
  return true;
}

function onImportSuccess(response: any) {
  const msg = response?.message || `成功导入 ${response?.imported || 0} 所学校`;
  ElMessage.success(msg);
  if (response?.errors?.length) {
    ElMessage.warning(`${response.errors.length} 条数据导入失败`);
  }
  showImportDialog.value = false;
  fetchData();
}

function onImportError() {
  ElMessage.error("导入失败，请检查文件格式");
}

// 导出
async function handleExport() {
  ElMessage.success("正在导出学校数据...");
  try {
    const token = AuthStorage.getToken() || "";
    const resp = await fetch(`${baseUrl}/schools/export/excel`, {
      headers: { Authorization: token ? `Bearer ${token}` : "" },
    });
    if (!resp.ok) throw new Error("export failed");
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "schools.xlsx";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    // 导出成功 — 浏览器已确认
  } catch {
    ElMessage.error("导出失败");
  }
}

onMounted(() => {
  fetchData();
  loadApiStats();
});

// 页面激活时刷新数据（解决keep-alive缓存问题）
onActivated(() => {
  fetchData();
  loadApiStats();
});
</script>

<style scoped>
.school-mgmt-list-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1b4332;
}

.page-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: #666;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.btn-create {
  background: linear-gradient(135deg, #2d6a4f, #40916c) !important;
  border-color: #2d6a4f !important;
  color: white !important;
  font-weight: 600;
  padding: 10px 20px;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(45, 106, 79, 0.3);
  transition: all 0.3s;
}

.btn-create:hover {
  background: linear-gradient(135deg, #1b4332, #2d6a4f) !important;
  box-shadow: 0 4px 12px rgba(27, 67, 50, 0.4);
  transform: translateY(-1px);
}

.import-dialog-body {
  padding: 0 10px;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-item {
  flex: 1;
  background: linear-gradient(
    135deg,
    rgba(27, 67, 50, 0.08) 0%,
    rgba(45, 106, 79, 0.05) 100%
  );
  border: 1px solid rgba(45, 106, 79, 0.2);
  border-radius: 8px;
  padding: 16px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.stat-item:hover {
  border-color: rgba(45, 106, 79, 0.5);
  box-shadow: 0 2px 12px rgba(27, 67, 50, 0.12);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1b4332;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
}

.text-success {
  color: #40916c;
}
.text-primary {
  color: #2d6a4f;
}
.text-warning {
  color: #d4af37;
}
.text-info {
  color: #409eff;
}
.text-project {
  color: #e6a23c;
}
.text-scholarship {
  color: #f56c6c;
}

/* 筛选区 */
.filter-card {
  background: white;
  border-radius: 8px;
  padding: 16px 20px 4px;
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
}

/* 表格区 */
.table-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e4e7ed;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
