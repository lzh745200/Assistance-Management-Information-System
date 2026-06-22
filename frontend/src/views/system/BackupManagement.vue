<template>
  <div class="backup-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">系统备份管理</span>
          <div class="header-actions">
            <el-button :loading="loading" @click="refreshAll">刷新</el-button>
            <el-button type="primary" @click="handleCreateBackup"> 创建备份 </el-button>
          </div>
        </div>
      </template>

      <!-- 备份统计 -->
      <el-descriptions :column="3" border class="backup-status">
        <el-descriptions-item label="备份数量">
          {{ backupStats.totalBackups ?? 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="总大小">
          {{ formatSize(backupStats.totalSize ?? 0) }}
        </el-descriptions-item>
        <el-descriptions-item label="最近备份">
          {{ formatTime(backupStats.lastBackup) }}
        </el-descriptions-item>
        <el-descriptions-item label="完整备份">
          {{ backupStats.fullBackups ?? 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="增量备份">
          {{ backupStats.incrementalBackups ?? 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="自动备份">
          <el-tag :type="backupStats.scheduleEnabled ? 'success' : 'info'">
            {{ backupStats.scheduleEnabled ? '已启用' : '未启用' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 备份列表 -->
      <el-table v-loading="loading" :data="backupList" style="width: 100%; margin-top: 20px">
        <el-table-column prop="file_name" label="文件名" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="150" />
        <el-table-column prop="backup_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.backup_type === 'incremental' ? 'warning' : 'primary'">
              {{ row.backup_type === 'incremental' ? '增量' : '完整' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="100">
          <template #default="{ row }">
            {{ formatSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleDownload(row)"> 下载 </el-button>
            <el-button size="small" type="warning" @click="handleRestore(row)"> 恢复 </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)"> 删除 </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !backupList.length" description="暂无备份记录" />
    </el-card>

    <!-- 创建备份对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建备份" width="500px">
      <el-form :model="backupForm" label-width="120px">
        <el-form-item label="备份描述">
          <el-input v-model="backupForm.description" placeholder="请输入备份描述" />
        </el-form-item>
        <el-form-item label="包含上传文件">
          <el-switch v-model="backupForm.include_uploads" />
        </el-form-item>
        <el-form-item label="加密密码">
          <el-input
            v-model="backupForm.password"
            type="password"
            placeholder="留空则不加密"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="confirmCreateBackup">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 恢复备份确认对话框 -->
    <el-dialog v-model="restoreDialogVisible" title="恢复备份" width="500px">
      <el-alert title="警告：恢复备份将覆盖当前所有数据！" type="error" :closable="false" />
      <div style="margin-top: 16px">
        <p><strong>备份文件：</strong>{{ restoreTarget?.file_name }}</p>
        <p><strong>创建时间：</strong>{{ formatTime(restoreTarget?.created_at) }}</p>
        <p><strong>大小：</strong>{{ formatSize(restoreTarget?.file_size ?? 0) }}</p>
      </div>
      <el-form
        v-if="restoreTarget?.is_encrypted"
        :model="restoreForm"
        label-width="120px"
        style="margin-top: 16px"
      >
        <el-form-item label="解密密码" required>
          <el-input
            v-model="restoreForm.password"
            type="password"
            placeholder="请输入加密密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="restoreDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="restoring" @click="confirmRestore"> 确认恢复 </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const loading = ref(false)
const creating = ref(false)
const restoring = ref(false)
const backupList = ref<any[]>([])
const backupStats = ref<Record<string, any>>({
  totalBackups: 0,
  totalSize: 0,
  lastBackup: null,
  fullBackups: 0,
  incrementalBackups: 0,
  scheduleEnabled: false,
})

const createDialogVisible = ref(false)
const restoreDialogVisible = ref(false)
const restoreTarget = ref<any>(null)
const backupForm = ref({
  description: '手动备份',
  include_uploads: true,
  password: '',
})
const restoreForm = ref({ password: '' })

async function fetchBackupList() {
  try {
    const res = await request.get('/system/backup')
    const resData = res.data
    backupList.value = resData?.data?.items ?? resData?.items ?? []
  } catch {
    ElMessage.error('获取备份列表失败')
  }
}

async function fetchBackupStats() {
  try {
    const res = await request.get('/system/backup/stats')
    const resData = res.data?.data ?? res.data
    backupStats.value = {
      totalBackups: resData?.totalBackups ?? 0,
      totalSize: resData?.totalSize ?? 0,
      lastBackup: resData?.lastBackup ?? null,
      fullBackups: resData?.fullBackups ?? 0,
      incrementalBackups: resData?.incrementalBackups ?? 0,
      scheduleEnabled: resData?.scheduleEnabled ?? false,
    }
  } catch {
    // 静默处理
  }
}

async function refreshAll() {
  loading.value = true
  try {
    await Promise.all([fetchBackupList(), fetchBackupStats()])
  } finally {
    loading.value = false
  }
}

function handleCreateBackup() {
  backupForm.value = {
    description: '手动备份',
    include_uploads: true,
    password: '',
  }
  createDialogVisible.value = true
}

async function confirmCreateBackup() {
  creating.value = true
  try {
    const res = await request.post('/system/backup', {
      description: backupForm.value.description,
      include_uploads: backupForm.value.include_uploads,
      password: backupForm.value.password || null,
    })
    if (res.data?.success !== false) {
      ElMessage.success('已创建')
      createDialogVisible.value = false
      await refreshAll()
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建备份失败')
  } finally {
    creating.value = false
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定要删除备份 "${row.file_name}" 吗？`, '警告', {
      type: 'warning',
    })
    const res = await request.delete(`/system/backup/${row.file_name}`)
    if (res.data?.success !== false) {
      ElMessage.success('已删除')
      await refreshAll()
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function handleRestore(row: any) {
  restoreTarget.value = row
  restoreForm.value.password = ''
  restoreDialogVisible.value = true
}

async function confirmRestore() {
  if (!restoreTarget.value) return
  restoring.value = true
  try {
    const res = await request.post('/system/backup/restore', {
      filename: restoreTarget.value.file_name,
      password: restoreForm.value.password || null,
    })
    if (res.data?.success !== false) {
      ElMessage.success('系统恢复成功，请重新登录')
      restoreDialogVisible.value = false
      setTimeout(() => {
        window.location.href = '/login'
      }, 2000)
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '恢复失败')
  } finally {
    restoring.value = false
  }
}

function handleDownload(row: any) {
  // 通过隐藏的 iframe 或链接下载
  const link = document.createElement('a')
  link.href = `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/system/backup/download/${encodeURIComponent(row.file_name)}`
  link.download = row.file_name
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function formatSize(bytes: number) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

function formatTime(time: string | number | Date | null) {
  if (!time) return '-'
  try {
    return new Date(time).toLocaleString('zh-CN')
  } catch {
    return '-'
  }
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.backup-management {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title {
  font-size: 16px;
  font-weight: 600;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.backup-status {
  margin-bottom: 20px;
}
</style>
