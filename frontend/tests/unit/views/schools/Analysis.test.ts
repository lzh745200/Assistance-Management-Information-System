/**
 * views/schools/Analysis.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：渲染与图表 option 透传。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

vi.mock('@/components/common/BaseChart.vue', () => ({
  default: {
    name: 'BaseChart',
    template: '<div class="base-chart-stub" />',
    props: ['option', 'height'],
  },
}))

import Analysis from '@/views/schools/Analysis.vue'

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('schools/Analysis.vue', () => {
  it('渲染两个图表卡片', async () => {
    const wrapper = mount(Analysis, {
      global: {
        renderStubDefaultSlot: true,
        stubs: {
          'el-card': { template: '<div class="el-card-stub"><slot name="header" /><slot /></div>' },
          'el-row': { template: '<div class="el-row-stub"><slot /></div>' },
          'el-col': { template: '<div class="el-col-stub"><slot /></div>' },
        },
      },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('学校分析')
    expect(wrapper.findAll('.base-chart-stub')).toHaveLength(2)
  })

  it('typeOption/regionOption 结构', async () => {
    const wrapper = mount(Analysis, {
      global: {
        renderStubDefaultSlot: true,
        stubs: {
          'el-card': { template: '<div class="el-card-stub"><slot name="header" /><slot /></div>' },
          'el-row': { template: '<div class="el-row-stub"><slot /></div>' },
          'el-col': { template: '<div class="el-col-stub"><slot /></div>' },
        },
      },
    })
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.typeOption.series[0].type).toBe('pie')
    expect(vm.typeOption.series[0].data).toEqual([])
    expect(vm.regionOption.series[0].type).toBe('bar')
    expect(vm.regionOption.xAxis.type).toBe('category')
    expect(vm.regionOption.xAxis.data).toEqual([])
  })
})
