<template>
  <div class="user-backup-page">
    <div class="page-header">
      <h2 class="page-title">数据备份</h2>
      <p class="page-desc">创建系统数据备份，保障数据安全</p>
    </div>

    <!-- 操作区 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>快速备份</span>
          <el-button type="primary" :loading="creating" @click="handleCreateBackup">
            <el-icon><Plus /></el-icon>
            创建备份
          </el-button>
        </div>
      </template>
      <el-alert
        title="备份说明"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        备份将包含所有系统数据（帮扶村、项目、学校、经费等），可用于数据恢复。如需恢复备份或删除备份，请联系系统管理员。
      </el-alert>

      <!-- 备份列表 -->
      <el-table v-loading="loading" :data="backups" stripe>
        <el-table-column prop="filename" label="备份文件" min-width="200" show-overflow-tooltip />
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ formatSize(row.size_bytes || row.size) }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip />
        <el-table-column label="压缩" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.compressed ? 'success' : 'info'" size="small">{{
              row.compressed ? '是' : '否'
            }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建备份对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建备份" width="480px">
      <el-form label-width="90px">
        <el-form-item label="备份描述">
          <el-input v-model="createForm.description" placeholder="例如：日常备份" />
        </el-form-item>
        <el-form-item label="加密密码">
          <el-input
            v-model="createForm.password"
            type="password"
            placeholder="留空则不加密"
            show-password
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px">
            设置密码后备份文件将使用 AES-256 加密存储
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="confirmCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getBackupList, createBackup } from '@/api/backup'
import { formatFileSize } from '@/api/export'
import { format } from '@/utils'

const loading = ref(false)
const creating = ref(false)
const backups = ref<any[]>([])
const showCreateDialog = ref(false)
const createForm = reactive({ description: '', password: '' })

const formatSize = (bytes: number) => formatFileSize(bytes || 0)
const formatTime = (iso: string) => (iso ? format.formatDateTime(iso) : '-')

async function loadBackups() {
  loading.value = true
  try {
    const res = await getBackupList()
    // 后端返回 snake_case（file_name/backup_id），映射为组件使用的 filename/id
    backups.value = (res.items || []).map((it: any) => ({
      ...it,
      filename: it.filename ?? it.file_name,
      id: it.id ?? it.backup_id,
    }))
  } catch {
    backups.value = []
  } finally {
    loading.value = false
  }
}

function handleCreateBackup() {
  Object.assign(createForm, { description: '', password: '' })
  showCreateDialog.value = true
}

async function confirmCreate() {
  creating.value = true
  showCreateDialog.value = false
  try {
    const res = await createBackup({
      description: createForm.description || '用户手动备份',
      include_uploads: true,
      password: createForm.password || undefined,
    })
    if (res.success !== false) {
      ElMessage.success('备份创建成功')
      loadBackups()
    } else {
      ElMessage.error(res.message || '备份创建失败')
    }
  } catch {
    ElMessage.error('备份创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(loadBackups)
</script>

<style scoped>
.user-backup-page {
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
</style>
