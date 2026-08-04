import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LineChart from '@/components/charts/LineChart.vue'
import BaseChart from '@/components/common/BaseChart.vue'

const echartsInstance = vi.hoisted(() => ({
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
  on: vi.fn(),
}))
const initMock = vi.hoisted(() => vi.fn(() => echartsInstance))
vi.mock('@/utils/echarts', () => ({
  __esModule: true,
  default: { init: initMock, use: vi.fn(), graphic: {} },
}))

const data = [
  { name: 'A', value: 10 },
  { name: 'B', value: 20 },
]

describe('charts/LineChart.vue', () => {
  beforeEach(() => {
    initMock.mockClear()
  })

  it('renders BaseChart with computed line option', () => {
    const wrapper = mount(LineChart, { props: { data } })
    const baseChart = wrapper.findComponent(BaseChart)
    expect(baseChart.exists()).toBe(true)
    expect(baseChart.props('option')).toEqual({
      xAxis: { type: 'category', data: ['A', 'B'] },
      yAxis: { type: 'value' },
      series: [{ type: 'line', data: [10, 20], smooth: true }],
    })
  })

  it('handles missing data via || fallback', () => {
    const wrapper = mount(LineChart, { props: { height: 240 } })
    const baseChart = wrapper.findComponent(BaseChart)
    expect(baseChart.props('option')).toEqual({
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value' },
      series: [{ type: 'line', data: [], smooth: true }],
    })
    expect(baseChart.props('height')).toBe(240)
  })
})
