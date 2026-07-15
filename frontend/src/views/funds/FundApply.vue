<template>
  <div class="fund-apply-page">
    <div class="page-header">
      <h2 class="page-title">经费申请</h2>
      <p class="page-desc">填写经费申请信息，提交后将自动进入审批流程</p>
    </div>

    <el-card>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 700px"
      >
        <el-form-item label="经费名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入经费名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="经费类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择经费类型" style="width: 100%">
            <el-option label="项目经费" value="project" />
            <el-option label="运营经费" value="operation" />
            <el-option label="教育帮扶" value="education" />
            <el-option label="基础设施" value="infrastructure" />
            <el-option label="应急经费" value="emergency" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="申请金额(万元)" prop="amount">
          <el-input-number
            v-model="form.amount"
            :min="0"
            :precision="2"
            :step="1"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="关联项目" prop="project_name">
          <el-input v-model="form.project_name" placeholder="请输入关联项目名称（可选）" />
        </el-form-item>

        <el-form-item label="经费来源" prop="source">
          <el-input v-model="form.source" placeholder="请输入经费来源" />
        </el-form-item>

        <el-form-item label="用途说明" prop="purpose">
          <el-input
            v-model="form.purpose"
            type="textarea"
            :rows="4"
            placeholder="请详细说明经费用途"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="备注" prop="remarks">
          <el-input
            v-model="form.remarks"
            type="textarea"
            :rows="2"
            placeholder="其他说明（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            提交申请
          </el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useRouterSafe } from '@/composables/useRouterSafe'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { post } from '@/api/request'

defineOptions({ name: 'FundApply' })

const router = useRouter()
const { pushSafe } = useRouterSafe()
const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  name: '',
  type: '',
  amount: 0,
  project_name: '',
  source: '',
  purpose: '',
  remarks: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入经费名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择经费类型', trigger: 'change' }],
  amount: [
    { required: true, message: '请输入申请金额', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '申请金额必须大于0', trigger: 'blur' },
  ],
  purpose: [{ required: true, message: '请填写用途说明', trigger: 'blur' }],
}

async function handleSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  if (form.amount <= 0) {
    ElMessage.warning('申请金额必须大于0')
    return
  }

  submitting.value = true
  try {
    await post('/funds/apply', {
      name: form.name,
      type: form.type,
      amount: form.amount,
      project_name: form.project_name || undefined,
      source: form.source || undefined,
      purpose: form.purpose,
      remarks: form.remarks || undefined,
      status: 'pending',
    })
    ElMessage.success('经费申请提交成功，已进入审批流程')
    pushSafe('/funds/user')
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : '提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.fund-apply-page {
  padding: 20px;
}
.page-header {
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
</style>
