<template>
  <div class="notification-settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">通知设置</span>
          <span class="subtitle">管理您的消息通知偏好</span>
        </div>
      </template>

      <el-form v-loading="loading" :model="preferences" label-width="150px" class="settings-form">
        <!-- 站内消息设置 -->
        <el-divider content-position="left">
          <el-icon><Bell /></el-icon>
          站内消息
        </el-divider>

        <el-form-item label="审批通知">
          <el-switch v-model="preferences.site_approval" />
          <span class="setting-desc">接收审批相关的站内消息通知</span>
        </el-form-item>

        <el-form-item label="任务提醒">
          <el-switch v-model="preferences.site_task" />
          <span class="setting-desc">接收任务相关的站内消息提醒</span>
        </el-form-item>

        <el-form-item label="系统通知">
          <el-switch v-model="preferences.site_system" />
          <span class="setting-desc">接收系统公告和维护通知</span>
        </el-form-item>

        <!-- 邮件通知设置 -->
        <el-divider content-position="left">
          <el-icon><Message /></el-icon>
          邮件通知
        </el-divider>

        <el-form-item label="审批通知">
          <el-switch v-model="preferences.email_approval" />
          <span class="setting-desc">通过邮件接收审批相关通知</span>
        </el-form-item>

        <el-form-item label="任务提醒">
          <el-switch v-model="preferences.email_task" />
          <span class="setting-desc">通过邮件接收任务相关提醒</span>
        </el-form-item>

        <el-form-item label="系统通知">
          <el-switch v-model="preferences.email_system" />
          <span class="setting-desc">通过邮件接收系统公告</span>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-divider />

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">
            <el-icon><Check /></el-icon>
            保存设置
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 说明信息 -->
      <el-alert title="温馨提示" type="info" :closable="false" show-icon class="tips-alert">
        <template #default>
          <ul class="tips-list">
            <li>关闭某类通知后，您将不会收到该类型的消息推送</li>
            <li>重要的系统通知可能会忽略您的偏好设置</li>
            <li>邮件通知需要您在个人资料中设置有效的邮箱地址</li>
          </ul>
        </template>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell, Message, Check, Refresh } from '@element-plus/icons-vue'
import {
  getNotificationPreferences,
  updateNotificationPreferences,
  type NotificationPreference,
} from '@/api/message'

// ==================== 状态 ====================

const loading = ref(false)
const saving = ref(false)

const preferences = ref<NotificationPreference>({
  email_approval: true,
  email_task: true,
  email_system: false,
  site_approval: true,
  site_task: true,
  site_system: true,
})

const originalPreferences = ref<NotificationPreference | null>(null)

// ==================== 方法 ====================

/**
 * 加载通知偏好
 */
async function loadPreferences() {
  loading.value = true
  try {
    const data = await getNotificationPreferences()
    preferences.value = { ...data }
    originalPreferences.value = { ...data }
  } catch (error) {
    ElMessage.error('加载通知设置失败')
  } finally {
    loading.value = false
  }
}

/**
 * 保存设置
 */
async function handleSave() {
  saving.value = true
  try {
    await updateNotificationPreferences(preferences.value)
    originalPreferences.value = { ...preferences.value }
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

/**
 * 重置设置
 */
function handleReset() {
  if (originalPreferences.value) {
    preferences.value = { ...originalPreferences.value }
    ElMessage.info('已重置为上次保存的设置')
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadPreferences()
})
</script>

<style scoped lang="scss">
.notification-settings {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  .title {
    font-size: 18px;
    font-weight: 600;
  }

  .subtitle {
    margin-left: 12px;
    font-size: 14px;
    color: #909399;
  }
}

.settings-form {
  .el-divider {
    margin: 30px 0 20px;

    :deep(.el-divider__text) {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #303133;
    }
  }

  .setting-desc {
    margin-left: 16px;
    color: #909399;
    font-size: 13px;
  }
}

.tips-alert {
  margin-top: 20px;

  .tips-list {
    margin: 0;
    padding-left: 20px;

    li {
      line-height: 1.8;
    }
  }
}
</style>
