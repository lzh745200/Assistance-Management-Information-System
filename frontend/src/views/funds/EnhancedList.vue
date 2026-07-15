<template>
  <div class="fund-list-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">经费管理</h2>
        <p class="page-desc">管理帮扶经费记录，跟踪资金流向与使用情况</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>新增经费
        </el-button>
        <el-button @click="pushSafe('/funds/budget')">
          <el-icon><Tickets /></el-icon>预算管理
        </el-button>
        <el-button @click="handleDownloadTemplate">
          <el-icon><Download /></el-icon>下载模板
        </el-button>
        <el-button :loading="exporting" :disabled="exporting" @click="handleExport">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-item">
        <div class="stat-value">{{ stats.totalAmount }}</div>
        <div class="stat-label">经费总额(万元)</div>
      </div>
      <div class="stat-item" @click="filterByStatus('allocated')">
        <div class="stat-value text-success">{{ stats.allocatedAmount }}</div>
        <div class="stat-label">已拨付(万元)</div>
      </div>
      <div class="stat-item" @click="filterByStatus('pending')">
        <div class="stat-value text-warning">{{ stats.pendingCount }}</div>
        <div class="stat-label">待审批</div>
      </div>
      <div class="stat-item" @click="filterByStatus('planned')">
        <div class="stat-value text-info">{{ stats.plannedCount }}</div>
        <div class="stat-label">规划中</div>
      </div>
      <div class="stat-item">
        <div class="stat-value text-primary">{{ stats.totalCount }}</div>
        <div class="stat-label">记录总数</div>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <div class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="经费名称">
          <el-input
            v-model="filterForm.keyword"
            placeholder="名称/项目/来源"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="经费类型">
          <el-select
            v-model="filterForm.type"
            placeholder="全部类型"
            clearable
            style="width: 130px"
          >
            <el-option label="项目经费" value="project" />
            <el-option label="运营经费" value="operation" />
            <el-option label="教育帮扶" value="education" />
            <el-option label="基础设施" value="infrastructure" />
            <el-option label="应急经费" value="emergency" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="filterForm.status"
            placeholder="全部状态"
            clearable
            style="width: 130px"
          >
            <el-option label="待审批" value="pending" />
            <el-option label="已计划" value="planned" />
            <el-option label="已批准" value="approved" />
            <el-option label="已拨付" value="allocated" />
            <el-option label="使用中" value="in_use" />
            <el-option label="已完成" value="completed" />
            <el-option label="已审计" value="audited" />
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
      <!-- 批量操作工具栏 -->
      <div v-if="selectedRows.length > 0" class="batch-toolbar">
        <span class="batch-info">已选择 {{ selectedRows.length }} 项</span>
        <el-button
          type="danger"
          size="small"
          :loading="batchDeleting"
          :disabled="batchDeleting"
          @click="handleBatchDelete"
        >
          批量删除
        </el-button>
        <el-button
          size="small"
          :loading="exporting"
          :disabled="exporting"
          @click="handleBatchExport"
        >
          导出选中
        </el-button>
        <el-button size="small" text @click="clearSelection">取消选择</el-button>
      </div>
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="tableData"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="45" />
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="经费名称" min-width="180">
          <template #default="scope">
            <el-link type="primary" @click="handleView(scope.row)">{{ scope.row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="110" align="center">
          <template #default="scope">
            <el-tag size="small">{{ getTypeName(scope.row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额(万元)" width="120" align="right">
          <template #default="scope">
            <span class="amount-text">{{ formatAmount(scope.row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="project_name" label="关联项目" width="160" show-overflow-tooltip>
          <template #default="scope">
            {{ scope.row.project_name || scope.row.project || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="经费来源" width="120" show-overflow-tooltip />
        <el-table-column label="健康度" width="100" align="center">
          <template #default="scope">
            <el-progress
              v-if="scope.row.health_score != null"
              type="circle"
              :percentage="scope.row.health_score"
              :width="36"
              :stroke-width="4"
              :color="
                scope.row.health_score >= 80
                  ? '#67c23a'
                  : scope.row.health_score >= 60
                    ? '#e6a23c'
                    : '#f56c6c'
              "
            />
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column label="阶段" width="110" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.lifecycle_phase" size="small" effect="plain">
              {{ phaseLabels[scope.row.lifecycle_phase] || `阶段${scope.row.lifecycle_phase}` }}
            </el-tag>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="日期" width="110" align="center">
          <template #default="scope">
            {{
              scope.row.date || (scope.row.created_at ? scope.row.created_at.split('T')[0] : '-')
            }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button type="primary" link size="small" @click="handleView(scope.row)"
              >查看</el-button
            >
            <el-button
              v-if="scope.row.project_id"
              type="primary"
              link
              size="small"
              @click="pushSafe('/funds/lifecycle/' + scope.row.project_id)"
              >生命周期</el-button
            >
            <el-button type="primary" link size="small" @click="handleEdit(scope.row)"
              >编辑</el-button
            >
            <el-button
              v-if="scope.row.status === 'pending'"
              type="success"
              link
              size="small"
              :loading="approving[scope.row.id]"
              :disabled="approving[scope.row.id]"
              @click="quickApprove(scope.row)"
              >审批</el-button
            >
            <el-button
              v-if="scope.row.status === 'approved'"
              type="warning"
              link
              size="small"
              :loading="allocating[scope.row.id]"
              :disabled="allocating[scope.row.id]"
              @click="quickAllocate(scope.row)"
              >拨付</el-button
            >
            <el-popconfirm title="确定删除该经费记录吗？" @confirm="handleDelete(scope.row)">
              <template #reference>
                <el-button
                  type="danger"
                  link
                  size="small"
                  :loading="deleting[scope.row.id]"
                  :disabled="deleting[scope.row.id]"
                  >删除</el-button
                >
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
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'

import { ref, reactive, computed, onMounted } from 'vue'
import { useRouterSafe } from '@/composables/useRouterSafe'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Search, Tickets } from '@element-plus/icons-vue'
import { get, del, apiRequest } from '@/api/request'
import { fundApi } from '@/api/funds'
import { downloadImportTemplateAndSave } from '@/api/import'

const phaseLabels: Record<number, string> = {
  1: '论证立项',
  2: '汇总审核',
  3: '计划拨付',
  4: '军地对接',
  5: '实施监管',
  6: '核查督查',
  7: '决算绩效',
}

const { pushSafe } = useRouterSafe()
const tableData = ref<any[]>([])
const loading = ref(false)
const exporting = ref(false)
const approving = ref<Record<number, boolean>>({})
const allocating = ref<Record<number, boolean>>({})
const deleting = ref<Record<number, boolean>>({})
const batchDeleting = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const selectedRows = ref<any[]>([])
const tableRef = ref<any>(null)

const filterForm = reactive({
  keyword: '',
  type: '',
  status: '',
})

// 服务端统计数据（全量准确）
const serverStats = ref<any>(null)
const stats = computed(() => {
  const s = serverStats.value
  if (s) {
    const byStatus = s.by_status || {}
    return {
      totalAmount: formatAmount(s.total_amount || 0),
      allocatedAmount: formatAmount(s.total_allocated || 0),
      pendingCount: byStatus.pending?.count || 0,
      plannedCount: byStatus.planned?.count || 0,
      totalCount: s.total_count || total.value,
    }
  }
  // 回退：服务端统计不可用时使用当前页数据
  const list = tableData.value
  const totalAmount = list.reduce((sum, f) => sum + (Number(f.amount) || 0), 0)
  const allocatedAmount = list
    .filter((f) => f.status === 'allocated' || f.status === 'completed' || f.status === 'audited')
    .reduce((sum, f) => sum + (Number(f.amount) || 0), 0)
  return {
    totalAmount: formatAmount(totalAmount),
    allocatedAmount: formatAmount(allocatedAmount),
    pendingCount: list.filter((f) => f.status === 'pending').length,
    plannedCount: list.filter((f) => f.status === 'planned').length,
    totalCount: total.value || list.length,
  }
})

async function loadStats() {
  try {
    const res = await get('/funds/statistics/overview')
    const d = res.data || res
    if (d) serverStats.value = d
  } catch {
    /* 统计加载失败不阻塞主流程 */
  }
}

function formatAmount(val: any) {
  const num = Number(val)
  if (isNaN(num)) return '0.00'
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

async function fetchData() {
  loading.value = true
  try {
    const response = await apiRequest({ method: 'GET', url: '/funds', params: {
        page: currentPage.value,
        page_size: pageSize.value,
        keyword: filterForm.keyword || undefined,
        fund_type: filterForm.type || undefined,
        status: filterForm.status || undefined,
      }})
    const resData = response.data
    tableData.value =
      resData?.items || resData?.data?.items || (Array.isArray(resData) ? resData : [])
    total.value = resData?.total || resData?.data?.total || tableData.value.length
  } catch (e) {
    logger.error('加载数据失败:', e)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchData()
}
function handleReset() {
  filterForm.keyword = ''
  filterForm.type = ''
  filterForm.status = ''
  currentPage.value = 1
  fetchData()
}
function filterByStatus(status: string) {
  filterForm.status = status
  currentPage.value = 1
  fetchData()
}
function handleSizeChange() {
  currentPage.value = 1
  fetchData()
}
function handlePageChange() {
  fetchData()
}
function handleCreate() {
  pushSafe('/funds/create')
}
function handleView(row: any) {
  pushSafe(`/funds/${row.id}`)
}
function handleEdit(row: any) {
  pushSafe(`/funds/${row.id}/edit`)
}
async function handleDelete(row: any) {
  if (deleting.value[row.id]) return
  deleting.value[row.id] = true
  try {
    await del(`/funds/${row.id}`)
    ElMessage.success('删除成功')
    // 立即从前端列表中移除，确保界面及时更新
    tableData.value = tableData.value.filter((item: any) => item.id !== row.id)
    total.value = Math.max(0, total.value - 1)
    currentPage.value = 1 // 重置到第1页，确保新建/编辑后的数据可见
    fetchData()
    loadStats()
  } catch (e: any) {
    const detail = e?.response?.data?.detail || e?.message || '删除失败'
    ElMessage.error(`删除失败: ${detail}`)
  } finally {
    delete deleting.value[row.id]
  }
}
async function handleDownloadTemplate() {
  try {
    await downloadImportTemplateAndSave('fund', '经费')
  } catch {
    ElMessage.error('模板下载失败，请重试')
  }
}

async function handleExport() {
  if (exporting.value) return
  exporting.value = true
  try {
    await fundApi.exportList({
      search: filterForm.keyword || undefined,
      type: filterForm.type || undefined,
      status: filterForm.status || undefined,
    })
    // 导出成功 — 浏览器已确认
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

async function quickApprove(row: any) {
  if (approving.value[row.id]) return
  approving.value[row.id] = true
  try {
    await fundApi.approve(row.id, {})
    ElMessage.success('审批成功')
    currentPage.value = 1 // 重置到第1页，确保新建/编辑后的数据可见
    fetchData()
    loadStats()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '审批失败')
  } finally {
    delete approving.value[row.id]
  }
}
async function quickAllocate(row: any) {
  if (allocating.value[row.id]) return
  allocating.value[row.id] = true
  try {
    await fundApi.allocate(row.id, {})
    ElMessage.success('拨付成功')
    currentPage.value = 1 // 重置到第1页，确保新建/编辑后的数据可见
    fetchData()
    loadStats()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '拨付失败')
  } finally {
    delete allocating.value[row.id]
  }
}

function getTypeName(type: string) {
  const m: Record<string, string> = {
    project: '项目经费',
    operation: '运营经费',
    education: '教育帮扶',
    infrastructure: '基础设施',
    emergency: '应急经费',
    other: '其他',
  }
  return m[type] || type || '-'
}
function getStatusType(status: string): 'success' | 'info' | 'warning' | 'danger' | 'primary' {
  const m: Record<string, 'success' | 'info' | 'warning' | 'danger' | 'primary'> = {
    pending: 'warning',
    planned: 'info',
    approved: 'primary',
    allocated: 'info',
    in_use: 'primary',
    completed: 'success',
    audited: 'success',
  }
  return m[status] || 'info'
}
function getStatusText(status: string) {
  const m: Record<string, string> = {
    pending: '待审批',
    planned: '已计划',
    approved: '已批准',
    allocated: '已拨付',
    in_use: '使用中',
    completed: '已完成',
    audited: '已审计',
  }
  return m[status] || status || '-'
}

// 批量操作
function handleSelectionChange(rows: any[]) {
  selectedRows.value = rows
}
function clearSelection() {
  tableRef.value?.clearSelection()
  selectedRows.value = []
}
async function handleBatchDelete() {
  if (!selectedRows.value.length || batchDeleting.value) return
  const count = selectedRows.value.length
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${count} 条经费记录吗？`, '批量删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  batchDeleting.value = true
  try {
    let deleted = 0
    let failed = 0
    const deletedIds: any[] = []
    for (const row of selectedRows.value) {
      try {
        await del(`/funds/${row.id}`)
        deleted++
        deletedIds.push(row.id)
      } catch {
        failed++
      }
    }
    // 立即从前端列表中移除已删除的记录
    tableData.value = tableData.value.filter((item: any) => !deletedIds.includes(item.id))
    total.value = Math.max(0, total.value - deleted)
    if (deleted > 0) ElMessage.success(`成功删除 ${deleted} 条记录`)
    if (failed > 0) ElMessage.warning(`${failed} 条记录删除失败`)
    clearSelection()
    currentPage.value = 1 // 重置到第1页，确保新建/编辑后的数据可见
    fetchData()
    loadStats()
  } finally {
    batchDeleting.value = false
  }
}
async function handleBatchExport() {
  if (exporting.value) return
  exporting.value = true
  try {
    await fundApi.exportList({})
    // 导出成功 — 浏览器已确认
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  fetchData()
  loadStats()
})
</script>

<style scoped>
.fund-list-page {
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

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-item {
  flex: 1;
  background: linear-gradient(135deg, rgba(27, 67, 50, 0.08) 0%, rgba(45, 106, 79, 0.05) 100%);
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
  font-size: 26px;
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
  color: #e6a23c;
}
.text-info {
  color: #409eff;
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

.amount-text {
  font-weight: 600;
  color: #1b4332;
}

.batch-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 6px;
  margin-bottom: 12px;
}

.batch-info {
  font-size: 13px;
  color: #409eff;
  font-weight: 500;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
