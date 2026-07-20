<template>
  <div class="task-package-admin">
    <div class="page-header">
      <h2 class="page-title">任务数据包管理</h2>
      <p class="page-desc">生成标准化任务数据包模板、分发给用户，导入用户上报的数据包</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 生成任务包 -->
      <el-tab-pane label="生成任务包" name="create">
        <el-form :model="createForm" label-width="120px" style="max-width: 650px; padding: 20px">
          <el-form-item label="任务名称" required>
            <el-input v-model="createForm.name" placeholder="如：2025年度帮扶数据采集任务" />
          </el-form-item>
          <el-form-item label="数据年度">
            <el-date-picker
              v-model="createForm.year"
              type="year"
              placeholder="选择年度"
              value-format="YYYY"
            />
          </el-form-item>
          <el-form-item label="数据类型">
            <el-checkbox-group v-model="createForm.dataTypes">
              <el-checkbox :value="DATA_TYPES.VILLAGES">{{
                DATA_TYPE_LABELS[DATA_TYPES.VILLAGES]
              }}</el-checkbox>
              <el-checkbox :value="DATA_TYPES.PROJECTS">{{
                DATA_TYPE_LABELS[DATA_TYPES.PROJECTS]
              }}</el-checkbox>
              <el-checkbox :value="DATA_TYPES.FUNDS">经费数据</el-checkbox>
              <el-checkbox :value="DATA_TYPES.SCHOOLS">{{
                DATA_TYPE_LABELS[DATA_TYPES.SCHOOLS]
              }}</el-checkbox>
              <el-checkbox value="rural_works">乡村工作</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item label="任务说明">
            <el-input
              v-model="createForm.description"
              type="textarea"
              :rows="3"
              placeholder="请填写任务要求和说明"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" @click="createTaskPackage"
              >生成任务包模板</el-button
            >
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 导入上报包 -->
      <el-tab-pane label="导入上报包" name="import">
        <div style="max-width: 650px; padding: 20px">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".zip"
            :on-change="handleFileChange"
            drag
          >
            <el-icon style="font-size: 40px; color: #909399"><UploadFilled /></el-icon>
            <div style="margin-top: 8px">将上报数据包拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div style="color: #909399; font-size: 12px; margin-top: 8px">
                仅支持 ZIP 格式的数据包文件
              </div>
            </template>
          </el-upload>

          <div v-if="importPreview" style="margin-top: 20px">
            <el-descriptions title="数据包预览" :column="2" border size="small">
              <el-descriptions-item label="文件名">{{
                importPreview.fileName
              }}</el-descriptions-item>
              <el-descriptions-item label="上报单位">{{
                importPreview.orgName || '未知'
              }}</el-descriptions-item>
              <el-descriptions-item
                v-for="(count, key) in importPreview.counts"
                :key="key"
                :label="typeLabels[key] || key"
              >
                {{ count }} 条记录
              </el-descriptions-item>
            </el-descriptions>
            <div style="margin-top: 16px; display: flex; gap: 12px">
              <el-button type="primary" :loading="importing" @click="confirmImport"
                >确认导入</el-button
              >
              <el-button @click="clearImport">取消</el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 数据包列表 -->
      <el-tab-pane label="历史记录" name="list">
        <div style="padding: 12px 0">
          <el-radio-group
            v-model="listFilter"
            size="small"
            style="margin-bottom: 16px"
            @change="loadPackageList"
          >
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button label="task">任务包</el-radio-button>
            <el-radio-button label="report">上报包</el-radio-button>
          </el-radio-group>

          <el-table v-loading="loadingList" :data="packageList" border stripe>
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="name" label="名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="type" label="类型" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.type === 'task' ? 'warning' : 'success'" size="small">
                  {{ row.type === 'task' ? '任务包' : '上报包' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" size="small">{{
                  statusLabel(row.status)
                }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160" />
            <el-table-column label="操作" width="160" align="center">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="downloadPkg(row)"
                  >下载</el-button
                >
                <el-button type="info" size="small" link @click="viewDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="数据包详情" width="600px">
      <el-descriptions v-if="detailData" :column="1" border>
        <el-descriptions-item label="名称">{{ detailData.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{
          detailData.type === 'task' ? '任务包' : '上报包'
        }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{
          statusLabel(detailData.status)
        }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{
          detailData.description || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailData.created_at }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { get, post } from '@/api/request'
import request from '@/api/request'
import { downloadBlobAsFile } from '@/api/helpers/blobDownload'
import { AuthStorage } from '@/utils/authStorage'
import { DATA_TYPES, DATA_TYPE_LABELS } from '@/constants/dataTypes'

defineOptions({ name: 'TaskPackageAdmin' })

const activeTab = ref('create')
const creating = ref(false)
const importing = ref(false)
const loadingList = ref(false)
const listFilter = ref('')
const packageList = ref<any[]>([])
const detailVisible = ref(false)
const detailData = ref<any>(null)

const typeLabels: Record<string, string> = {
  villages: '帮扶村',
  projects: '项目',
  funds: '经费',
  schools: '学校',
  rural_works: '乡村工作',
}

const createForm = reactive({
  name: '',
  year: new Date().getFullYear().toString(),
  dataTypes: [DATA_TYPES.VILLAGES, DATA_TYPES.PROJECTS, DATA_TYPES.FUNDS] as string[],
  description: '',
})

// ========== 生成任务包 ==========
async function createTaskPackage() {
  if (!createForm.name) {
    ElMessage.warning('请输入任务名称')
    return
  }
  if (createForm.dataTypes.length === 0) {
    ElMessage.warning('请至少选择一种数据类型')
    return
  }
  creating.value = true
  try {
    // 尝试从 localStorage 获取用户信息中的 org_id
    let orgId: number | undefined
    try {
      const userStr = JSON.stringify(AuthStorage.getUser()) || JSON.stringify(AuthStorage.getUser())
      if (userStr) {
        const u = JSON.parse(userStr)
        orgId = u.organization_id || u.org_id
      }
    } catch {
      /* ignore */
    }
    await post('/data-packages/export', {
      data_types: createForm.dataTypes,
      description: `[任务包] ${createForm.name} - ${createForm.description}`,
      type: 'task',
      ...(orgId ? { org_id: orgId } : {}),
    })
    ElMessage.success('任务数据包模板已生成')
    createForm.name = ''
    createForm.description = ''
    activeTab.value = 'list'
    await loadPackageList()
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.message || '生成任务包失败'
    ElMessage.error(errorMsg)
  } finally {
    creating.value = false
  }
}

// ========== 导入上报包 ==========
interface ImportPreviewData {
  fileName: string
  orgName: string
  counts: Record<string, number>
  tempId?: string
}
const importPreview = ref<ImportPreviewData | null>(null)
const uploadRef = ref<any>(null)
const selectedFile = ref<File | null>(null)

async function handleFileChange(file: any) {
  const raw = file?.raw || file
  selectedFile.value = raw || null
  if (!selectedFile.value) return

  // 上传到后端进行验证
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  try {
    const data = await post('/data-packages/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (data?.errors?.length) {
      ElMessage.error(`数据包验证失败: ${data.errors[0]}`)
      clearImport()
      return
    }
    importPreview.value = {
      fileName: selectedFile.value.name,
      orgName: data?.manifest?.org_name || '已验证',
      counts: data?.manifest?.record_counts || {},
      tempId: String(data?.package_id || ''),
    }
  } catch {
    ElMessage.error('数据包上传失败，请检查文件格式')
    clearImport()
  }
}

async function confirmImport() {
  if (!importPreview.value?.tempId) {
    ElMessage.warning('请先选择并上传文件')
    return
  }
  importing.value = true
  try {
    const packageId = importPreview.value.tempId
    await post(`/data-packages/${packageId}/confirm`, {
      package_id: Number(packageId),
      confirm: true,
    })
    ElMessage.success('数据包导入成功')
    clearImport()
    activeTab.value = 'list'
    await loadPackageList()
  } catch {
    // 全局拦截器已处理
  } finally {
    importing.value = false
  }
}

function clearImport() {
  importPreview.value = null
  selectedFile.value = null
  uploadRef.value?.clearFiles()
}

// ========== 历史列表 ==========
async function loadPackageList() {
  loadingList.value = true
  try {
    const params: Record<string, any> = { page: 1, page_size: 50 }
    if (listFilter.value) {
      params.type = listFilter.value
    }
    const data = await get('/data-packages', params)
    packageList.value = data?.items || data?.data?.items || []
  } catch {
    packageList.value = []
  } finally {
    loadingList.value = false
  }
}

function statusTagType(status: string): 'success' | 'warning' | 'info' | 'danger' | 'primary' {
  const map: Record<string, 'success' | 'warning' | 'info' | 'danger' | 'primary'> = {
    completed: 'success',
    exported: 'success',
    imported: 'success',
    pending: 'warning',
    processing: 'info',
    failed: 'danger',
    error: 'danger',
  }
  return map[status] || 'info'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    completed: '已完成',
    exported: '已导出',
    imported: '已导入',
    pending: '待处理',
    processing: '处理中',
    failed: '失败',
    error: '错误',
    draft: '草稿',
  }
  return map[status] || status || '未知'
}

async function downloadPkg(row: any) {
  try {
    await downloadBlobAsFile(
      () => request.get(`/data-packages/${row.id}/download`, { responseType: 'blob' }),
      { fallbackFileName: `${row.name || '数据包'}.zip` }
    )
  } catch {
    ElMessage.error('下载失败')
  }
}

function viewDetail(row: any) {
  detailData.value = row
  detailVisible.value = true
}

onMounted(() => {
  loadPackageList()
})
</script>

<style scoped>
.task-package-admin {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-header {
  margin-bottom: 8px;
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
</style>
