<template>
  <div class="contract-container">
    <el-page-header title="返回" @back="$router.back()">
      <template #content
        ><span class="page-title">合同-支付管理</span></template
      >
    </el-page-header>

    <el-card class="mt-4" shadow="never">
      <div class="toolbar">
        <el-select
          v-model="filters.status"
          placeholder="合同状态"
          clearable
          size="default"
          style="width: 140px"
          @change="loadData"
        >
          <el-option label="草稿" value="draft" />
          <el-option label="执行中" value="active" />
          <el-option label="已完成" value="completed" />
          <el-option label="已终止" value="terminated" />
        </el-select>
        <el-button type="primary" @click="showCreateDialog = true"
          >新建合同</el-button
        >
      </div>

      <el-table
        v-loading="loading"
        :data="contracts"
        size="default"
        class="mt-3"
      >
        <el-table-column prop="contract_no" label="合同编号" width="150" />
        <el-table-column
          prop="contract_name"
          label="合同名称"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column
          prop="party_a"
          label="甲方"
          width="150"
          show-overflow-tooltip
        />
        <el-table-column
          prop="party_b"
          label="乙方"
          width="150"
          show-overflow-tooltip
        />
        <el-table-column prop="contract_amount" label="合同金额" width="120" />
        <el-table-column prop="paid_amount" label="已付金额" width="120" />
        <el-table-column label="付款进度" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.payment_progress" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === 'completed'
                  ? 'success'
                  : row.status === 'active'
                    ? 'primary'
                    : row.status === 'terminated'
                      ? 'danger'
                      : 'info'
              "
              size="small"
            >
              {{ row.status_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showPaymentDialog(row)"
              >登记付款</el-button
            >
            <el-button
              v-if="row.status === 'draft'"
              size="small"
              type="danger"
              @click="handleDeleteContract(row.id)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        class="mt-3"
        background
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        @current-change="loadData"
      />
    </el-card>

    <!-- 新建合同对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建合同" width="600px">
      <el-form :model="contractForm" label-width="100px">
        <el-form-item label="合同编号" required
          ><el-input v-model="contractForm.contract_no"
        /></el-form-item>
        <el-form-item label="合同名称" required
          ><el-input v-model="contractForm.contract_name"
        /></el-form-item>
        <el-form-item label="甲方"
          ><el-input v-model="contractForm.party_a"
        /></el-form-item>
        <el-form-item label="乙方"
          ><el-input v-model="contractForm.party_b"
        /></el-form-item>
        <el-form-item label="合同金额"
          ><el-input-number
            v-model="contractForm.contract_amount"
            :min="0"
            :precision="2"
        /></el-form-item>
        <el-form-item label="签订日期"
          ><el-date-picker
            v-model="contractForm.sign_date"
            type="date"
            value-format="YYYY-MM-DD"
        /></el-form-item>
        <el-form-item label="截止日期"
          ><el-date-picker
            v-model="contractForm.deadline"
            type="date"
            value-format="YYYY-MM-DD"
        /></el-form-item>
        <el-form-item label="备注"
          ><el-input v-model="contractForm.remarks" type="textarea"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="handleCreateContract"
          >创建</el-button
        >
      </template>
    </el-dialog>

    <!-- 登记付款对话框 -->
    <el-dialog
      v-model="paymentDialogVisible"
      title="登记合同付款"
      width="500px"
    >
      <el-form :model="paymentForm" label-width="100px">
        <el-form-item label="付款金额" required
          ><el-input-number
            v-model="paymentForm.amount"
            :min="0.01"
            :precision="2"
        /></el-form-item>
        <el-form-item label="付款日期" required
          ><el-date-picker
            v-model="paymentForm.payment_date"
            type="date"
            value-format="YYYY-MM-DD"
        /></el-form-item>
        <el-form-item label="用途"
          ><el-input v-model="paymentForm.purpose"
        /></el-form-item>
        <el-form-item label="凭证号"
          ><el-input v-model="paymentForm.voucher_no"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="paymentDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="handleCreatePayment"
          >提交</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { fundLifecycleApi } from "@/api/fundLifecycle";

const route = useRoute();
const projectId = route.query.project_id
  ? Number(route.query.project_id)
  : undefined;

const loading = ref(false);
const contracts = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;
const filters = reactive({ status: "" });
const showCreateDialog = ref(false);
const paymentDialogVisible = ref(false);
const currentContractId = ref(0);

const contractForm = reactive({
  contract_no: "",
  contract_name: "",
  party_a: "",
  party_b: "",
  contract_amount: 0,
  sign_date: "",
  deadline: "",
  remarks: "",
  project_id: projectId,
  fund_id: undefined as number | undefined,
});

const paymentForm = reactive({
  amount: 0,
  payment_date: "",
  purpose: "",
  voucher_no: "",
});

async function loadData() {
  loading.value = true;
  try {
    const data = await fundLifecycleApi.listContracts({
      project_id: projectId,
      status: filters.status || undefined,
      page: page.value,
      page_size: pageSize,
    });
    contracts.value = data.items || [];
    total.value = data.total || 0;
  } catch {
    ElMessage.error("加载失败");
  } finally {
    loading.value = false;
  }
}

async function handleCreateContract() {
  if (!contractForm.contract_no || !contractForm.contract_name) {
    ElMessage.warning("请填写合同编号和名称");
    return;
  }
  loading.value = true;
  try {
    await fundLifecycleApi.createContract(contractForm);
    ElMessage.success("创建成功");
    showCreateDialog.value = false;
    await loadData();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "创建失败");
  } finally {
    loading.value = false;
  }
}

function showPaymentDialog(contract: any) {
  currentContractId.value = contract.id;
  paymentForm.amount = 0;
  paymentForm.payment_date = "";
  paymentForm.purpose = "";
  paymentForm.voucher_no = "";
  paymentDialogVisible.value = true;
}

async function handleCreatePayment() {
  if (!paymentForm.amount || !paymentForm.payment_date) {
    ElMessage.warning("请填写金额和日期");
    return;
  }
  loading.value = true;
  try {
    await fundLifecycleApi.createContractPayment(
      currentContractId.value,
      paymentForm,
    );
    ElMessage.success("付款登记成功");
    paymentDialogVisible.value = false;
    await loadData();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "登记失败");
  } finally {
    loading.value = false;
  }
}

async function handleDeleteContract(id: number) {
  try {
    await ElMessageBox.confirm("确认删除此合同？", "确认");
    await fundLifecycleApi.deleteContract(id);
    ElMessage.success("已删除");
    await loadData();
  } catch (e: any) {
    if (e !== "cancel")
      ElMessage.error(e?.response?.data?.detail || "删除失败");
  }
}

onMounted(loadData);
</script>

<style scoped>
.contract-container {
  padding: 20px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.mt-3 {
  margin-top: 12px;
}
.mt-4 {
  margin-top: 16px;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
}
</style>
