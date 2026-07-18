import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElButton, ElSkeleton } from 'element-plus'
import KpiCards from '@/views/dashboard/KpiCards.vue'

const mockGet = vi.hoisted(() => vi.fn())

// Mock request API（组件使用命名导出 get）
vi.mock('@/api/request', () => ({
  get: mockGet,
  default: { get: mockGet },
}))

const statsPayload = {
  data: {
    code: 200,
    data: {
      total_villages: 128,
      total_projects: 45,
      total_schools: 32,
      total_population: 126000,
      total_funds: 8900000,
    },
  },
}

function mountKpi(trends?: Record<string, number>) {
  return mount(KpiCards, {
    global: {
      components: { ElButton, ElSkeleton },
      stubs: { 'el-icon': true },
    },
    props: trends ? { trends } : {},
  })
}

async function flush() {
  await new Promise((r) => setTimeout(r, 300))
}

describe('KpiCards.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGet.mockResolvedValue(statsPayload)
  })

  it('renders 5 stat-card elements', async () => {
    const wrapper = mountKpi()
    await flush()
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('.stat-card').length).toBe(5)
  })

  it('renders .data-number on each card', async () => {
    const wrapper = mountKpi()
    await flush()
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('.data-number').length).toBeGreaterThanOrEqual(5)
  })

  it('shows green tag for positive, red for negative trend', async () => {
    const wrapper = mountKpi({
      villages: 12,
      projects: -3,
      schools: 0,
      population: 8,
      funds: 15,
    })
    await flush()
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('.trend-tag--up').length).toBeGreaterThanOrEqual(3)
    expect(wrapper.findAll('.trend-tag--down').length).toBeGreaterThanOrEqual(1)
  })

  it('renders 5 kpi columns', async () => {
    const wrapper = mountKpi()
    await flush()
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('.kpi-col').length).toBe(5)
  })

  it('stat-card is keyboard accessible (role/tabindex)', async () => {
    const wrapper = mountKpi()
    await flush()
    await wrapper.vm.$nextTick()
    const card = wrapper.find('.stat-card')
    expect(card.attributes('role')).toBe('button')
    expect(card.attributes('tabindex')).toBe('0')
  })

  it('shows error placeholder with retry button when loading fails', async () => {
    mockGet.mockRejectedValue(new Error('network error'))
    const wrapper = mountKpi()
    await flush()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.kpi-error').exists()).toBe(true)
    expect(wrapper.findAll('.stat-card').length).toBe(0)

    // 点击“重试”后恢复渲染卡片（el-button 被全局 stub,@click 透传到 stub 根元素）
    mockGet.mockResolvedValue(statsPayload)
    await wrapper.find('.kpi-error el-button-stub').trigger('click')
    await flush()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.kpi-error').exists()).toBe(false)
    expect(wrapper.findAll('.stat-card').length).toBe(5)
  })
})
