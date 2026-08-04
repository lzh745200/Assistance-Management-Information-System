import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FundSummary from '@/components/common/FundSummary.vue'

const stubs = {
  'el-row': { name: 'ElRow', template: '<div class="el-row"><slot /></div>' },
  'el-col': { name: 'ElCol', props: ['xs', 'sm'], template: '<div class="el-col"><slot /></div>' },
  'el-card': { name: 'ElCard', props: ['shadow'], template: '<div class="el-card"><slot /></div>' },
  'el-statistic': {
    name: 'ElStatistic',
    props: ['title', 'value'],
    template:
      '<div class="el-statistic"><span class="stat-title">{{ title }}</span><slot name="prefix" /><span class="stat-value">{{ value }}</span><slot name="suffix" /></div>',
  },
}

describe('common/FundSummary.vue', () => {
  it('renders all four items with values, prefixes and suffix', () => {
    const wrapper = mount(FundSummary, {
      props: {
        data: {
          total_amount: 1000,
          approved_amount: 600,
          pending_amount: 400,
          total_count: 12,
        },
      },
      global: { stubs },
    })
    const items = wrapper.findAll('.el-statistic')
    expect(items.length).toBe(4)
    expect(items[0].find('.stat-title').text()).toBe('经费总额')
    expect(items[0].text()).toContain('¥')
    expect(items[0].text()).toContain('1000')
    expect(items[3].text()).toContain('12')
    expect(items[3].text()).toContain('条')
  })

  it('falls back to 0 when data fields are missing', () => {
    const wrapper = mount(FundSummary, { props: { data: {} }, global: { stubs } })
    const items = wrapper.findAll('.el-statistic')
    expect(items.length).toBe(4)
    expect(items[0].text()).toContain('0')
    expect(items[3].text()).toContain('0')
  })

  it('handles null data object via optional chaining', () => {
    const wrapper = mount(FundSummary, { props: { data: null as any }, global: { stubs } })
    const items = wrapper.findAll('.el-statistic')
    expect(items.length).toBe(4)
    expect(items[0].text()).toContain('0')
  })
})
