<template>
  <div class="kpi-cards">
    <div v-for="(card, i) in cards" :key="i" class="kpi-col">
      <div class="stat-card" :class="card.theme" @click="navigateTo(card.route)">
        <div class="stat-icon">
          <el-icon><component :is="card.icon" /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">
            <span class="data-number data-number--lg">{{ card.formatted }}</span>
            <span v-if="card.unit" class="data-unit">{{ card.unit }}</span>
          </div>
          <div class="stat-trend" :class="trendClass(card.trend)">
            <span class="trend-tag" :class="trendTagClass(card.trend)">
              <i class="trend-tag__arrow">{{ trendArrow(card.trend) }}</i>
              <template v-if="card.trend !== 0">{{ Math.abs(card.trend) }}%</template>
              <template v-else>持平</template>
            </span>
            <span class="trend-label">较上月</span>
          </div>
        </div>
        <div :ref="(el: any) => (sparkRefs[i] = el)" class="stat-sparkline" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { OfficeBuilding, Folder, School, Money, User } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { get } from '@/api/request'
import { useRouterSafe } from '@/composables/useRouterSafe'
import { unwrapData } from '@/utils/unwrapData'

export interface DashboardStats {
  total_villages: number
  total_projects: number
  total_schools: number
  total_population: number
  total_funds: number
}
export interface KpiTrends {
  villages: number
  projects: number
  schools: number
  population: number
  funds: number
}

interface Props {
  trends?: KpiTrends
}
const props = withDefaults(defineProps<Props>(), {
  trends: () => ({
    villages: 0,
    projects: 0,
    schools: 0,
    population: 0,
    funds: 0,
  }),
})
const trends = computed(() => props.trends)

const stats = ref<DashboardStats>({
  total_villages: 0,
  total_projects: 0,
  total_schools: 0,
  total_population: 0,
  total_funds: 0,
})

function fmt(v: number | undefined): string {
  return v != null ? v.toLocaleString() : '--'
}
function fmtFunds(v: number | undefined): string {
  return v != null ? (v / 10000).toFixed(0) : '--'
}
function fmtPop(v: number | undefined): string {
  if (v == null) return '--'
  return v >= 10000 ? (v / 10000).toFixed(1) + '万' : v.toLocaleString()
}
function trendClass(v: number) {
  return v > 0 ? 'stat-trend--up' : v < 0 ? 'stat-trend--down' : ''
}
function trendTagClass(v: number) {
  return v > 0 ? 'trend-tag--up' : v < 0 ? 'trend-tag--down' : 'trend-tag--flat'
}
function trendArrow(v: number) {
  return v > 0 ? '↗' : v < 0 ? '↘' : '→'
}

const icons: Record<string, any> = {
  OfficeBuilding,
  Folder,
  School,
  Money,
  User,
}

const cards = computed(() => [
  {
    theme: 'primary',
    icon: icons.OfficeBuilding,
    label: '帮扶村',
    formatted: fmt(stats.value.total_villages),
    unit: '个',
    trend: trends.value.villages,
    route: '/supported-villages',
  },
  {
    theme: 'success',
    icon: icons.Folder,
    label: '帮扶项目',
    formatted: fmt(stats.value.total_projects),
    unit: '个',
    trend: trends.value.projects,
    route: '/projects',
  },
  {
    theme: 'warning',
    icon: icons.School,
    label: '帮扶学校',
    formatted: fmt(stats.value.total_schools),
    unit: '所',
    trend: trends.value.schools,
    route: '/schools',
  },
  {
    theme: 'danger',
    icon: icons.Money,
    label: '帮扶经费',
    formatted: fmtFunds(stats.value.total_funds),
    unit: '万元',
    trend: trends.value.funds,
    route: '/funds',
  },
  {
    theme: 'info-card',
    icon: icons.User,
    label: '覆盖人口',
    formatted: fmtPop(stats.value.total_population),
    unit: undefined,
    trend: trends.value.population,
    route: '/supported-villages',
  },
])

function navigateTo(route?: string) {
  if (!route) return
  try {
    const { pushSafe } = useRouterSafe()
    pushSafe(route)
  } catch {
    window.location.hash = '#' + route
  }
}

const SPARK_COLORS = ['#1e4d8c', '#2d6a4f', '#f59e0b', '#ef4444', '#6366f1']
const SPARK_ALPHAS = [
  'rgba(30,77,140,0.19)',
  'rgba(45,106,79,0.19)',
  'rgba(245,158,11,0.19)',
  'rgba(239,68,68,0.19)',
  'rgba(99,102,241,0.19)',
]
const sparkRefs: (HTMLElement | null)[] = [null, null, null, null, null]
let sparkCharts: (echarts.ECharts | null)[] = []

function makeSparkOption(data: number[], color: string, alpha: string): echarts.EChartsCoreOption {
  return {
    grid: { left: 0, right: 0, top: 2, bottom: 0 },
    xAxis: { type: 'category', data: data.map((_, idx) => idx), show: false },
    yAxis: { type: 'value', show: false },
    series: [
      {
        type: 'line',
        data,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: alpha },
            { offset: 1, color: 'rgba(255,255,255,0)' },
          ]),
        },
      },
    ],
  }
}

function initSparklines() {
  sparkCharts.forEach((c) => c?.dispose())
  sparkCharts = sparkRefs.map((el, i) => {
    if (!el) return null
    const chart = echarts.init(el)
    const statValues = [
      stats.value.total_villages,
      stats.value.total_projects,
      stats.value.total_schools,
      stats.value.total_funds,
      stats.value.total_population,
    ]
    const base = statValues[i] || 100
    const data = Array.from({ length: 8 }, () => Math.round(base * (0.7 + Math.random() * 0.5)))
    chart.setOption(makeSparkOption(data, SPARK_COLORS[i], SPARK_ALPHAS[i]))
    return chart
  })
}

async function loadStats() {
  try {
    const res = await get('/dashboard/stats', {
      params: { refresh: true },
    } as any)
    const d = unwrapData<Record<string, number>>(res, {} as Record<string, number>)
    if (d) {
      stats.value = {
        total_villages: d.total_villages ?? 0,
        total_projects: d.total_projects ?? 0,
        total_schools: d.total_schools ?? 0,
        total_population: d.total_population ?? 0,
        total_funds: d.total_funds ?? 0,
      }
    }
  } catch {
    /* use defaults */
  }
}

function handleResize() {
  sparkCharts.forEach((c) => c?.resize())
}

onMounted(async () => {
  await loadStats()
  await nextTick()
  initSparklines()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  sparkCharts.forEach((c) => c?.dispose())
  sparkCharts = []
})
</script>

<style scoped lang="scss">
.kpi-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  @media (max-width: 1200px) {
    grid-template-columns: repeat(3, 1fr);
  }
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.stat-card {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  background: #fff;
  padding: 18px 20px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition:
    box-shadow 0.3s,
    transform 0.3s;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  &:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 20%;
    height: 60%;
    width: 4px;
    border-radius: 0 4px 4px 0;
  }
  &.primary::before {
    background: #1e4d8c;
  }
  &.success::before {
    background: #2d6a4f;
  }
  &.warning::before {
    background: #f59e0b;
  }
  &.danger::before {
    background: #ef4444;
  }
  &.info-card::before {
    background: #6366f1;
  }
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  margin-right: 12px;
}
.primary .stat-icon {
  background: rgba(30, 77, 140, 0.08);
  color: #1e4d8c;
}
.success .stat-icon {
  background: rgba(45, 106, 79, 0.08);
  color: #2d6a4f;
}
.warning .stat-icon {
  background: rgba(245, 158, 11, 0.08);
  color: #f59e0b;
}
.danger .stat-icon {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}
.info-card .stat-icon {
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1;
}

.stat-content {
  flex: 1;
  min-width: 0;
}
.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 2px;
}
.stat-value {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 12px;
}
.stat-trend--up {
  color: #16a34a;
}
.stat-trend--down {
  color: #dc2626;
}
.trend-label {
  color: #94a3b8;
  font-size: 11px;
}
.trend-tag {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-weight: 600;
  font-family: 'DIN Alternate', 'Roboto Mono', monospace;
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 10px;
}
.trend-tag--up {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.08);
}
.trend-tag--down {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.08);
}
.trend-tag--flat {
  color: #64748b;
  background: rgba(100, 116, 139, 0.08);
}
.trend-tag__arrow {
  font-size: 10px;
}
.stat-sparkline {
  width: 100%;
  height: 36px;
  margin-top: 8px;
}
</style>
