import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import PieChart from '@/components/charts/PieChart.vue'
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

describe('charts/PieChart.vue', () => {
  beforeEach(() => {
    initMock.mockClear()
  })

  it('renders BaseChart with computed pie option', () => {
    const wrapper = mount(PieChart, { props: { data } })
    const baseChart = wrapper.findComponent(BaseChart)
    expect(baseChart.exists()).toBe(true)
    expect(baseChart.props('option')).toEqual({
      tooltip: { trigger: 'item' },
      series: [{ type: 'pie', data, radius: ['40%', '70%'] }],
    })
  })

  it('handles missing data via || fallback', () => {
    const wrapper = mount(PieChart, { props: { height: 260 } })
    const baseChart = wrapper.findComponent(BaseChart)
    expect(baseChart.props('option')).toEqual({
      tooltip: { trigger: 'item' },
      series: [{ type: 'pie', data: [], radius: ['40%', '70%'] }],
    })
    expect(baseChart.props('height')).toBe(260)
  })
})
