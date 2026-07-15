<template>
  <div class="logs-page">
    <div class="page-header">
      <h2 class="page-title">操作日志</h2>
      <p class="page-desc">
        记录所有数据变更操作的日志，包括导入、导出、修改、删除和备份等，支持备注编辑和导出
      </p>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="操作类型">
          <el-select v-model="filters.type" placeholder="全部" clearable style="width: 140px">
            <el-option label="创建" value="create" />
            <el-option label="更新" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="导入" value="import" />
            <el-option label="导出" value="export" />
            <el-option label="备份" value="backup" />
            <el-option label="恢复" value="restore" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据操作日志 (共 {{ total }} 条)</span>
          <div class="header-actions">
            <el-button
              v-if="isAdmin"
              type="danger"
              size="small"
              :loading="clearing"
              @click="handleClearLogs"
              >清除所有日志</el-button
            >
            <el-button type="success" size="small" :loading="exporting" @click="handleExport"
              >导出日志</el-button
            >
          </div>
        </div>
      </template>
      <el-table v-loading="loading" :data="logs" stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="time" label="时间" width="170" />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="typeTagMap[row.type] || 'info'" size="small">{{
              typeNameMap[row.type] || row.type
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="detail" label="操作详情" min-width="160" show-overflow-tooltip />
        <el-table-column label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">{{
              row.success ? '成功' : '失败'
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="130" />
        <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="openRemarkDialog(row)"
              >编辑备注</el-button
            >
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 备注编辑对话框 -->
    <el-dialog v-model="remarkDialogVisible" title="编辑日志备注" width="500px">
      <el-input
        v-model="remarkForm.remark"
        type="textarea"
        :rows="4"
        placeholder="请输入备注信息"
      />
      <template #footer>
        <el-button @click="remarkDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="remarkSaving" @click="saveRemark">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'

import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { auditApi } from '@/api/audit'
import { get, patch, apiRequest } from '@/api/request'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isAdmin = computed(() => ['admin', 'super_admin'].includes(authStore.user?.role || ''))

const loading = ref(false)
const exporting = ref(false)
const clearing = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)

// 数据操作类型，排除登录、权限等系统审计日志
const DATA_OPERATION_TYPES = ['create', 'update', 'delete', 'import', 'export', 'backup', 'restore']
const filters = reactive({ type: '', dateRange: null as string[] | null })

const typeTagMap: Record<string, 'success' | 'info' | 'warning' | 'danger' | 'primary'> = {
  create: 'success',
  update: 'primary',
  delete: 'danger',
  import: 'primary',
  export: 'success',
  backup: 'warning',
  login: 'success',
  restore: 'warning',
  read: 'info',
}
const typeNameMap: Record<string, string> = {
  create: '创建',
  update: '修改',
  delete: '删除',
  import: '导入',
  export: '导出',
  backup: '备份',
  login: '登录',
  restore: '恢复',
  read: '查看',
}

const logs = ref<any[]>([])

// 备注编辑
const remarkDialogVisible = ref(false)
const remarkSaving = ref(false)
const remarkForm = reactive({ id: 0, remark: '' })
let currentEditRow: any = null

async function loadLogs() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize,
    }

    // 如果用户筛选了类型，使用用户筛选的类型；否则默认只显示数据操作类型
    if (filters.type) {
      params.action = filters.type
    } else {
      // 默认只显示数据操作日志，过滤掉登录、权限等系统审计日志
      params.action_filter = DATA_OPERATION_TYPES.join(',')
    }

    if (filters.dateRange?.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    const data = await auditApi.getLogs(params)

    // 再次过滤确保只显示数据操作日志
    const allItems = data.items || []
    const filteredItems = filters.type
      ? allItems
      : allItems.filter((item: any) => DATA_OPERATION_TYPES.includes(item.action))

    logs.value = filteredItems.map((item: any) => ({
      id: item.id,
      time: item.created_at || '',
      operator: item.username || `用户${item.user_id || ''}`,
      type: item.action || '',
      module: item.resource_type || '',
      detail: item.detail || '',
      success: item.status !== 'failed',
      ip: item.ip_address || item.user_ip || '',
      remark: (item.metadata || {}).remark || '',
    }))
    total.value = filteredItems.length
  } catch {
    logs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadLogs()
}
function handleReset() {
  Object.assign(filters, { type: '', dateRange: null })
  handleSearch()
}
function handlePageChange(p: number) {
  page.value = p
  loadLogs()
}

function openRemarkDialog(row: any) {
  currentEditRow = row
  remarkForm.id = row.id
  remarkForm.remark = row.remark || ''
  remarkDialogVisible.value = true
}

async function saveRemark() {
  remarkSaving.value = true
  try {
    await patch(`/system/audit/logs/${remarkForm.id}/remark`, {
      remark: remarkForm.remark,
    })
    if (currentEditRow) currentEditRow.remark = remarkForm.remark
    ElMessage.success('备注保存成功')
    remarkDialogVisible.value = false
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.message || '备注保存失败'
    ElMessage.error(errorMsg)
  } finally {
    remarkSaving.value = false
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const params: Record<string, any> = {}
    if (filters.type) {
      params.action = filters.type
    } else {
      params.action_filter = DATA_OPERATION_TYPES.join(',')
    }
    if (filters.dateRange?.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    const res = await get('/system/audit/logs/export', { params })
    const data = res.data
    // 生成CSV并下载
    let csv = '\uFEFFID,时间,用户,操作类型,资源类型,状态,IP,备注\n'
    for (const item of data.items || []) {
      csv += `${item.id},"${item.time}","${item.user}","${item.action}","${item.resource_type}","${item.status}","${item.ip}","${item.detail}"\n`
    }
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `数据操作日志_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('日志导出成功')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

async function handleClearLogs() {
  try {
    await ElMessageBox.confirm('此操作将清除所有数据操作日志记录，是否继续？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    clearing.value = true
    try {
      // 注意：使用 actions（数组），与后端 BatchDeleteRequest.actions 字段对应
      const res = await apiRequest({ method: 'DELETE', url: '/system/audit/logs/batch', data: { actions: DATA_OPERATION_TYPES } })
      const count = res?.data?.deleted_count ?? 0
      ElMessage.success(`日志清除成功，共删除 ${count} 条记录`)
      await loadLogs()
    } catch (err: any) {
      // 提取后端返回的具体错误信息
      const detail = err?.response?.data?.detail
      const errMsg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join('；')
            : '日志清除失败，请稍后重试'
      logger.error('[handleClearLogs] 清除日志失败:', errMsg, err)
      ElMessage.error(errMsg)
    } finally {
      clearing.value = false
    }
  } catch {
    // 用户取消，静默处理
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.logs-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-actions {
  display: flex;
  gap: 8px;
}
</style>
