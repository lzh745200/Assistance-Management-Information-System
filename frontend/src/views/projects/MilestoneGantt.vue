<template>
  <div class="milestone-gantt">
    <div v-if="milestones.length > 0" ref="chartRef" class="gantt-chart" />
    <el-empty v-else description="暂无里程碑数据" :image-size="80" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { get } from '@/api/request'

interface Milestone {
  id: number
  name: string
  plannedDate: string
  actualDate?: string
  status: string
}

const props = defineProps<{ projectId: number }>()

const chartRef = ref<HTMLElement>()
const milestones = ref<Milestone[]>([])
let chart: echarts.ECharts | null = null

function renderChart() {
  if (!chartRef.value || milestones.value.length === 0) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const names = milestones.value.map((m) => m.name)
  const baseTime = new Date('2026-01-01').getTime()

  const plannedData = milestones.value.map((m, i) => {
    const start = baseTime
    const end = m.plannedDate ? new Date(m.plannedDate).getTime() : start + 30 * 86400000
    return { value: [i, start, end, '计划'], itemStyle: { color: '#B3D8FF' } }
  })

  const actualData = milestones.value
    .map((m, i) => {
      if (!m.actualDate) return null
      const start = baseTime
      const end = new Date(m.actualDate).getTime()
      const isOverdue = m.plannedDate && end > new Date(m.plannedDate).getTime()
      return {
        value: [i, start, end, '实际'],
        itemStyle: { color: isOverdue ? '#F56C6C' : '#67C23A' },
      }
    })
    .filter(Boolean)

  chart.setOption({
    tooltip: {
      formatter: (params: Record<string, unknown>) => {
        const val = (params as { value: [number, number, number, string] }).value
        const name = names[val[0]]
        const date = new Date(val[2]).toLocaleDateString()
        return `${name}<br/>${val[3]}: ${date}`
      },
    },
    grid: { left: 120, right: 40, top: 20, bottom: 30 },
    xAxis: { type: 'time', min: baseTime },
    yAxis: {
      type: 'category',
      data: names,
      inverse: true,
      axisLabel: { width: 100, overflow: 'truncate' },
    },
    series: [
      {
        name: '计划',
        type: 'custom',
        renderItem: renderGanttItem,
        encode: { x: [1, 2], y: 0 },
        data: plannedData,
      },
      {
        name: '实际',
        type: 'custom',
        renderItem: renderGanttItem,
        encode: { x: [1, 2], y: 0 },
        data: actualData,
      },
    ],
  })
}

function renderGanttItem(_params: Record<string, unknown>, api: Record<string, Function>) {
  const yIndex = (api as { value: (idx: number) => number }).value(0)
  const start = (api as { coord: (val: [number, number]) => number[] }).coord([
    (api as { value: (idx: number) => number }).value(1),
    yIndex,
  ])
  const end = (api as { coord: (val: [number, number]) => number[] }).coord([
    (api as { value: (idx: number) => number }).value(2),
    yIndex,
  ])
  const height = 12

  return {
    type: 'rect',
    shape: { x: start[0], y: start[1] - height / 2, width: end[0] - start[0], height },
    style: (api as { style: () => Record<string, unknown> }).style(),
  }
}

async function loadMilestones() {
  if (!props.projectId) return
  try {
    const res = await get(`/projects/${props.projectId}/milestones`)
    const data = res.data || res
    milestones.value = Array.isArray(data) ? data : data.items || []
    renderChart()
  } catch {
    milestones.value = []
  }
}

watch(() => props.projectId, loadMilestones)
onMounted(loadMilestones)
onBeforeUnmount(() => {
  chart?.dispose()
})
</script>

<style scoped>
.milestone-gantt {
  padding: 16px 0;
}
.gantt-chart {
  width: 100%;
  height: 300px;
}
</style>
