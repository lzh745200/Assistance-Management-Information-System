<template>
  <div class="import-section">
    <el-row :gutter="20">
      <!-- 左侧：上传区域 -->
      <el-col :span="14">
        <el-card class="upload-card">
          <template #header>
            <div class="card-header">
              <span>上传文件</span>
              <el-button type="primary" link @click="handleDownloadTemplate">
                <el-icon><Download /></el-icon>
                下载导入模板
              </el-button>
            </div>
          </template>

          <el-upload
            ref="uploadRef"
            class="upload-area"
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            accept=".xlsx,.xls"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">仅支持 .xlsx 或 .xls 格式，单次最多导入1000条记录</div>
            </template>
          </el-upload>

          <!-- 导入模式选择 -->
          <div v-if="selectedFile" class="import-options">
            <el-divider />
            <el-form label-width="100px">
              <el-form-item label="导入模式">
                <el-radio-group v-model="importMode">
                  <el-radio value="incremental">增量导入</el-radio>
                  <el-radio value="full">全量覆盖</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="importing" @click="handleImport">
                  开始导入
                </el-button>
                <el-button @click="handleClear">清除文件</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：导入历史 -->
      <el-col :span="10">
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <span>导入历史</span>
              <el-button link @click="loadHistory">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>

          <el-table v-loading="loadingHistory" :data="historyList" max-height="400">
            <el-table-column
              prop="file_name"
              label="文件名"
              min-width="120"
              show-overflow-tooltip
            />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ formatImportStatus(row.status).text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="结果" width="100">
              <template #default="{ row }">
                <span v-if="row.success_rows !== undefined">
                  {{ row.success_rows }}/{{ row.total_rows }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="100">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 导入结果对话框 -->
    <el-dialog v-model="showResultDialog" title="导入结果" width="600px">
      <div v-if="importResult" class="import-result">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="总行数">{{ importResult.total_rows }}</el-descriptions-item>
          <el-descriptions-item label="成功">
            <el-tag type="success">{{ importResult.success_rows }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="失败">
            <el-tag type="danger">{{ importResult.failed_rows }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="跳过">
            <el-tag type="info">{{ importResult.skipped_rows }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="importResult.errors && importResult.errors.length > 0" class="error-list">
          <el-divider content-position="left">错误详情</el-divider>
          <el-table :data="importResult.errors" max-height="300">
            <el-table-column prop="row_number" label="行号" width="80" />
            <el-table-column prop="field_name" label="字段" width="100" />
            <el-table-column prop="message" label="错误信息" />
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="showResultDialog = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'

import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, UploadFilled, Refresh } from '@element-plus/icons-vue'
import type { UploadInstance, UploadFile, UploadRawFile } from 'element-plus'
import {
  downloadImportTemplate,
  importVillages,
  getImportHistory,
  formatImportStatus,
  type ImportResult,
  type ImportHistory,
  type ImportMode,
} from '@/api/import'

const emit = defineEmits<{
  (e: 'import-complete'): void
}>()

// 状态
const uploadRef = ref<UploadInstance>()
const selectedFile = ref<File | null>(null)
const importMode = ref<ImportMode>('incremental')
const importing = ref(false)
const loadingHistory = ref(false)
const historyList = ref<ImportHistory[]>([])
const showResultDialog = ref(false)
const importResult = ref<ImportResult | null>(null)

// 加载导入历史
async function loadHistory() {
  loadingHistory.value = true
  try {
    const res = await getImportHistory(1, 10)
    historyList.value = (res as any)?.data?.items || (res as any)?.items
  } catch (error) {
    logger.error('加载导入历史失败:', error)
  } finally {
    loadingHistory.value = false
  }
}

// 下载模板
async function handleDownloadTemplate() {
  try {
    const blob = await downloadImportTemplate('supported_village')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '帮扶村导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    // 模板下载成功 — 浏览器已确认
  } catch (error) {
    ElMessage.error('模板下载失败')
  }
}

// 文件选择
function handleFileChange(file: UploadFile) {
  selectedFile.value = file.raw as File
}

// 超出限制
function handleExceed(files: File[]) {
  uploadRef.value?.clearFiles()
  const file = files[0] as UploadRawFile
  uploadRef.value?.handleStart(file)
}

// 清除文件
function handleClear() {
  uploadRef.value?.clearFiles()
  selectedFile.value = null
}

// 执行导入
async function handleImport() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  importing.value = true
  try {
    const result = await importVillages(selectedFile.value, importMode.value)
    importResult.value = result
    showResultDialog.value = true

    if (result.success) {
      ElMessage.success(`导入成功：${result.success_rows}条记录`)
      emit('import-complete')
    } else {
      ElMessage.warning(`导入完成，但有${result.failed_rows}条失败`)
    }

    handleClear()
    loadHistory()
  } catch (error) {
    ElMessage.error('导入失败，请检查文件格式')
  } finally {
    importing.value = false
  }
}

// 获取状态类型
function getStatusType(status: string): 'success' | 'info' | 'warning' | 'danger' | 'primary' {
  const typeMap: Record<string, 'success' | 'info' | 'warning' | 'danger' | 'primary'> = {
    completed: 'success',
    failed: 'danger',
    processing: 'warning',
    pending: 'info',
  }
  return typeMap[status] || 'info'
}

// 格式化时间
function formatTime(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped lang="scss">
.import-section {
  .upload-card,
  .history-card {
    height: 100%;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .upload-area {
    :deep(.el-upload-dragger) {
      padding: 40px 20px;
    }
  }

  .import-options {
    margin-top: 20px;
  }

  .import-result {
    .error-list {
      margin-top: 20px;
    }
  }
}
</style>
