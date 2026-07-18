<template>
  <div class="organization-list-page">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">组织管理</span>
          <div class="header-actions">
            <el-input
              v-model="searchText"
              placeholder="搜索..."
              clearable
              style="width: 200px; margin-right: 10px"
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            />
            <el-button v-if="isAdmin" type="primary" @click="handleCreate">新增组织</el-button>
          </div>
        </div>
      </template>

      <div v-if="isAdmin && !searchText" class="drag-tip">
        <el-alert title="拖拽提示" type="info" :closable="false" show-icon>
          <template #default> 可以通过拖拽表格行来调整组织排序，松开鼠标后自动保存 </template>
        </el-alert>
      </div>

      <el-table ref="tableRef" v-loading="loading" :data="tableData" border stripe row-key="id">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="org_type" label="类型" width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.org_type === 'department'" type="primary">部门单位</el-tag>
            <el-tag v-else-if="scope.row.org_type === 'support_unit'" type="success"
              >帮扶单位</el-tag
            >
            <el-tag v-else>{{ scope.row.org_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column v-if="isAdmin" label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="组织名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入组织名称" />
        </el-form-item>
        <el-form-item label="上级组织" prop="parent_id">
          <el-select
            v-model="formData.parent_id"
            placeholder="选择上级组织"
            clearable
            filterable
            style="width: 100%"
          >
            <el-option label="无" :value="null as any" />
            <el-option
              v-for="org in parentOrgOptions"
              :key="org.id"
              :label="org.name"
              :value="org.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="组织类型" prop="org_type">
          <el-select v-model="formData.org_type" placeholder="选择组织类型" style="width: 100%">
            <el-option label="部门单位" value="department" />
            <el-option label="帮扶单位" value="support_unit" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入组织描述"
          />
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="formData.is_active" active-text="正常" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'

import { ref, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { post, put, del, apiRequest } from '@/api/request'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import Sortable from 'sortablejs'
import { batchUpdateSortOrders } from '@/api/organization'

// 获取认证状态
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdmin)

const tableRef = ref()
const tableData = ref<any[]>([])
const loading = ref(false)
const searchText = ref('')
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
let sortableInstance: Sortable | null = null

// 对话框相关
const dialogVisible = ref(false)
const dialogTitle = computed(() => (formData.value.id ? '编辑组织' : '新增组织'))
const submitting = ref(false)
const formRef = ref<FormInstance>()
const formData = ref({
  id: null as number | null,
  name: '',
  parent_id: null as number | null,
  org_type: 'department',
  description: '',
  is_active: true,
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入组织名称', trigger: 'blur' }],
  org_type: [{ required: true, message: '请选择组织类型', trigger: 'change' }],
}

// 收集某组织及其所有后代的 id（当前页内），用于父级选项过滤
function collectDescendantIds(rootId: number, orgs: any[]): Set<number> {
  const ids = new Set<number>([rootId])
  let changed = true
  while (changed) {
    changed = false
    for (const org of orgs) {
      if (!ids.has(org.id) && org.parent_id !== null && ids.has(org.parent_id)) {
        ids.add(org.id)
        changed = true
      }
    }
  }
  return ids
}

// 上级组织选项（排除当前编辑的组织及其所有后代，防止形成循环层级）
const parentOrgOptions = computed(() => {
  if (!formData.value.id) return tableData.value
  const excluded = collectDescendantIds(formData.value.id, tableData.value)
  return tableData.value.filter((org) => !excluded.has(org.id))
})

async function fetchData() {
  loading.value = true
  try {
    const response = await apiRequest({
      method: 'GET',
      url: '/organizations',
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        search: searchText.value || undefined,
        is_active: true, // 只显示活跃的组织，过滤掉已删除的
      },
    })
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
  fetchDataWithSort()
}
function handlePageChange(page: number) {
  currentPage.value = page
  fetchDataWithSort()
}

function handleCreate() {
  formData.value = {
    id: null,
    name: '',
    parent_id: null,
    org_type: 'department',
    description: '',
    is_active: true,
  }
  dialogVisible.value = true
}

function handleEdit(row: any) {
  formData.value = {
    id: row.id,
    name: row.name || '',
    parent_id: row.parent_id || null,
    org_type: row.org_type || row.type || 'department',
    description: row.description || '',
    is_active: row.is_active !== false,
  }
  dialogVisible.value = true
}

function handleDialogClose() {
  formRef.value?.resetFields()
}

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const payload: Record<string, any> = { ...formData.value }
    delete payload.id

    if (formData.value.id) {
      // 编辑
      await put(`/organizations/${formData.value.id}`, payload)
      ElMessage.success('已保存')
    } else {
      // 新增
      await post('/organizations', payload)
      ElMessage.success('已创建')
    }

    dialogVisible.value = false
    currentPage.value = 1
    fetchDataWithSort()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      `确认删除组织"${row.name}"？\n\n` +
        '删除后该组织将被停用，不再显示在系统中。\n' +
        '如有子组织，请先删除子组织。',
      '删除组织',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      }
    )

    // 执行物理删除
    const response = await del(`/organizations/${row.id}`)

    // 显示后端返回的消息
    ElMessage.success(response.data?.message || '组织已删除')

    // 刷新列表（重置到第1页，确保删除后数据可见）
    currentPage.value = 1
    await fetchDataWithSort()
  } catch (err: any) {
    if (err !== 'cancel' && err?.toString() !== 'cancel') {
      const detail = err?.response?.data?.detail || err?.message || '删除失败'
      ElMessage.error(detail)
    }
  }
}

// 初始化拖拽排序
function initSortable() {
  // 销毁旧实例
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }

  // 只在管理员模式且无搜索条件时启用拖拽
  if (!isAdmin.value || searchText.value) {
    return
  }

  nextTick(() => {
    const tbody = tableRef.value?.$el.querySelector('.el-table__body-wrapper tbody')
    if (!tbody) return

    sortableInstance = Sortable.create(tbody, {
      animation: 150,
      handle: 'tr',
      onEnd: async (evt: any) => {
        const { oldIndex, newIndex } = evt
        if (oldIndex === newIndex) return

        // 更新本地数据
        const movedItem = tableData.value.splice(oldIndex, 1)[0]
        tableData.value.splice(newIndex, 0, movedItem)

        // 重新计算排序号
        const sortItems = tableData.value.map((item, index) => ({
          id: item.id,
          sort_order: index + 1,
        }))

        try {
          // 调用批量更新 API
          await batchUpdateSortOrders(sortItems)
          ElMessage.success('排序已保存')
          // 本地状态已更新，无需重新获取数据
        } catch (error: any) {
          logger.error('保存排序失败', error)
          ElMessage.error(error.response?.data?.detail || '保存排序失败')

          // 恢复原始顺序
          await fetchData()
        }
      },
    })
  })
}

// 修改 fetchData，在数据加载后初始化拖拽
async function fetchDataWithSort() {
  await fetchData()
  initSortable()
}

onMounted(() => fetchDataWithSort())
</script>

<style scoped>
.organization-list-page {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-title {
  font-size: 16px;
  font-weight: bold;
}
.header-actions {
  display: flex;
  align-items: center;
}
.drag-tip {
  margin-bottom: 16px;
}
/* 拖拽时的样式 */
:deep(.sortable-ghost) {
  opacity: 0.4;
  background: var(--color-primary-light-8);
}
:deep(.el-table__body-wrapper tbody tr) {
  cursor: move;
}
</style>
