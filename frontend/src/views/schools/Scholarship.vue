<template>
  <div class="scholarship-page">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="pushSafe(`/schools/${schoolId}`)"
          >返回详情</el-button
        >
        <h2 class="page-title">资助学生管理</h2>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon>新增
        </el-button>
        <el-button type="warning" plain @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>Excel导入
        </el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-select
        v-model="filterYear"
        placeholder="筛选年度"
        clearable
        style="width: 130px"
        @change="loadData"
      >
        <el-option
          v-for="y in yearOptions"
          :key="y"
          :label="String(y)"
          :value="y"
        />
      </el-select>
    </div>

    <el-table v-loading="loading" :data="students" stripe border>
      <el-table-column type="index" label="序号" width="60" align="center" />
      <el-table-column prop="student_name" label="学生姓名" width="100" />
      <el-table-column prop="grade" label="年级" width="80" />
      <el-table-column prop="year" label="年度" width="80" />
      <el-table-column
        prop="amount"
        label="资助金额(元)"
        width="120"
        align="right"
      />
      <el-table-column
        prop="reason"
        label="资助原因"
        min-width="160"
        show-overflow-tooltip
      />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="statusTagType(row.status)">{{
            statusMap[row.status] || row.status
          }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="contact_info"
        label="联系方式"
        width="120"
        show-overflow-tooltip
      />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="openDialog(row)"
            >编辑</el-button
          >
          <el-popconfirm title="确定删除？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button type="danger" link size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingItem ? '编辑资助学生' : '新增资助学生'"
      width="550px"
      destroy-on-close
    >
      <el-form :model="form" label-width="90px">
        <el-form-item label="学生姓名" required>
          <el-input v-model="form.student_name" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="年级">
              <el-input v-model="form.grade" placeholder="如：三年级" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="资助年度">
              <el-input-number
                v-model="form.year"
                :min="2020"
                :max="2030"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="资助金额">
              <el-input-number
                v-model="form.amount"
                :min="0"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select
                v-model="form.status"
                placeholder="请选择状态"
                clearable
                style="width: 100%"
              >
                <el-option label="待审批" value="pending" />
                <el-option label="已批准" value="approved" />
                <el-option label="已发放" value="disbursed" />
                <el-option label="已完成" value="completed" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="资助原因">
          <el-input v-model="form.reason" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="form.contact_info" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave"
          >保存</el-button
        >
      </template>
    </el-dialog>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入资助学生"
      width="500px"
      destroy-on-close
    >
      <el-alert
        title="Excel格式：学生姓名、年级、年度、金额、原因、状态"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 16px"
      />
      <el-upload
        :action="importUrl"
        :headers="uploadHeaders"
        :on-success="onImportSuccess"
        :on-error="() => ElMessage.error('导入失败')"
        :limit="1"
        accept=".xlsx,.xls"
        drag
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">拖拽或点击上传 Excel</div>
      </el-upload>
      <template #footer>
        <el-button @click="showImportDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { logger } from "@/utils/logger";
import { AuthStorage } from "@/utils/authStorage";

import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useRouterSafe } from "@/composables/useRouterSafe";
import { ElMessage } from "element-plus";
import { ArrowLeft, Plus, Upload } from "@element-plus/icons-vue";
import { schoolApi } from "@/api/schools";

const { pushSafe } = useRouterSafe();
const route = useRoute();
const schoolId = Number(route.params.id);

const loading = ref(false);
const saving = ref(false);
const students = ref<any[]>([]);
const dialogVisible = ref(false);
const editingItem = ref<any>(null);
const filterYear = ref<number | undefined>(undefined);
const showImportDialog = ref(false);

const yearOptions = Array.from({ length: 11 }, (_, i) => 2020 + i);
const statusMap: Record<string, string> = {
  pending: "待审批",
  approved: "已批准",
  disbursed: "已发放",
  completed: "已完成",
};
function statusTagType(s: string) {
  if (s === "disbursed" || s === "completed") return "success";
  if (s === "approved") return "primary";
  return "info";
}

const baseUrl = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";
const importUrl = `${baseUrl}/schools/${schoolId}/scholarship-students/import`;
const uploadHeaders = computed(() => {
  const token = AuthStorage.getToken() || "";
  return { Authorization: token ? `Bearer ${token}` : "" };
});

const form = ref({
  student_name: "",
  grade: "",
  year: new Date().getFullYear(),
  amount: 0,
  reason: "",
  status: "pending",
  contact_info: "",
});

async function loadData() {
  loading.value = true;
  try {
    const res = await schoolApi.listScholarshipStudents(
      schoolId,
      filterYear.value,
    );
    students.value = res.items || [];
  } catch (error) {
    logger.error("Failed to load scholarship students:", error);
  } finally {
    loading.value = false;
  }
}

function openDialog(row?: any) {
  editingItem.value = row || null;
  if (row) {
    form.value = { ...row };
  } else {
    form.value = {
      student_name: "",
      grade: "",
      year: new Date().getFullYear(),
      amount: 0,
      reason: "",
      status: "pending",
      contact_info: "",
    };
  }
  dialogVisible.value = true;
}

async function handleSave() {
  if (!form.value.student_name) {
    ElMessage.warning("请输入学生姓名");
    return;
  }
  saving.value = true;
  try {
    if (editingItem.value) {
      await schoolApi.updateScholarshipStudent(
        schoolId,
        editingItem.value.id,
        form.value,
      );
      ElMessage.success("更新成功");
    } else {
      await schoolApi.createScholarshipStudent(schoolId, form.value);
      ElMessage.success("创建成功");
    }
    dialogVisible.value = false;
    loadData();
  } catch {
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
}

async function handleDelete(row: any) {
  try {
    await schoolApi.deleteScholarshipStudent(schoolId, row.id);
    ElMessage.success("删除成功");
    loadData();
  } catch (error) {
    logger.error("Failed to delete scholarship student:", error);
  }
}

function onImportSuccess(response: any) {
  ElMessage.success(response?.message || "导入成功");
  showImportDialog.value = false;
  loadData();
}

onMounted(() => loadData());
</script>

<style scoped>
.scholarship-page {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-actions {
  display: flex;
  gap: 10px;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1b4332;
}
.filter-bar {
  margin-bottom: 16px;
}
</style>
