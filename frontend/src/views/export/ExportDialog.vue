<template>
  <el-dialog
    v-model="visible"
    title="数据导出"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <!-- 筛选条件 -->
    <el-form :model="filterForm" label-width="100px" class="filter-form">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="部门">
            <el-input v-model="filterForm.department" placeholder="请输入部门" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="帮扶单位">
            <el-input v-model="filterForm.support_unit" placeholder="请输入帮扶单位" clearable />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="村庄名称">
            <el-input v-model="filterForm.village_name" placeholder="请输入村庄名称" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="地区范围">
            <el-input v-model="filterForm.region_scope" placeholder="请输入地区范围" clearable />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="三区三州">
            <el-select v-model="filterForm.is_three_regions" placeholder="请选择" clearable>
              <el-option label="是" :value="1" />
              <el-option label="否" :value="0" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="边疆地区">
            <el-select v-model="filterForm.is_border_area" placeholder="请选择" clearable>
              <el-option label="是" :value="1" />
              <el-option label="否" :value="0" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="振兴梯队">
            <el-switch
              v-model="filterForm.is_revitalization_tier"
              active-text="是"
              inactive-text="全部"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="强制异步">
            <el-switch v-model="forceAsync" />
            <el-tooltip content="数据量大于5000条时自动使用异步导出" placement="top">
              <el-icon class="help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <!-- 导出状态 -->
    <div v-if="exportTask" class="export-status">
      <el-divider />
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="任务ID">{{ exportTask.task_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="formatExportStatus(exportTask.status).type" size="small">
            {{ formatExportStatus(exportTask.status).text }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="记录数">{{ exportTask.record_count }}</el-descriptions-item>
        <el-descriptions-item label="文件大小">
          {{ exportTask.file_size ? formatFileSize(exportTask.file_size) : '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 进度条 -->
      <el-progress
        v-if="exportTask.status === 'processing'"
        :percentage="50"
        :indeterminate="true"
        class="progress-bar"
      />

      <!-- 下载按钮 -->
      <div v-if="exportTask.is_downloadable" class="download-action">
        <el-button type="primary" :loading="downloading" @click="handleDownload">
          <el-icon><Download /></el-icon>
          下载文件
        </el-button>
      </div>

      <!-- 错误信息 -->
      <el-alert
        v-if="exportTask.status === 'failed'"
        :title="exportTask.error_message || '导出失败'"
        type="error"
        show-icon
        class="error-alert"
      />
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button @click="handleReset">重置</el-button>
      <el-button
        type="primary"
        :loading="exporting"
        :disabled="!!exportTask && exportTask.status === 'processing'"
        @click="handleExport"
      >
        <el-icon><Upload /></el-icon>
        开始导出
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Upload, QuestionFilled } from '@element-plus/icons-vue'
import {
  exportVillages,
  getExportStatus,
  downloadExportFile,
  formatExportStatus,
  formatFileSize,
  triggerDownload,
  type ExportFilterParams,
  type ExportTask,
} from '@/api/export'

// ==================== Props & Emits ====================

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

// ==================== 状态 ====================

const visible = ref(props.modelValue)
const exporting = ref(false)
const downloading = ref(false)
const forceAsync = ref(false)
const exportTask = ref<ExportTask | null>(null)
let pollTimer: number | null = null

const filterForm = ref<ExportFilterParams>({
  department: undefined,
  support_unit: undefined,
  village_name: undefined,
  region_scope: undefined,
  is_three_regions: undefined,
  is_border_area: undefined,
  is_revitalization_tier: undefined,
})

// ==================== 监听 ====================

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
  }
)

watch(visible, (val) => {
  emit('update:modelValue', val)
  if (!val) {
    stopPolling()
  }
})

// ==================== 方法 ====================

/**
 * 开始导出
 */
async function handleExport() {
  exporting.value = true
  exportTask.value = null

  try {
    // 清理空值
    const filters: ExportFilterParams = {}
    Object.entries(filterForm.value).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        const converted =
          key === 'is_three_regions' || key === 'is_border_area' || key === 'is_revitalization_tier'
            ? (value as number | boolean | string) === 1 || value === true
              ? true
              : (value as number | boolean | string) === 0 || value === false
                ? false
                : undefined
            : value
        ;(filters as any)[key] = converted
      }
    })

    const result = await exportVillages(filters, forceAsync.value)

    // 如果是Blob，直接下载
    if (result instanceof Blob) {
      const filename = `帮扶村数据_${new Date().toISOString().slice(0, 10)}.xlsx`
      triggerDownload(result, filename)
      // 导出成功 — 浏览器已确认
      handleClose()
      return
    }

    // 异步导出
    if (result.mode === 'async' && result.task_id) {
      ElMessage.info('导出任务已创建，正在处理中...')
      // 开始轮询状态
      startPolling(result.task_id)
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '导出失败')
  } finally {
    exporting.value = false
  }
}

/**
 * 开始轮询导出状态
 */
function startPolling(taskId: string) {
  stopPolling()

  const poll = async () => {
    try {
      const task = await getExportStatus(taskId)
      exportTask.value = task

      if (task.status === 'completed' || task.status === 'failed' || task.status === 'expired') {
        stopPolling()
        if (task.status === 'completed') {
          ElMessage.success('导出完成，可以下载文件了')
        }
      }
    } catch (error) {
      stopPolling()
    }
  }

  // 立即执行一次
  poll()
  // 每3秒轮询一次
  pollTimer = window.setInterval(poll, 3000)
}

/**
 * 停止轮询
 */
function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

/**
 * 下载文件
 */
async function handleDownload() {
  if (!exportTask.value?.task_id) return

  downloading.value = true
  try {
    const blob = await downloadExportFile(exportTask.value.task_id)
    const filename =
      exportTask.value.file_name || `帮扶村数据_${new Date().toISOString().slice(0, 10)}.xlsx`
    triggerDownload(blob, filename)
    ElMessage.success('下载成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '下载失败')
  } finally {
    downloading.value = false
  }
}

/**
 * 重置表单
 */
function handleReset() {
  filterForm.value = {
    department: undefined,
    support_unit: undefined,
    village_name: undefined,
    region_scope: undefined,
    is_three_regions: undefined,
    is_border_area: undefined,
    is_revitalization_tier: undefined,
  }
  forceAsync.value = false
  exportTask.value = null
}

/**
 * 关闭对话框
 */
function handleClose() {
  visible.value = false
  stopPolling()
}
</script>

<style scoped lang="scss">
.filter-form {
  .help-icon {
    margin-left: 8px;
    color: #909399;
    cursor: help;
  }
}

.export-status {
  margin-top: 20px;

  .progress-bar {
    margin-top: 16px;
  }

  .download-action {
    margin-top: 16px;
    text-align: center;
  }

  .error-alert {
    margin-top: 16px;
  }
}
</style>
