<template>
  <div class="system-config-page">
    <div class="page-header">
      <h2 class="page-title">系统配置</h2>
      <div class="page-header-right">
        <span
          v-if="saveStatus.statusText.value"
          :class="['save-indicator', saveStatus.state.value]"
        >
          <el-icon v-if="saveStatus.isSaving.value" class="is-loading"><Loading /></el-icon>
          <el-icon v-else-if="saveStatus.isSaved.value" color="#67C23A"><CircleCheck /></el-icon>
          <el-icon v-else-if="saveStatus.isError.value" color="#F56C6C"><CircleClose /></el-icon>
          {{ saveStatus.statusText.value }}
        </span>
      </div>
    </div>
    <p class="page-desc">管理系统基础参数、通知设置和安全策略</p>

    <el-skeleton v-if="loading" :rows="6" animated />

    <el-tabs v-else v-model="activeTab" type="border-card">
      <!-- 基础配置 -->
      <el-tab-pane label="基础配置" name="basic">
        <el-form :model="basicConfig" label-width="140px" class="config-form">
          <el-form-item label="系统名称">
            <el-input v-model="basicConfig.systemName" />
          </el-form-item>
          <el-form-item label="系统版本">
            <el-input v-model="basicConfig.version" disabled />
          </el-form-item>
          <el-form-item label="数据年度">
            <el-date-picker
              v-model="basicConfig.dataYear"
              type="year"
              placeholder="选择年度"
              value-format="YYYY"
            />
          </el-form-item>
          <el-form-item label="默认地区">
            <el-input v-model="basicConfig.defaultRegion" />
          </el-form-item>
          <el-form-item label="分页大小">
            <el-input-number v-model="basicConfig.pageSize" :min="10" :max="100" :step="10" />
          </el-form-item>
          <el-form-item label="普通用户默认首页">
            <el-select
              v-model="basicConfig.default_user_homepage"
              placeholder="请选择普通用户登录后的默认首页"
              style="width: 100%"
            >
              <el-option label="工作台" value="/dashboard" />
              <el-option label="帮扶村管理" value="/villages" />
              <el-option label="帮扶学校管理" value="/schools" />
              <el-option label="帮扶项目管理" value="/projects" />
              <el-option label="经费管理" value="/funds/user" />
              <el-option label="政策法规" value="/policies" />
              <el-option label="乡村工作" value="/rural-works" />
              <el-option label="数据导入" value="/data-import" />
              <el-option label="审批申请" value="/approval/my-applications" />
              <el-option label="报表导出" value="/report-export" />
            </el-select>
            <span class="form-tip">设置后普通用户（非管理员）登录将自动进入此页面</span>
          </el-form-item>
          <el-form-item label="数据保留天数">
            <el-input-number v-model="basicConfig.retentionDays" :min="30" :max="365" />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="saveStatus.isSaving.value"
              @click="saveSection('basic')"
              >保存配置</el-button
            >
            <el-button @click="resetBasicConfig">重置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 通知设置 -->
      <el-tab-pane label="通知设置" name="notification">
        <el-form :model="notifyConfig" label-width="140px" class="config-form">
          <el-form-item label="启用邮件通知">
            <el-switch v-model="notifyConfig.emailEnabled" />
          </el-form-item>
          <el-form-item v-if="notifyConfig.emailEnabled" label="SMTP 服务器">
            <el-input v-model="notifyConfig.smtpHost" placeholder="smtp.example.com" />
          </el-form-item>
          <el-form-item v-if="notifyConfig.emailEnabled" label="SMTP 端口">
            <el-input-number v-model="notifyConfig.smtpPort" :min="1" :max="65535" />
          </el-form-item>
          <el-form-item v-if="notifyConfig.emailEnabled" label="发件人邮箱">
            <el-input v-model="notifyConfig.senderEmail" placeholder="noreply@example.com" />
          </el-form-item>
          <el-form-item label="启用系统通知">
            <el-switch v-model="notifyConfig.systemNotifyEnabled" />
          </el-form-item>
          <el-form-item label="备份完成通知">
            <el-switch v-model="notifyConfig.backupNotify" />
          </el-form-item>
          <el-form-item label="数据异常通知">
            <el-switch v-model="notifyConfig.errorNotify" />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="saveStatus.isSaving.value"
              @click="saveSection('notify')"
              >保存配置</el-button
            >
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 更新日志 -->
      <el-tab-pane label="更新日志" name="changelog">
        <div class="changelog-section">
          <div v-if="isAdmin" style="margin-bottom: 16px">
            <el-button type="primary" size="small" @click="showAddLog = true"
              >+ 添加更新记录</el-button
            >
          </div>
          <el-timeline v-if="updateLogs.length">
            <el-timeline-item
              v-for="log in updateLogs"
              :key="log.id"
              :timestamp="log.created_at?.slice(0, 10)"
              placement="top"
            >
              <el-card shadow="hover">
                <h4 style="margin: 0 0 8px">{{ log.version }}</h4>
                <p style="white-space: pre-wrap; color: #606266; font-size: 14px; margin: 0">
                  {{ log.description }}
                </p>
                <p style="font-size: 12px; color: #909399; margin-top: 8px">
                  操作人：{{ log.updated_by || '系统' }}
                </p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无更新记录" />
        </div>

        <!-- 添加更新日志对话框 -->
        <el-dialog v-model="showAddLog" title="添加更新记录" width="500px">
          <el-form :model="newLog" label-width="80px">
            <el-form-item label="版本号" required>
              <el-input v-model="newLog.version" placeholder="如 V1.0.2" />
            </el-form-item>
            <el-form-item label="更新内容" required>
              <el-input
                v-model="newLog.description"
                type="textarea"
                :rows="5"
                placeholder="请描述本次更新的内容"
              />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showAddLog = false">取消</el-button>
            <el-button type="primary" :loading="savingLog" @click="submitUpdateLog">确定</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <!-- 安全策略 -->
      <el-tab-pane label="安全策略" name="security">
        <el-form :model="securityConfig" label-width="160px" class="config-form">
          <el-form-item label="登录失败锁定次数">
            <el-input-number v-model="securityConfig.maxLoginAttempts" :min="3" :max="10" />
          </el-form-item>
          <el-form-item label="账号锁定时间(分)">
            <el-input-number v-model="securityConfig.lockDuration" :min="5" :max="60" />
          </el-form-item>
          <el-form-item label="会话超时时间(分)">
            <el-input-number v-model="securityConfig.sessionTimeout" :min="15" :max="480" />
          </el-form-item>
          <el-form-item label="密码最小长度">
            <el-input-number v-model="securityConfig.minPasswordLength" :min="6" :max="20" />
          </el-form-item>
          <el-form-item label="强制密码复杂度">
            <el-switch v-model="securityConfig.requireComplexPassword" />
          </el-form-item>
          <el-form-item label="密码过期天数">
            <el-input-number v-model="securityConfig.passwordExpireDays" :min="0" :max="365" />
            <span class="form-tip">0 表示不过期</span>
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="saveStatus.isSaving.value"
              @click="saveSection('security')"
              >保存配置</el-button
            >
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { get, post, put, apiRequest } from '@/api/request'
import { useSaveStatus } from '@/composables/useSaveStatus'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdmin)

const activeTab = ref('basic')
const loading = ref(true)
const saveStatus = useSaveStatus()

// ---------- 更新日志 ----------
interface UpdateLog {
  id: string
  version: string
  description: string
  updated_by: string
  created_at: string
}
const updateLogs = ref<UpdateLog[]>([])
const showAddLog = ref(false)
const savingLog = ref(false)
const newLog = reactive({ version: '', description: '' })

async function loadUpdateLogs() {
  try {
    // update_logs.py 使用 skip/limit 分页，默认 limit=100
    const { data } = await apiRequest({
      method: 'GET',
      url: '/system/update-logs',
      params: { skip: 0, limit: 100 },
    })
    updateLogs.value = data?.items || data || []
  } catch {
    /* 忽略 */
  }
}

async function submitUpdateLog() {
  if (!newLog.version || !newLog.description) {
    ElMessage.warning('请填写版本号和更新内容')
    return
  }
  savingLog.value = true
  try {
    await post('/system/update-logs', {
      version: newLog.version,
      description: newLog.description,
    })
    ElMessage.success('更新日志已添加')
    showAddLog.value = false
    newLog.version = ''
    newLog.description = ''
    await loadUpdateLogs()
  } catch {
    ElMessage.error('添加失败')
  } finally {
    savingLog.value = false
  }
}

// ---------- 默认值（也用于重置） ----------
const DEFAULTS = {
  basic: {
    systemName: '帮扶管理信息系统',
    version: 'V1.2.0',
    dataYear: '2025',
    defaultRegion: '黔南布依族苗族自治州',
    pageSize: 20,
    default_user_homepage: '/dashboard',
    retentionDays: 90,
  },
  notify: {
    emailEnabled: false,
    smtpHost: '',
    smtpPort: 465,
    senderEmail: '',
    systemNotifyEnabled: true,
    backupNotify: true,
    errorNotify: true,
  },
  security: {
    maxLoginAttempts: 5,
    lockDuration: 15,
    sessionTimeout: 120,
    minPasswordLength: 8,
    requireComplexPassword: true,
    passwordExpireDays: 90,
  },
} as const

const basicConfig = reactive({ ...DEFAULTS.basic })
const notifyConfig = reactive({ ...DEFAULTS.notify })
const securityConfig = reactive({ ...DEFAULTS.security })

// ---------- 序列化 / 反序列化辅助 ----------
type SectionKey = 'basic' | 'notify' | 'security'

const SECTION_MAP: Record<SectionKey, Record<string, any>> = {
  basic: basicConfig,
  notify: notifyConfig,
  security: securityConfig,
}

/** 将某个区域的 reactive 对象转为 ConfigItem[] */
function sectionToConfigItems(section: SectionKey) {
  const data = SECTION_MAP[section]
  return Object.entries(data).map(([field, value]) => ({
    key: `${section}.${field}`,
    value: JSON.stringify(value),
    description: null as string | null,
  }))
}

/** 从后端返回的扁平 dict 还原到 reactive 对象 */
function applyRemoteConfigs(remoteData: Record<string, any>) {
  for (const section of ['basic', 'notify', 'security'] as SectionKey[]) {
    const target = SECTION_MAP[section]
    for (const field of Object.keys(target)) {
      const remoteKey = `${section}.${field}`
      if (remoteKey in remoteData) {
        ;(target as any)[field] = remoteData[remoteKey]
      }
    }
  }
}

// ---------- 加载配置 ----------
async function loadConfigs() {
  loading.value = true
  try {
    const data = await get('/system/config')
    if (data?.data) {
      applyRemoteConfigs(data.data)
    }
  } catch {
    // 首次使用时后端可能无数据，使用默认值即可
  } finally {
    loading.value = false
  }
}

// ---------- 保存配置 ----------
const SECTION_LABEL: Record<SectionKey, string> = {
  basic: '基础配置',
  notify: '通知设置',
  security: '安全策略',
}

async function saveSection(section: SectionKey) {
  try {
    await saveStatus.wrapSave(() =>
      put('/system/config', { configs: sectionToConfigItems(section) })
    )
    ElMessage.success(`${SECTION_LABEL[section]}已保存`)
  } catch {
    // wrapSave 已经标记 error 状态，无需额外处理
  }
}

function resetBasicConfig() {
  Object.assign(basicConfig, DEFAULTS.basic)
}

// ---------- 初始化 ----------
onMounted(() => {
  loadConfigs()
  loadUpdateLogs()
})
</script>

<style scoped>
.system-config-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1b4332;
  margin: 0;
}
.page-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}
.config-form {
  max-width: 600px;
  padding: 20px;
}
.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.save-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}
.save-indicator.saved {
  color: #67c23a;
}
.save-indicator.error {
  color: #f56c6c;
}
.changelog-section {
  max-width: 700px;
  padding: 20px;
}
</style>
