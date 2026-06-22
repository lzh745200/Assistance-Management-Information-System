<template>
  <div class="system-init-page">
    <el-card class="init-card">
      <template #header>
        <div class="card-header">
          <h2>系统初始化向导</h2>
          <p v-if="!initialized">请完成以下步骤以完成系统初始配置</p>
        </div>
      </template>

      <div v-if="loading" class="loading-box">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p>检查系统状态...</p>
      </div>

      <div v-else-if="alreadyInit" class="already-init">
        <el-result icon="success" title="系统已初始化" :sub-title="'单位: ' + orgName">
          <template #extra>
            <el-button type="primary" @click="goToLogin">前往登录</el-button>
          </template>
        </el-result>
      </div>

      <div v-else>
        <el-steps :active="currentStep" finish-status="success" align-center>
          <el-step title="单位信息" />
          <el-step title="管理员账号" />
          <el-step title="确认执行" />
        </el-steps>

        <!-- Step 0: 单位信息 -->
        <el-form
          v-if="currentStep === 0"
          ref="orgFormRef"
          :model="form"
          :rules="orgRules"
          label-width="120px"
          class="init-form"
        >
          <el-form-item label="单位名称" prop="organization_name">
            <el-input v-model="form.organization_name" placeholder="请输入单位名称" />
          </el-form-item>
          <el-form-item label="单位简称">
            <el-input v-model="form.organization_short_name" placeholder="可选" />
          </el-form-item>
          <el-form-item label="单位编码">
            <el-input v-model="form.organization_code" placeholder="可选" />
          </el-form-item>
          <el-form-item label="联系人">
            <el-input v-model="form.contact_person" placeholder="可选" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="form.contact_phone" placeholder="可选" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="nextStep(orgFormRef)">下一步</el-button>
          </el-form-item>
        </el-form>

        <!-- Step 1: 管理员 -->
        <el-form
          v-if="currentStep === 1"
          ref="adminFormRef"
          :model="form"
          :rules="adminRules"
          label-width="120px"
          class="init-form"
        >
          <el-form-item label="用户名" prop="admin_username">
            <el-input v-model="form.admin_username" placeholder="管理员用户名" />
          </el-form-item>
          <el-form-item label="密码" prop="admin_password">
            <el-input
              v-model="form.admin_password"
              type="password"
              show-password
              placeholder="至少8位"
            />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              show-password
              placeholder="再次输入密码"
            />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="form.admin_email" placeholder="可选" />
          </el-form-item>
          <el-form-item>
            <el-button @click="currentStep = 0">上一步</el-button>
            <el-button type="primary" @click="nextStep(adminFormRef)">下一步</el-button>
          </el-form-item>
        </el-form>

        <!-- Step 2: 确认 -->
        <div v-if="currentStep === 2" class="init-form">
          <el-descriptions title="确认配置信息" :column="2" border>
            <el-descriptions-item label="单位名称">{{
              form.organization_name
            }}</el-descriptions-item>
            <el-descriptions-item label="用户名">{{ form.admin_username }}</el-descriptions-item>
            <el-descriptions-item label="系统名称">{{ form.system_name }}</el-descriptions-item>
            <el-descriptions-item label="联系人">{{
              form.contact_person || '-'
            }}</el-descriptions-item>
          </el-descriptions>
          <div class="step-actions">
            <el-button @click="currentStep = 1">上一步</el-button>
            <el-button type="primary" :loading="submitting" @click="executeInit"
              >确认初始化</el-button
            >
          </div>
          <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouterSafe } from '@/composables/useRouterSafe'
import { get, post } from '@/api/request'

const { pushSafe } = useRouterSafe()

const loading = ref(true)
const alreadyInit = ref(false)
const orgName = ref('')
const currentStep = ref(0)
const submitting = ref(false)
const errorMsg = ref('')
const initialized = alreadyInit // alias for template
const orgFormRef = ref<any>(null)
const adminFormRef = ref<any>(null)

const form = ref({
  organization_name: '',
  organization_short_name: '',
  organization_code: '',
  admin_username: 'admin',
  admin_password: '',
  confirmPassword: '',
  admin_email: '',
  system_name: '帮扶管理信息系统',
  contact_person: '',
  contact_phone: '',
})

const orgRules = {
  organization_name: [{ required: true, message: '请输入单位名称', trigger: 'blur' }],
}
const adminRules = {
  admin_username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  admin_password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_r: any, v: string, cb: any) =>
        cb(v !== form.value.admin_password ? new Error('两次密码不一致') : undefined),
      trigger: 'blur',
    },
  ],
}

onMounted(async () => {
  try {
    const res: any = await get('/init/status')
    const data = res?.data || res
    if (data?.initialized) {
      alreadyInit.value = true
      orgName.value = data.organization_name || ''
    }
  } catch {
    /* use defaults */
  }
  loading.value = false
})

function nextStep(formRef: any) {
  if (!formRef) {
    currentStep.value++
    return
  }
  formRef.validate((valid: boolean) => {
    if (valid) currentStep.value++
  })
}

async function executeInit() {
  submitting.value = true
  errorMsg.value = ''
  try {
    const payload: any = { ...form.value }
    delete payload.confirmPassword
    await post('/init/initialize', payload)
    ElMessage.success('系统初始化成功！即将跳转登录页...')
    setTimeout(() => pushSafe('/login'), 1500)
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || e?.message || '初始化失败'
  } finally {
    submitting.value = false
  }
}

function goToLogin() {
  pushSafe('/login')
}
</script>

<style scoped>
.system-init-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  background: #081c15;
  padding: 20px;
}
.init-card {
  width: 100%;
  max-width: 680px;
}
.card-header {
  text-align: center;
}
.card-header h2 {
  color: #1b4332;
}
.loading-box {
  text-align: center;
  padding: 60px;
}
.init-form {
  margin-top: 30px;
}
.step-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  justify-content: center;
}
.error-msg {
  margin-top: 16px;
  color: #f56c6c;
  text-align: center;
}
</style>
