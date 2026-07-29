<template>
  <div class="fund-timeline">
    <el-timeline v-if="history.length > 0">
      <el-timeline-item
        v-for="item in history"
        :key="item.id"
        :timestamp="item.changedAt || item.createdAt"
        :type="timelineType(item.newStatus)"
        placement="top"
      >
        <el-card shadow="never" class="timeline-card">
          <div class="timeline-header">
            <el-tag :type="timelineType(item.newStatus)" size="small">{{ statusLabel(item.newStatus) }}</el-tag>
            <span v-if="item.changedBy" class="timeline-operator">操作人: {{ item.changedBy }}</span>
          </div>
          <p v-if="item.reason" class="timeline-reason">{{ item.reason }}</p>
        </el-card>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无流转记录" :image-size="80" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { get } from '@/api/request'

interface StatusHistory {
  id: number
  newStatus: string
  oldStatus?: string
  reason?: string
  changedBy?: string
  changedAt?: string
  createdAt?: string
}

const props = defineProps<{ fundId: number }>()

const history = ref<StatusHistory[]>([])

function timelineType(status: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    planned: 'info', pending: 'warning', approved: 'primary',
    allocated: 'success', completed: 'success', rejected: 'danger', audited: 'primary',
  }
  return map[status] || 'primary'
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    planned: '已规划', pending: '待审批', approved: '已批准',
    allocated: '已拨付', completed: '已完成', rejected: '已驳回', audited: '已审计',
  }
  return map[status] || status
}

async function loadHistory() {
  if (!props.fundId) return
  try {
    const res = await get(`/funds/${props.fundId}/status-history`)
    const data = res.data || res
    history.value = Array.isArray(data) ? data : (data.items || [])
  } catch {
    history.value = []
  }
}

watch(() => props.fundId, loadHistory)
onMounted(loadHistory)
</script>

<style scoped>
.fund-timeline {
  padding: 16px 0;
}
.timeline-card {
  padding: 4px 0;
}
.timeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.timeline-operator {
  font-size: 12px;
  color: #909399;
}
.timeline-reason {
  margin: 8px 0 0;
  font-size: 13px;
  color: #606266;
}
</style>
