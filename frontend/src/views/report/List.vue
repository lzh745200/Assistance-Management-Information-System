<template>
  <div class="report-list-page">
    <div class="page-header">
      <h2>报表订阅管理</h2>
      <el-button type="primary" @click="openDialog()"><el-icon><Plus /></el-icon>新增订阅</el-button>
    </div>

    <el-card>
      <el-table :data="subscriptions" v-loading="loading" stripe border>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="name" label="订阅名称" min-width="150" />
        <el-table-column prop="report_type" label="报表类型" width="120">
          <template #default="{ row }">{{ typeLabel(row.report_type) }}</template>
        </el-table-column>
        <el-table-column prop="format" label="格式" width="80">
          <template #default="{ row }"><el-tag size="small">{{ row.format || 'xlsx' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="frequency" label="频率" width="80">
          <template #default="{ row }">{{ freqLabel(row.frequency) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch :model-value="row.is_active" @change="toggle(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="last_sent_at" label="上次发送" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleGenerate(row)">生成</el-button>
            <el-button size="small" @click="handleDownload(row)">下载</el-button>
            <el-button size="small" type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && subscriptions.length === 0" description="暂无报表订阅，点击新增订阅" />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑订阅' : '新增订阅'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="订阅名称" prop="name">
          <el-input v-model="form.name" placeholder="如：月度工作汇总" />
        </el-form-item>
        <el-form-item label="报表类型" prop="report_type">
          <el-select v-model="form.report_type" placeholder="选择类型">
            <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="输出格式" prop="format">
          <el-radio-group v-model="form.format"><el-radio value="xlsx">Excel</el-radio><el-radio value="pdf">PDF</el-radio></el-radio-group>
        </el-form-item>
        <el-form-item label="年度" prop="year">
          <el-input-number v-model="form.year" :min="2020" :max="2099" />
        </el-form-item>
        <el-form-item label="生成频率" prop="frequency">
          <el-select v-model="form.frequency">
            <el-option label="手动" value="manual" /><el-option label="每日" value="daily" />
            <el-option label="每周" value="weekly" /><el-option label="每月" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item label="接收邮箱">
          <el-input v-model="form.email" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { reportApi } from "@/api/report";

const subscriptions = ref<any[]>([]);
const loading = ref(false);
const saving = ref(false);
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const formRef = ref<any>(null);

const currentYear = new Date().getFullYear();
const defaultForm = () => ({
  name: "", report_type: "comprehensive", format: "xlsx", year: currentYear,
  frequency: "manual", email: "",
});

const form = ref(defaultForm());
const rules = {
  name: [{ required: true, message: "请输入名称", trigger: "blur" }],
  report_type: [{ required: true, message: "请选择类型", trigger: "change" }],
};

const typeOptions = [
  { label: "综合报表", value: "comprehensive" }, { label: "帮扶村报表", value: "supported_villages" },
  { label: "项目报表", value: "projects" }, { label: "经费报表", value: "funds" },
  { label: "学校报表", value: "schools" }, { label: "乡村振兴", value: "rural_work" },
];

function typeLabel(v: string) { return typeOptions.find(t => t.value === v)?.label || v; }
function freqLabel(v: string) {
  const m: Record<string, string> = { manual: "手动", daily: "每日", weekly: "每周", monthly: "每月" };
  return m[v] || v;
}

async function loadList() {
  loading.value = true;
  try {
    const res: any = await reportApi.list();
    subscriptions.value = res?.items || res?.data?.items || res || [];
  } catch { subscriptions.value = []; }
  finally { loading.value = false; }
}

function openDialog(row?: any) {
  editingId.value = row?.id || null;
  form.value = row ? { ...row } : defaultForm();
  dialogVisible.value = true;
}

async function handleSave() {
  if (!formRef.value) return;
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;
  saving.value = true;
  try {
    if (editingId.value) {
      await reportApi.update(editingId.value, form.value);
      ElMessage.success("已保存");
    } else {
      await reportApi.create(form.value);
      ElMessage.success("创建成功");
    }
    dialogVisible.value = false;
    loadList();
  } catch { ElMessage.error("保存失败"); }
  finally { saving.value = false; }
}

async function toggle(row: any) {
  try { await reportApi.toggle(row.id); row.is_active = !row.is_active; }
  catch { ElMessage.error("操作失败"); }
}

async function handleGenerate(row: any) {
  try { await reportApi.generate({ subscription_id: row.id }); ElMessage.success("已生成"); }
  catch { ElMessage.error("生成失败"); }
}

function handleDownload(row: any) {
  if (!row.id) return;
  reportApi.download(row.id).then((res: any) => {
    const blob = new Blob([res.data || res], { type: "application/octet-stream" });
    const link = document.createElement("a"); link.href = URL.createObjectURL(blob);
    link.download = `report_${row.id}.xlsx`; link.click();
  }).catch(() => ElMessage.error("下载失败"));
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm("确定删除此订阅？", "提示", { type: "warning" });
    await reportApi.delete(row.id);
    ElMessage.success("已删除");
    loadList();
  } catch { /* cancelled */ }
}

onMounted(loadList);
</script>

<style scoped>
.report-list-page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; color: #303133; }
</style>
