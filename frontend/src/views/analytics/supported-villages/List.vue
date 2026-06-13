<template>
  <div class="supported-village-list">
    <!-- 搜索筛选区域 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索村庄名称/单位"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="部门">
          <el-select
            v-model="filters.department"
            placeholder="选择部门"
            clearable
          >
            <el-option
              v-for="dept in filterOptions.departments"
              :key="dept"
              :label="dept"
              :value="dept"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所在县市">
          <el-select
            v-model="filters.county"
            placeholder="选择县市"
            clearable
            style="width: 140px"
          >
            <el-option
              v-for="c in filterOptions.counties"
              :key="c"
              :label="c"
              :value="c"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="振兴梯队">
          <el-switch v-model="filters.isRevitalizationTier" />
        </el-form-item>
        <el-form-item label="三区三州">
          <el-select
            v-model="filters.isThreeRegions"
            placeholder="全部"
            clearable
          >
            <el-option label="是" :value="1" />
            <el-option label="否" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item label="民族地区">
          <el-select
            v-model="filters.isEthnicArea"
            placeholder="全部"
            clearable
          >
            <el-option label="是" :value="1" />
            <el-option label="否" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item label="重点帮扶县">
          <el-select
            v-model="filters.isKeyCounty"
            placeholder="全部"
            clearable
            style="width: 140px"
          >
            <el-option label="是" :value="1" />
            <el-option label="否" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item label="年份">
          <el-select
            v-model="filters.yearStart"
            placeholder="选择年份"
            clearable
          >
            <el-option
              v-for="y in filterOptions.years"
              :key="y"
              :label="`${y}年`"
              :value="y"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="action-bar-left">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增帮扶村
        </el-button>
        <el-button @click="handleImport">
          <el-icon><Upload /></el-icon>
          导入数据
        </el-button>
        <el-button :loading="exporting" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
        <el-button @click="handleDownloadTemplate">
          <el-icon><Download /></el-icon>
          下载模板
        </el-button>
      </div>
      <div v-if="selectedRows.length > 0" class="action-bar-right">
        <span class="selection-info">已选择 {{ selectedRows.length }} 条</span>
        <el-popconfirm
          :title="`确定批量删除这 ${selectedRows.length} 条记录吗？`"
          @confirm="handleBatchDelete"
        >
          <template #reference>
            <el-button type="danger" :loading="batchDeleting">
              <el-icon><Delete /></el-icon>
              批量删除
            </el-button>
          </template>
        </el-popconfirm>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-card shadow="never">
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="tableData"
        stripe
        border
        @sort-change="handleSortChange"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column
          prop="department"
          label="部门单位"
          min-width="120"
          sortable="custom"
        />
        <el-table-column prop="supportUnit" label="帮扶单位" min-width="120" />
        <el-table-column prop="villageName" label="帮扶村名称" min-width="120">
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewDetail(row)">
              {{ row.villageName }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="regionScope" label="地区范围" width="100" />
        <el-table-column label="地域属性" width="280">
          <template #default="{ row }">
            <el-tag v-if="row.isThreeRegions" size="small" type="danger"
              >三区三州</el-tag
            >
            <el-tag v-if="row.isBorderArea" size="small">边疆地区</el-tag>
            <el-tag v-if="row.isEthnicArea" size="small" type="info"
              >民族地区</el-tag
            >
            <el-tag v-if="row.isRevolutionaryArea" size="small" type="success"
              >革命地区</el-tag
            >
            <el-tag v-if="row.isKeyCounty" size="small" type="warning"
              >重点帮扶县</el-tag
            >
          </template>
        </el-table-column>
        <el-table-column label="振兴属性" width="180">
          <template #default="{ row }">
            <el-tag v-if="row.isRevitalizationTier" size="small" type="danger">
              振兴梯队
            </el-tag>
            <el-tag v-if="row.isProvincialDemo" size="small" type="success"
              >省级示范</el-tag
            >
            <el-tag v-if="row.isHundredVillageDemo" size="small" type="success"
              >百村示范</el-tag
            >
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <div class="operation-buttons">
              <el-button
                type="primary"
                link
                size="small"
                @click="handleView(row)"
                >查看</el-button
              >
              <el-button
                type="primary"
                link
                size="small"
                @click="handleEdit(row)"
                >编辑</el-button
              >
              <el-button
                type="primary"
                link
                size="small"
                @click="handleYearlyData(row)"
                >年度数据</el-button
              >
              <el-popconfirm
                title="确定删除该帮扶村记录吗？"
                @confirm="handleDelete(row)"
              >
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="(pagination as any)?.data?.total || (pagination as any)?.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      destroy-on-close
    >
      <SupportedVillageForm
        v-if="dialogVisible"
        :village="currentVillage"
        :mode="dialogMode"
        @submit="handleFormSubmit"
        @cancel="dialogVisible = false"
      />
    </el-dialog>

    <!-- 年度数据对话框 -->
    <el-dialog
      v-model="yearlyDialogVisible"
      title="年度数据管理"
      width="900px"
      destroy-on-close
    >
      <YearlyDataForm
        v-if="yearlyDialogVisible && currentVillage"
        :village-id="currentVillage.id"
        :village-name="currentVillage.villageName"
        @close="yearlyDialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { logger } from "@/utils/logger";

import { ref, reactive, computed, onMounted } from "vue";
import { useRouterSafe } from "@/composables/useRouterSafe";
import { ElMessage } from "element-plus";
import {
  Search,
  Refresh,
  Plus,
  Download,
  Upload,
  Delete,
} from "@element-plus/icons-vue";
import {
  getSupportedVillages,
  deleteSupportedVillage,
  batchDeleteSupportedVillages,
  createSupportedVillage,
  updateSupportedVillage,
  saveTransitionFunding,
  importSupportedVillages,
  exportSupportedVillages,
  downloadImportTemplate,
  getFilterOptions,
} from "@/api/supportedVillage";
import type {
  SupportedVillage,
  SupportedVillageCreate,
  VillageFilters,
} from "@/types/analytics";
import SupportedVillageForm from "./components/SupportedVillageForm.vue";
import YearlyDataForm from "./components/YearlyDataForm.vue";

const { pushSafe } = useRouterSafe();

// 状态
const loading = ref(false);
const exporting = ref(false);
const batchDeleting = ref(false);
const tableData = ref<SupportedVillage[]>([]);
const selectedRows = ref<SupportedVillage[]>([]);
const tableRef = ref();
const dialogVisible = ref(false);
const yearlyDialogVisible = ref(false);
const dialogMode = ref<"create" | "edit" | "view">("create");
const currentVillage = ref<SupportedVillage | null>(null);

// 筛选条件
const filters = reactive<VillageFilters>({
  keyword: "",
  department: undefined,
  county: undefined,
  isRevitalizationTier: undefined,
  isThreeRegions: undefined,
  isEthnicArea: undefined,
  isKeyCounty: undefined,
});

// 筛选选项
const filterOptions = ref<{
  departments: string[];
  supportUnits: string[];
  counties: string[];
  regionScopes: string[];
  tieredLevels: string[];
  years: number[];
}>({
  departments: [],
  supportUnits: [],
  counties: [],
  regionScopes: [],
  tieredLevels: [],
  years: [],
});

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
});

// 排序
const sortParams = reactive({
  prop: "",
  order: "",
});

// 计算属性
const dialogTitle = computed(() => {
  const titles = {
    create: "新增帮扶村",
    edit: "编辑帮扶村",
    view: "查看帮扶村",
  };
  return titles[dialogMode.value];
});

// 加载数据
async function loadData() {
  loading.value = true;
  try {
    const response = await getSupportedVillages({
      page: pagination.page,
      pageSize: pagination.pageSize,
      filters: {
        keyword: filters.keyword || undefined,
        department: filters.department || undefined,
        county: filters.county || undefined,
        isRevitalizationTier: filters.isRevitalizationTier || undefined,
        isThreeRegions: filters.isThreeRegions,
        isEthnicArea: filters.isEthnicArea,
        isKeyCounty: filters.isKeyCounty,
      },
    });
    tableData.value = (response as any)?.data?.items || (response as any)?.items;
    pagination.total = (response as any)?.data?.total || (response as any)?.total || tableData.value.length;
  } catch (error) {
    ElMessage.error("加载数据失败");
  } finally {
    loading.value = false;
  }
}

// 加载筛选选项
async function loadFilterOptions() {
  try {
    filterOptions.value = await getFilterOptions();
  } catch (error) {
    logger.error("加载筛选选项失败:", error);
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1;
  loadData();
}

// 重置
function handleReset() {
  Object.assign(filters, {
    keyword: "",
    department: undefined,
    county: undefined,
    isRevitalizationTier: undefined,
    isThreeRegions: undefined,
    isEthnicArea: undefined,
    isKeyCounty: undefined,
  });
  pagination.page = 1;
  loadData();
}

// 排序变化
function handleSortChange({ prop, order }: { prop: string; order: string }) {
  sortParams.prop = prop;
  sortParams.order = order;
  loadData();
}

// 分页变化
function handleSizeChange(size: number) {
  pagination.pageSize = size;
  pagination.page = 1;
  loadData();
}

function handlePageChange(page: number) {
  pagination.page = page;
  loadData();
}

// 新增
function handleCreate() {
  logger.info("点击新增帮扶村");
  dialogMode.value = "create";
  currentVillage.value = null;
  dialogVisible.value = true;
  logger.info("dialogVisible set to:", dialogVisible.value);
}

// 查看（对话框模式）
function handleView(row: SupportedVillage) {
  dialogMode.value = "view";
  currentVillage.value = row;
  dialogVisible.value = true;
}

// 查看详情页
function handleViewDetail(row: SupportedVillage) {
  pushSafe(`/supported-villages/${row.id}`);
}

// 编辑
function handleEdit(row: SupportedVillage) {
  dialogMode.value = "edit";
  currentVillage.value = row;
  dialogVisible.value = true;
}

// 年度数据 - 跳转到独立页面
function handleYearlyData(row: SupportedVillage) {
  pushSafe(`/supported-villages/${row.id}/yearly`);
}

// 删除
async function handleDelete(row: SupportedVillage) {
  try {
    await deleteSupportedVillage(row.id);
    ElMessage.success("删除成功");
    loadData();
  } catch (error) {
    ElMessage.error("删除失败");
  }
}

// 批量选择
function handleSelectionChange(rows: SupportedVillage[]) {
  selectedRows.value = rows;
}

// 批量删除
async function handleBatchDelete() {
  if (selectedRows.value.length === 0) return;
  batchDeleting.value = true;
  try {
    const ids = selectedRows.value.map((row) => row.id);
    const result = await batchDeleteSupportedVillages(ids);
    ElMessage.success(result.message);
    selectedRows.value = [];
    if (tableRef.value) tableRef.value.clearSelection();
    loadData();
  } catch (error) {
    ElMessage.error("批量删除失败");
  } finally {
    batchDeleting.value = false;
  }
}

// 表单提交
async function handleFormSubmit(data: SupportedVillageCreate) {
  logger.info("收到表单提交事件，数据:", data);
  try {
    if (dialogMode.value === "create") {
      logger.info("创建帮扶村...");
      const fundingItems = (data as any)._transitionFundingItems;
      delete (data as any)._transitionFundingItems;
      const created = await createSupportedVillage(data);
      const villageId = created?.data?.id || created?.id;
      if (fundingItems?.length && villageId) {
        try {
          await saveTransitionFunding(villageId, { items: fundingItems });
        } catch (fundErr: any) {
          logger.error("创建时保存过渡资金失败:", fundErr);
        }
      }
      ElMessage.success("创建成功");
    } else if (dialogMode.value === "edit" && currentVillage.value) {
      logger.info("更新帮扶村，ID:", currentVillage.value.id);
      await updateSupportedVillage(currentVillage.value.id, data);
      ElMessage.success("更新成功");
    }
    dialogVisible.value = false;
    loadData();
  } catch (error: any) {
    logger.error("保存失败:", error);
    ElMessage.error(dialogMode.value === "create" ? "创建失败" : "更新失败");
  }
}

// 导出
async function handleExport() {
  exporting.value = true;
  try {
    const blob = await exportSupportedVillages({
      year: new Date().getFullYear(),
      filters: {
        keyword: filters.keyword || undefined,
        department: filters.department || undefined,
        county: filters.county || undefined,
        isRevitalizationTier: filters.isRevitalizationTier || undefined,
        isThreeRegions: filters.isThreeRegions,
        isEthnicArea: filters.isEthnicArea,
        isKeyCounty: filters.isKeyCounty,
      },
    });

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `帮扶村数据_${new Date().getFullYear()}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);

    ElMessage.success("导出成功");
  } catch (error: any) {
    logger.error("导出失败:", error);
    ElMessage.error("导出功能需要后端支持，请先启动后端服务");
  } finally {
    exporting.value = false;
  }
}

// 导入
function handleImport() {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".xlsx,.xls";
  input.onchange = async (e: any) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const result = await importSupportedVillages(file);
      ElMessage.success(
        `导入成功：${result.imported}条，失败：${result.failed}条`,
      );
      if (result.errors && result.errors.length > 0) {
        logger.error("导入错误:", result.errors);
        ElMessage.warning(
          `有${result.errors.length}条数据导入失败，请检查数据格式`,
        );
      }
      loadData();
    } catch (error: any) {
      logger.error("导入失败:", error);
      ElMessage.error("导入功能需要后端支持，请先启动后端服务");
    }
  };
  input.click();
}

// 下载模板
async function handleDownloadTemplate() {
  try {
    const res = await downloadImportTemplate();
    const blob = res.data || res;

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "帮扶村导入模板.xlsx";
    link.click();
    window.URL.revokeObjectURL(url);

    ElMessage.success("模板下载成功");
  } catch (error: any) {
    logger.error("下载模板失败:", error);
    ElMessage.error("下载模板功能需要后端支持，请先启动后端服务");
  }
}

// 初始化
onMounted(() => {
  loadFilterOptions();
  loadData();
});
</script>

<style scoped lang="scss">
.supported-village-list {
  padding: 16px;
}

.filter-card {
  margin-bottom: 16px;
}

.action-bar {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-bar-left {
  display: flex;
  gap: 12px;
}

.action-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selection-info {
  color: #409eff;
  font-size: 14px;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.operation-buttons {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: nowrap;
  gap: 4px;
  white-space: nowrap;
}
</style>
