<template>
  <div class="policy-edit">
    <el-card v-loading="loading" class="edit-card">
      <template #header>
        <div class="card-header">
          <span class="title">{{ isEdit ? '编辑政策' : '新增政策' }}</span>
          <div class="actions">
            <el-button @click="handleBack">
              <el-icon><Back /></el-icon>
              返回列表
            </el-button>
          </div>
        </div>
      </template>

      <el-form ref="formRef" :model="formData" :rules="rules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="政策标题" prop="title">
              <el-input
                v-model="formData.title"
                placeholder="请输入政策标题"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="文号" prop="document_number">
              <el-input
                v-model="formData.document_number"
                placeholder="请输入文号（可选）"
                maxlength="100"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="政策分类" prop="category">
              <el-select
                v-model="formData.category"
                placeholder="请选择政策分类"
                style="width: 100%"
                @change="handleCategoryChange"
              >
                <el-option label="军队政策" value="military" />
                <el-option label="地方政策" value="local" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="组织层级" prop="organization_level">
              <el-select
                v-model="formData.organization_level"
                placeholder="请选择组织层级"
                style="width: 100%"
                :disabled="!formData.category"
              >
                <el-option
                  v-for="level in levelOptions"
                  :key="level.value"
                  :label="level.label"
                  :value="level.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发布部门" prop="issuing_authority">
              <el-input
                v-model="formData.issuing_authority"
                placeholder="请输入发布部门（可选）"
                maxlength="200"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发布日期" prop="publish_date">
              <el-date-picker
                v-model="formData.publish_date"
                type="date"
                value-format="YYYY-MM-DDTHH:mm:ss"
                placeholder="请选择发布日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="生效日期" prop="effective_date">
              <el-date-picker
                v-model="formData.effective_date"
                type="date"
                value-format="YYYY-MM-DDTHH:mm:ss"
                placeholder="请选择生效日期（可选）"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关键词" prop="keywords">
              <el-input
                v-model="formData.keywords"
                placeholder="多个关键词用逗号分隔（可选）"
                maxlength="500"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio value="active">有效</el-radio>
            <el-radio value="invalid">失效</el-radio>
            <el-radio value="draft">草稿</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="政策摘要" prop="summary">
          <el-input
            v-model="formData.summary"
            type="textarea"
            :rows="3"
            placeholder="请输入政策摘要（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="政策内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="12"
            placeholder="请输入政策内容"
          />
        </el-form-item>

        <el-form-item label="附件">
          <el-upload
            class="upload-demo"
            :action="uploadAction"
            :file-list="fileList"
            :on-success="handleUploadSuccess"
            :on-remove="handleUploadRemove"
            :before-upload="beforeUpload"
            :auto-upload="false"
            multiple
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持上传 jpg/png/pdf/doc/docx 文件，单个文件不超过 10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
            <el-icon><Check /></el-icon>
            保存
          </el-button>
          <el-button @click="handleBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useRouterSafe, safeRouteParam } from '@/composables/useRouterSafe'
import { ElMessage, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import { Back, Upload, Check } from '@element-plus/icons-vue'
import { usePolicyStore } from '@/stores/policy'
import {
  getLevelOptions,
  type PolicyCategory,
  type PolicyStatus,
  type OrganizationLevel,
  type PolicyCreate,
  type PolicyUpdate,
} from '@/api/policy'

const route = useRoute()
const { pushSafe } = useRouterSafe()
const policyStore = usePolicyStore()

const loading = ref(false)
const submitLoading = ref(false)
const isEdit = computed(() => !!route.params.id)

// 表单数据
const formData = reactive({
  title: '',
  category: '' as PolicyCategory | '',
  organization_level: '' as OrganizationLevel | '',
  publish_date: '',
  effective_date: '',
  issuing_authority: '',
  content: '',
  summary: '',
  document_number: '',
  keywords: '',
  attachment_urls: [] as string[],
  status: 'active' as PolicyStatus,
})

const fileList = ref<UploadFile[]>([])
const uploadAction = ref(`${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/files/upload`)

// 层级选项（根据分类动态变化）
const levelOptions = computed(() => {
  if (!formData.category) return []
  return getLevelOptions(formData.category as PolicyCategory)
})

// 表单验证规则
const rules: FormRules = {
  title: [
    { required: true, message: '请输入政策标题', trigger: 'blur' },
    {
      min: 2,
      max: 500,
      message: '标题长度在 2 到 500 个字符',
      trigger: 'blur',
    },
  ],
  category: [{ required: true, message: '请选择政策分类', trigger: 'change' }],
  organization_level: [{ required: true, message: '请选择组织层级', trigger: 'change' }],
  publish_date: [{ required: true, message: '请选择发布日期', trigger: 'change' }],
  content: [
    { required: true, message: '请输入政策内容', trigger: 'blur' },
    { max: 100000, message: '政策内容不能超过10万字符', trigger: 'blur' },
  ],
}

const formRef = ref<FormInstance>()

// 分类变化时清空层级选择
const handleCategoryChange = () => {
  formData.organization_level = ''
}

// 加载政策数据（编辑模式）
const loadData = async () => {
  const id = safeRouteParam(route.params.id)
  if (!id || isNaN(id)) return

  loading.value = true
  try {
    await policyStore.fetchPolicyById(id)
    const policy = policyStore.currentPolicy

    if (policy) {
      formData.title = policy.title
      formData.category = policy.category
      formData.organization_level = policy.organization_level
      formData.publish_date = policy.publish_date
      formData.effective_date = (policy as any).effective_date || ''
      formData.issuing_authority = policy.department || (policy as any).issuing_authority || ''
      formData.content = policy.content
      formData.summary = policy.summary || ''
      formData.document_number = policy.document_number || ''
      formData.keywords = (policy as any).keywords || ''
      formData.attachment_urls = policy.attachment_urls || []
      formData.status = policy.status

      // 处理附件列表
      if (policy.attachment_urls && policy.attachment_urls.length > 0) {
        fileList.value = policy.attachment_urls.map((url, index) => ({
          name: url.split('/').pop() || `附件${index + 1}`,
          url: url,
          uid: index,
        })) as UploadFile[]
      }
    } else {
      ElMessage.error('未找到该政策')
      pushSafe('/policies')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载政策数据失败')
    pushSafe('/policies')
  } finally {
    loading.value = false
  }
}

// 返回列表
const handleBack = () => {
  pushSafe('/policies')
}

// 上传成功处理
const handleUploadSuccess = (response: any, _file: UploadFile) => {
  if (response?.url) {
    formData.attachment_urls.push(response.url)
  }
  ElMessage.success('上传成功')
}

// 上传移除处理
const handleUploadRemove = (file: UploadFile) => {
  if (file.url) {
    const index = formData.attachment_urls.indexOf(file.url)
    if (index > -1) {
      formData.attachment_urls.splice(index, 1)
    }
  }
}

// 上传前检查
const beforeUpload = (file: File) => {
  const allowedTypes = [
    'image/jpeg',
    'image/png',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ]
  const maxSize = 10 * 1024 * 1024 // 10MB

  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('只能上传 jpg/png/pdf/doc/docx 文件!')
    return false
  }

  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }

  return true
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      const data = {
        title: formData.title,
        category: formData.category as PolicyCategory,
        organization_level: formData.organization_level as OrganizationLevel,
        publish_date: formData.publish_date,
        effective_date: formData.effective_date || undefined,
        issuing_authority: formData.issuing_authority || undefined,
        content: formData.content,
        summary: formData.summary || undefined,
        document_number: formData.document_number || undefined,
        keywords: formData.keywords || undefined,
        status: formData.status,
      }

      if (isEdit.value) {
        // 更新政策
        const id = safeRouteParam(route.params.id)
        await policyStore.editPolicy(id, data as PolicyUpdate)
        ElMessage.success('更新成功')
      } else {
        // 新增政策
        await policyStore.addPolicy(data as PolicyCreate)
        ElMessage.success('新增成功')
      }

      pushSafe('/policies')
    } catch (error: any) {
      ElMessage.error(error.message || '保存失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// 初始化
onMounted(async () => {
  if (isEdit.value) {
    await loadData()
  }
})
</script>

<style scoped lang="scss">
.policy-edit {
  padding: 20px;
  background: rgba(10, 30, 20, 0.3);
  min-height: calc(100vh - 60px);
}

.edit-card {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(64, 145, 108, 0.3);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #1b4332;
}

.actions {
  display: flex;
  gap: 10px;
}

.upload-demo {
  width: 100%;
}

:deep(.el-form-item__label) {
  color: #1b4332;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.el-textarea__inner) {
  background-color: rgba(255, 255, 255, 0.9);
  color: #1b4332;
}

:deep(.el-select__wrapper),
:deep(.el-select .el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.el-date-editor) {
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.el-radio-group) {
  color: #1b4332;
}

:deep(.el-radio__label) {
  color: #1b4332;
}

:deep(.el-upload__tip) {
  color: #666;
}
</style>
