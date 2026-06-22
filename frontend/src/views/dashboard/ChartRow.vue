<template>
  <div class="chart-row">
    <div class="chart-card">
      <h3 class="chart-title">项目进度跟踪</h3>
      <div ref="barRef" class="chart-body" />
    </div>
    <div class="chart-card">
      <h3 class="chart-title">经费使用概览</h3>
      <div ref="pieRef" class="chart-body" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import echarts from '@/utils/echarts'
import request from '@/api/request'

const barRef = ref<HTMLElement>()
const pieRef = ref<HTMLElement>()
let barChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

async function fetchData() {
  try {
    const [projRes, fundRes] = await Promise.all([
      request.get('/projects', {
        params: { summary: true, page_size: 5 },
      } as any),
      request.get('/dashboard/stats', { params: { refresh: true } } as any),
    ])
    return {
      projects: projRes?.data?.items || projRes?.data?.data || [],
      funds: {
        allocated: fundRes?.data?.funds_allocated || fundRes?.data?.total_funds || 0,
        pending: fundRes?.data?.funds_pending || 0,
        planned: fundRes?.data?.funds_planned || 0,
      },
    }
  } catch {
    return {
      projects: [],
      funds: { allocated: 600, pending: 200, planned: 90 },
    }
  }
}

function buildBarOption(projects: any[]): echarts.EChartsCoreOption {
  const names = projects.map((p: any) => p.name || p.project_name || '')
  const values = projects.map((p: any) => p.progress ?? p.completion_rate ?? 0)
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,.96)',
      borderColor: '#e2e8f0',
      borderRadius: 8,
      textStyle: { color: '#1e293b', fontSize: 13 },
    },
    grid: { left: 8, right: 24, top: 8, bottom: 8 },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#94a3b8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: names.reverse(),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#475569', fontSize: 12 },
    },
    series: [
      {
        type: 'bar',
        data: values.reverse(),
        barWidth: 16,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#2d6a4f' },
            { offset: 1, color: '#52b788' },
          ]),
        },
        label: {
          show: true,
          position: 'right',
          color: '#64748b',
          fontSize: 11,
          formatter: '{c}%',
        },
      },
    ],
  }
}

function buildPieOption(funds: {
  allocated: number
  pending: number
  planned: number
}): echarts.EChartsCoreOption {
  return {
    color: ['#2d6a4f', '#1e4d8c', '#f59e0b'],
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,.96)',
      borderColor: '#e2e8f0',
      borderRadius: 8,
      textStyle: { color: '#1e293b', fontSize: 13 },
      formatter: (p: any) => `${p.marker} ${p.name}: <b>${p.value}万</b> (${p.percent}%)`,
    },
    legend: { bottom: 0, textStyle: { color: '#64748b', fontSize: 11 } },
    series: [
      {
        type: 'pie',
        radius: ['55%', '78%'],
        center: ['50%', '46%'],
        itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 3 },
        label: { show: false },
        emphasis: {
          itemStyle: { shadowBlur: 16, shadowColor: 'rgba(0,0,0,.12)' },
        },
        data: [
          { value: funds.allocated, name: '已拨付' },
          { value: funds.pending, name: '待拨付' },
          { value: funds.planned, name: '计划中' },
        ],
      },
    ],
  }
}

function initCharts(data: { projects: any[]; funds: any }) {
  if (barRef.value) {
    barChart = echarts.init(barRef.value)
    barChart.setOption(buildBarOption(data.projects || []))
  }
  if (pieRef.value) {
    pieChart = echarts.init(pieRef.value)
    pieChart.setOption(buildPieOption(data.funds))
  }
}

function handleResize() {
  barChart?.resize()
  pieChart?.resize()
}

onMounted(async () => {
  const data = await fetchData()
  await nextTick()
  initCharts(data)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  barChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped lang="scss">
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}
.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  &::before {
    content: '';
    display: inline-block;
    width: 4px;
    height: 16px;
    border-radius: 2px;
    background: linear-gradient(180deg, #1e4d8c, #2d6a4f);
  }
}
.chart-body {
  width: 100%;
  height: 260px;
}
</style>
