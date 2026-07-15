<template>
  <div class="data-management">
    <!-- 页面标题 -->
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span class="title">数据管理中心</span>
          <span class="subtitle">集中管理数据导入、导出和备份功能</span>
        </div>
      </template>

      <!-- 数据统计概览 -->
      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="帮扶村总数" :value="stats.villageCount" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="本月导入" :value="stats.monthlyImports" suffix="次" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="本月导出" :value="stats.monthlyExports" suffix="次" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="备份数量" :value="stats.backupCount" />
        </el-col>
      </el-row>
    </el-card>

    <!-- 功能模块选项卡 -->
    <el-tabs v-model="activeTab" type="border-card" class="main-tabs">
      <!-- 数据导入 -->
      <el-tab-pane label="数据导入" name="import">
        <ImportSection @import-complete="handleImportComplete" />
      </el-tab-pane>

      <!-- 数据导出 -->
      <el-tab-pane label="数据导出" name="export">
        <ExportSection @export-complete="handleExportComplete" />
      </el-tab-pane>

      <!-- 数据备份 -->
      <el-tab-pane label="数据备份" name="backup">
        <BackupSection @backup-complete="handleBackupComplete" />
      </el-tab-pane>

      <!-- 数据质量 -->
      <el-tab-pane label="数据质量" name="quality">
        <QualitySection :stats="qualityStats" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'

import { ref, onMounted, defineAsyncComponent } from 'vue'
import { ElMessage } from 'element-plus'
import { get, apiRequest } from '@/api/request'

// 异步加载子组件
const ImportSection = defineAsyncComponent(() => import('./components/ImportSection.vue'))
const ExportSection = defineAsyncComponent(() => import('./components/ExportSection.vue'))
const BackupSection = defineAsyncComponent(() => import('./components/BackupSection.vue'))
const QualitySection = defineAsyncComponent(() => import('./components/QualitySection.vue'))

// 状态
const activeTab = ref('import')
const stats = ref({
  villageCount: 0,
  monthlyImports: 0,
  monthlyExports: 0,
  backupCount: 0,
})

const qualityStats = ref({
  totalRecords: 0,
  validRecords: 0,
  invalidRecords: 0,
  completenessRate: 0,
  lastCheckTime: '',
})
// 加载统计数据
async function loadStats() {
  try {
    // Use /dashboard/stats for real aggregate statistics
    const res = await get('/dashboard/stats')
    const data = res?.data ?? res ?? {}
    stats.value = {
      villageCount: data.total_villages ?? data.villageCount ?? 0,
      monthlyImports: data.monthly_imports ?? data.monthlyImports ?? 0,
      monthlyExports: data.monthly_exports ?? data.monthlyExports ?? 0,
      backupCount: data.backup_count ?? data.backupCount ?? 0,
    }
    // 加载帮扶村数据用于质量统计
    const villageRes = await apiRequest({ method: 'GET', url: '/supported-villages', params: { page: 1, page_size: 200 }})
    const villages = villageRes.data?.items || []
    const totalRecords = villages.length
    const validRecords = villages.filter(
      (v: any) => v.department && v.village_name && v.county
    ).length
    qualityStats.value = {
      totalRecords,
      validRecords,
      invalidRecords: totalRecords - validRecords,
      completenessRate:
        totalRecords > 0 ? Math.round((validRecords / totalRecords) * 10000) / 100 : 0,
      lastCheckTime: new Date().toLocaleString('zh-CN'),
    }
  } catch (error) {
    logger.error('加载统计数据失败:', error)
  }
}

// 事件处理
function handleImportComplete() {
  loadStats()
  ElMessage.success('数据导入完成')
}

function handleExportComplete() {
  loadStats()
  ElMessage.success('数据导出完成')
}

function handleBackupComplete() {
  loadStats()
  ElMessage.success('数据备份完成')
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped lang="scss">
.data-management {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;

  .card-header {
    .title {
      font-size: 20px;
      font-weight: 600;
      color: #1b4332;
    }

    .subtitle {
      margin-left: 12px;
      font-size: 14px;
      color: #909399;
    }
  }
}

.main-tabs {
  :deep(.el-tabs__content) {
    padding: 20px;
    min-height: 500px;
  }
}
</style>
