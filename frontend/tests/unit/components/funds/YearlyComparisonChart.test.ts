import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, enableAutoUnmount, flushPromises } from '@vue/test-utils'
import YearlyComparisonChart from '@/components/funds/YearlyComparisonChart.vue'
import BaseChart from '@/components/common/BaseChart.vue'

enableAutoUnmount(afterEach)

const echartsInstance = vi.hoisted(() => ({
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
  on: vi.fn(),
}))
vi.mock('@/utils/echarts', () => ({
  __esModule: true,
  default: { init: vi.fn(() => echartsInstance), use: vi.fn(), graphic: {} },
}))

const mockGet = vi.hoisted(() => vi.fn())
vi.mock('@/api/request', () => ({ get: mockGet,
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))

const stubs = {
  'el-card': {
    name: 'ElCard',
    props: ['shadow'],
    template: '<div class="el-card"><slot name="header" /><slot /></div>',
  },
  'el-empty': {
    name: 'ElEmpty',
    props: ['description'],
    template: '<div class="el-empty" />',
  },
}

describe('funds/YearlyComparisonChart.vue', () => {
  beforeEach(() => {
    mockGet.mockReset()
  })

  it('loads data on mount and renders BaseChart with computed option', async () => {
    mockGet.mockResolvedValue({
      data: [
        { year: 2022, total_actual: 100 },
        { year: 2023, amount: 200 },
        { year: 2024 },
        { total_actual: 50 },
      ],
    })
    const wrapper = mount(YearlyComparisonChart, {
      props: { yearStart: 2022, yearEnd: 2024, department: 'rural' },
      global: { stubs },
    })
    await flushPromises()

    expect(mockGet).toHaveBeenCalledWith('/funds/supported-village/statistics/yearly-comparison', {
      year_start: 2022,
      year_end: 2024,
      department: 'rural',
    })
    const baseChart = wrapper.findComponent(BaseChart)
    expect(baseChart.exists()).toBe(true)
    const option = baseChart.props('option') as any
    expect(option.xAxis.data).toEqual(['2022', '2023', '2024', ''])
    expect(option.series[0].data).toEqual([100, 200, 0, 50])
  })

  it('renders empty state when API returns empty list', async () => {
    mockGet.mockResolvedValue({ data: [] })
    const wrapper = mount(YearlyComparisonChart, { global: { stubs } })
    await flushPromises()
    expect(wrapper.findComponent(BaseChart).exists()).toBe(false)
    expect(wrapper.find('.el-empty').exists()).toBe(true)
  })

  it('renders empty state when response has no data property', async () => {
    mockGet.mockResolvedValue({})
    const wrapper = mount(YearlyComparisonChart, { global: { stubs } })
    await flushPromises()
    expect(wrapper.find('.el-empty').exists()).toBe(true)
  })

  it('handles API failure with empty chart', async () => {
    mockGet.mockRejectedValue(new Error('network'))
    const wrapper = mount(YearlyComparisonChart, {
      props: { department: '' },
      global: { stubs },
    })
    await flushPromises()
    expect(wrapper.find('.el-empty').exists()).toBe(true)
  })

  it('falls back to [] when API returns null', async () => {
    mockGet.mockResolvedValue(null)
    const wrapper = mount(YearlyComparisonChart, { global: { stubs } })
    await flushPromises()
    expect(wrapper.find('.el-empty').exists()).toBe(true)
  })

  it('only sends defined query params', async () => {
    mockGet.mockResolvedValue({ data: [] })
    const wrapper = mount(YearlyComparisonChart, { global: { stubs } })
    await flushPromises()
    expect(mockGet).toHaveBeenCalledWith('/funds/supported-village/statistics/yearly-comparison', {})
  })

  it('reloads when watched props change and exposes refresh', async () => {
    mockGet.mockResolvedValue({ data: [] })
    const wrapper = mount(YearlyComparisonChart, { global: { stubs } })
    await flushPromises()
    expect(mockGet).toHaveBeenCalledTimes(1)

    await wrapper.setProps({ yearStart: 2023 })
    await flushPromises()
    expect(mockGet).toHaveBeenCalledTimes(2)

    await (wrapper.vm as any).refresh()
    expect(mockGet).toHaveBeenCalledTimes(3)
  })
})
