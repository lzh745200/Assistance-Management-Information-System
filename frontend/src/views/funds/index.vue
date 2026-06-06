<template>
  <div class="fund-management">
    <div class="page-header">
      <h1>经费管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="$router.push('/funds/create')">
          <el-icon><Plus /></el-icon>
          经费登记
        </el-button>
        <el-button @click="handlePrint">
          <el-icon><Printer /></el-icon>
          打印表格
        </el-button>
      </div>
    </div>

    <!-- 经费汇总统计 -->
    <FundSummary :data="summaryData" />

    <div class="search-filters">
      <el-form :model="searchForm" inline>
        <el-form-item label="项目名称">
          <el-input
            v-model="searchForm.project_name"
            placeholder="输入项目名称"
            clearable
          />
        </el-form-item>
        <el-form-item label="经费类型">
          <el-select v-model="searchForm.type" clearable>
            <el-option label="建设经费" value="construction" />
            <el-option label="设备经费" value="equipment" />
            <el-option label="人工经费" value="labor" />
            <el-option label="材料经费" value="material" />
            <el-option label="其他经费" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-card>
      <template #header>
        <div class="table-header">
          <span>经费明细</span>
          <div class="table-actions">
            <el-button text @click="handleExportToExcel">
              <el-icon><Download /></el-icon>
              导出Excel
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="fundList"
        border
        style="width: 100%"
        empty-text="暂无经费数据"
      >
        <el-table-column prop="voucher_number" label="凭证号" width="120" />
        <el-table-column prop="project_name" label="项目名称" min-width="180" />
        <el-table-column prop="type" label="经费类型" width="120">
          <template #default="{ row }">
            {{ getFundTypeText(row.type) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="amount"
          label="金额(元)"
          width="120"
          align="right"
        >
          <template #default="{ row }">
            {{ formatCurrency(row.amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="payment_date" label="支付日期" width="120" />
        <el-table-column prop="payee" label="收款方" width="150" />
        <el-table-column prop="payment_method" label="支付方式" width="100">
          <template #default="{ row }">
            {{ getPaymentMethodText(row.payment_method) }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="用途说明" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'approved' ? 'success' : 'warning'">
              {{ row.status === "approved" ? "已审核" : "待审核" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="approver" label="审核人" width="100" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              link
              type="primary"
              @click="approveFund(row)"
            >
              审核
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 打印组件 -->
    <PrintTable
      v-if="showPrint"
      :visible="true"
      :data="printData"
      :columns="printColumns"
      title="经费明细表"
      @close="showPrint = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Printer, Download } from "@element-plus/icons-vue";
import { useFundsStore } from "@/stores/funds";
import FundSummary from "@/components/common/FundSummary.vue";
import PrintTable from "@/components/common/PrintTable.vue";
import { exportToExcel } from "@/utils/export";
import { SearchForm } from "@/types/index";

const router = useRouter();
const fundStore = useFundsStore();

// 定义SearchForm扩展接口以包含dateRange
interface ExtendedSearchForm extends SearchForm {
  project_name: string;
  type: string;
  dateRange: [string, string];
}

// 使用明确的类型定义
const searchForm = reactive<ExtendedSearchForm>({
  project_name: "",
  type: "",
  dateRange: ["", ""] as [string, string],
});

const loading = ref(false);
const showPrint = ref(false);

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
});

// 定义汇总数据类型
interface SummaryData {
  totalBudget: number;
  totalExpenditure: number;
  remainingBudget: number;
  byType: Array<{ type: string; amount: number }>;
}

const summaryData = ref<SummaryData>({
  totalBudget: 0,
  totalExpenditure: 0,
  remainingBudget: 0,
  byType: [],
});

// 定义fundList的类型
interface FundItem {
  id: number;
  voucher_number: string;
  project_name: string;
  type: string;
  amount: number;
  payment_date: string;
  payee: string;
  payment_method: string;
  description: string;
  status: "approved" | "pending";
  approver?: string;
}

const fundList = ref<FundItem[]>([]);

const printData = computed(() => fundList.value);
const printColumns = ref([
  { key: "voucher_number", label: "凭证号" },
  { key: "project_name", label: "项目名称" },
  { key: "type", label: "经费类型" },
  { key: "amount", label: "金额(元)" },
  { key: "payment_date", label: "支付日期" },
  { key: "payee", label: "收款方" },
  { key: "payment_method", label: "支付方式" },
  { key: "description", label: "用途说明" },
]);

onMounted(() => {
  loadFunds();
  loadSummary();
});

const loadFunds = async () => {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size,
    };
    if (searchForm.project_name) params.keyword = searchForm.project_name;
    if (searchForm.type) params.fund_type = searchForm.type;
    if (searchForm.dateRange?.[0]) params.start_date = searchForm.dateRange[0];
    if (searchForm.dateRange?.[1]) params.end_date = searchForm.dateRange[1];
    await fundStore.fetchFunds(params);
    fundList.value = fundStore.fundList as any;
    pagination.total = fundStore.total;
  } catch {
    ElMessage.error("加载经费明细失败");
  } finally {
    loading.value = false;
  }
};

const loadSummary = async () => {
  try {
    const data = await fundStore.getSummary();
    summaryData.value = data;
  } catch (error) {
    ElMessage.error("加载经费汇总失败");
  }
};

const handleSearch = () => {
  pagination.page = 1;
  loadFunds();
};

const handleReset = () => {
  Object.assign(searchForm, {
    project_name: "",
    type: "",
    dateRange: [],
  });
  pagination.page = 1;
  loadFunds();
};

const handleSizeChange = (size: number) => {
  pagination.page_size = size;
  loadFunds();
};

const handleCurrentChange = (page: number) => {
  pagination.page = page;
  loadFunds();
};

const formatCurrency = (value: number): string => {
  if (!value) return "0.00";
  return value.toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const getFundTypeText = (type: string): string => {
  const types: Record<string, string> = {
    construction: "建设经费",
    equipment: "设备经费",
    labor: "人工经费",
    material: "材料经费",
    other: "其他经费",
  };
  return types[type] || type;
};

const getPaymentMethodText = (method: string): string => {
  const methods: Record<string, string> = {
    bank_transfer: "银行转账",
    cash: "现金",
    check: "支票",
    online: "在线支付",
  };
  return methods[method] || method;
};

const viewDetail = (fund: FundItem) => {
  router.push({
    path: `/funds/${fund.id}`,
  });
};

const approveFund = async (fund: FundItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要审核通过这笔经费吗？\n金额：${formatCurrency(fund.amount)}元`,
      "审核确认",
      {
        type: "warning",
      },
    );
    await fundStore.approveFund(fund.id);
    ElMessage.success("审核通过");
    loadFunds();
  } catch {
    // 用户取消
  }
};

const handlePrint = () => {
  showPrint.value = true;
};

// 重命名函数以避免与导入的exportToExcel冲突
const handleExportToExcel = () => {
  const data = fundList.value.map((item) => ({
    凭证号: item.voucher_number,
    项目名称: item.project_name,
    经费类型: getFundTypeText(item.type),
    "金额(元)": item.amount,
    支付日期: item.payment_date,
    收款方: item.payee,
    支付方式: getPaymentMethodText(item.payment_method),
    用途说明: item.description,
    状态: item.status === "approved" ? "已审核" : "待审核",
    审核人: item.approver || "",
  }));
  // 使用从@/utils/export导入的exportToExcel函数
  exportToExcel(data, "经费明细表");
};
</script>

<style scoped>
.fund-management {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
  font-size: 20px;
}

.search-filters {
  background: white;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
