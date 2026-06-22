<template>
  <div class="subscriptions-page">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">报表订阅管理</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>新增订阅
          </el-button>
        </div>
      </template>

      <el-alert
        type="info"
        :closable="false"
        style="margin-bottom: 16px"
        title="报表订阅说明"
        description="设置报表自动生成和分发规则，系统将按照指定周期自动生成报表并通过系统消息推送。"
      />

      <!-- 订阅列表 -->
      <el-table v-loading="loading" :data="subscriptions" stripe>
        <el-table-column prop="name" label="订阅名称" min-width="160">
          <template #default="{ row }">
            <div class="sub-name">
              <el-icon><Document /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="reportType" label="报表类型" width="140">
          <template #default="{ row }">
            <el-tag size="small" :type="getReportTypeTag(row.reportType)">
              {{ getReportTypeLabel(row.reportType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="frequency" label="生成周期" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ frequencyMap[row.frequency] || row.frequency }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="nextRun" label="下次生成" width="160" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              active-value="active"
              inactive-value="paused"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="lastRun" label="上次生成" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleRunNow(row)">立即生成</el-button>
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 执行历史 -->
      <el-card class="history-card">
        <template #header>
          <span>最近执行记录</span>
        </template>
        <el-timeline>
          <el-timeline-item
            v-for="record in historyRecords"
            :key="record.id"
            :type="record.status === 'success' ? 'success' : 'danger'"
            :timestamp="record.time"
          >
            <div class="history-item">
              <span class="history-name">{{ record.name }}</span>
              <el-tag size="small" :type="record.status === 'success' ? 'success' : 'danger'">
                {{ record.status === 'success' ? '成功' : '失败' }}
              </el-tag>
              <span class="history-detail">{{ record.detail }}</span>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showAddDialog" :title="editingId ? '编辑订阅' : '新增订阅'" width="600px">
      <el-form ref="formRef" :model="form" label-width="100px" :rules="rules">
        <el-form-item label="订阅名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入订阅名称" />
        </el-form-item>
        <el-form-item label="报表类型" prop="reportType">
          <el-select v-model="form.reportType" placeholder="选择报表类型" style="width: 100%">
            <el-option label="帮扶村统计报表" value="village_stats" />
            <el-option label="学校帮扶报表" value="school_stats" />
            <el-option label="项目进度报表" value="project_progress" />
            <el-option label="经费使用报表" value="fund_usage" />
            <el-option label="综合汇总报表" value="comprehensive" />
          </el-select>
        </el-form-item>
        <el-form-item label="生成周期" prop="frequency">
          <el-select v-model="form.frequency" placeholder="选择周期" style="width: 100%">
            <el-option label="每日" value="daily" />
            <el-option label="每周" value="weekly" />
            <el-option label="每月" value="monthly" />
            <el-option label="每季度" value="quarterly" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据范围">
          <el-radio-group v-model="form.scope">
            <el-radio-button label="all">全部数据</el-radio-button>
            <el-radio-button label="org">本组织</el-radio-button>
            <el-radio-button label="self">仅本人</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document } from '@element-plus/icons-vue'

const loading = ref(false)
const showAddDialog = ref(false)
const editingId = ref<string | null>(null)
const formRef = ref()

const frequencyMap: Record<string, string> = {
  daily: '每日',
  weekly: '每周',
  monthly: '每月',
  quarterly: '每季度',
}

const subscriptions = ref([
  {
    id: '1',
    name: '月度帮扶村统计',
    reportType: 'village_stats',
    frequency: 'monthly',
    nextRun: '2026-05-01 08:00',
    status: 'active',
    lastRun: '2026-04-01 08:00',
  },
  {
    id: '2',
    name: '周度项目进度报告',
    reportType: 'project_progress',
    frequency: 'weekly',
    nextRun: '2026-04-27 08:00',
    status: 'active',
    lastRun: '2026-04-20 08:00',
  },
  {
    id: '3',
    name: '季度经费汇总',
    reportType: 'fund_usage',
    frequency: 'quarterly',
    nextRun: '2026-07-01 08:00',
    status: 'paused',
    lastRun: '2026-01-01 08:00',
  },
])

const historyRecords = ref([
  {
    id: '1',
    name: '月度帮扶村统计',
    status: 'success',
    time: '2026-04-01 08:00',
    detail: '生成 24 条记录，导出 Excel',
  },
  {
    id: '2',
    name: '周度项目进度报告',
    status: 'success',
    time: '2026-04-20 08:00',
    detail: '生成 56 个项目进度记录',
  },
  {
    id: '3',
    name: '季度经费汇总',
    status: 'error',
    time: '2026-01-01 08:00',
    detail: '数据库连接超时，已重试',
  },
])

const form = reactive({
  name: '',
  reportType: '',
  frequency: 'monthly',
  scope: 'all',
  remark: '',
})

const rules = {
  name: [{ required: true, message: '请输入订阅名称', trigger: 'blur' }],
  reportType: [{ required: true, message: '请选择报表类型', trigger: 'change' }],
  frequency: [{ required: true, message: '请选择生成周期', trigger: 'change' }],
}

function getReportTypeLabel(type: string): string {
  const map: Record<string, string> = {
    village_stats: '帮扶村统计',
    school_stats: '学校帮扶',
    project_progress: '项目进度',
    fund_usage: '经费使用',
    comprehensive: '综合汇总',
  }
  return map[type] || type
}

function getReportTypeTag(type: string): 'success' | 'warning' | 'primary' | 'danger' | 'info' {
  const map: Record<string, 'success' | 'warning' | 'primary' | 'danger' | 'info'> = {
    village_stats: 'success',
    school_stats: 'warning',
    project_progress: 'primary',
    fund_usage: 'danger',
    comprehensive: 'info',
  }
  return map[type] || 'info'
}

function handleStatusChange(row: any) {
  const statusText = row.status === 'active' ? '启用' : '暂停'
  ElMessage.success(`已${statusText}订阅：${row.name}`)
}

function handleRunNow(row: any) {
  ElMessage.info(`正在生成报表：${row.name}...`)
  setTimeout(() => {
    ElMessage.success(`报表生成成功：${row.name}`)
    row.lastRun = new Date().toLocaleString('zh-CN')
    historyRecords.value.unshift({
      id: Date.now().toString(),
      name: row.name,
      status: 'success',
      time: row.lastRun,
      detail: '手动触发生成',
    })
  }, 1500)
}

function handleEdit(row: any) {
  editingId.value = row.id
  form.name = row.name
  form.reportType = row.reportType
  form.frequency = row.frequency
  showAddDialog.value = true
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定要删除订阅「${row.name}」吗？`, '确认删除', { type: 'warning' })
    subscriptions.value = subscriptions.value.filter((s) => s.id !== row.id)
    ElMessage.success('删除成功')
  } catch {
    // 取消删除
  }
}

function handleSave() {
  formRef.value?.validate((valid: boolean) => {
    if (!valid) return
    if (editingId.value) {
      const idx = subscriptions.value.findIndex((s) => s.id === editingId.value)
      if (idx >= 0) {
        subscriptions.value[idx] = { ...subscriptions.value[idx], ...form }
      }
      ElMessage.success('更新成功')
    } else {
      subscriptions.value.push({
        id: Date.now().toString(),
        ...form,
        nextRun: '待定',
        status: 'active',
        lastRun: '-',
      })
      ElMessage.success('创建成功')
    }
    showAddDialog.value = false
    editingId.value = null
    formRef.value?.resetFields()
  })
}
</script>

<style scoped>
.subscriptions-page {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-title {
  font-size: 16px;
  font-weight: bold;
  color: #1b4332;
}
.sub-name {
  display: flex;
  align-items: center;
  gap: 8px;
}
.history-card {
  margin-top: 20px;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.history-name {
  font-weight: 500;
}
.history-detail {
  color: #909399;
  font-size: 12px;
}
</style>
