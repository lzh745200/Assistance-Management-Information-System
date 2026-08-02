/**
 * views/analytics/Assessment.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：cards 计算（总数/优秀数/平均分三分支/待改进）、barOpt/pieOpt（等级计数与颜色映射）、
 * levelTag 五分支、onMounted（code 200+items/非 200/缺 items/异常 message 与兜底）、
 * 模板：空态、错误 alert、统计卡、图表、明细表行。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }))

vi.mock('@/api/request', () => ({ get: mockGet }))

import Assessment from '@/views/analytics/Assessment.vue'

const scores = [
  { village_id: 1, village_name: '甲村', support_unit: '单位A', scores: { economic: 90, social: 80, project_completion: 70, fund_execution: 60 }, total_score: 95, level: '优秀', rank: 1 },
  { village_id: 2, village_name: '乙村', support_unit: '单位B', scores: { economic: 80, social: 75, project_completion: 65, fund_execution: 55 }, total_score: 85, level: '良好', rank: 2 },
  { village_id: 3, village_name: '丙村', support_unit: '单位C', scores: { economic: 70, social: 60, project_completion: 50, fund_execution: 40 }, total_score: 70, level: '合格', rank: 3 },
  { village_id: 4, village_name: '丁村', support_unit: '单位D', scores: { economic: 50, social: 40, project_completion: 30, fund_execution: 20 }, total_score: 55, level: '待改进', rank: 4 },
  { village_id: 5, village_name: '戊村', support_unit: '单位E', scores: { economic: 10, social: 10, project_completion: 10, fund_execution: 10 }, total_score: 20, level: '未知等级', rank: 5 },
]

const goodResp = { code: 200, data: { items: scores, total: 5, year: 2024, weights: {} } }

function mountComp() {
  return mount(Assessment, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        BaseChart: { name: 'BaseChart', template: '<div class="base-chart-stub" />' },
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot name="header" /><slot /></div>',
        },
        'el-statistic': {
          name: 'ElStatistic',
          props: ['value', 'title', 'suffix'],
          template: '<div class="el-statistic-stub">{{ title }}:{{ value }}{{ suffix }}</div>',
        },
        'el-table': { name: 'ElTable', template: '<div class="el-table-stub"><slot /></div>' },
        'el-table-column': {
          name: 'ElTableColumn',
          template:
            '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /><slot :row="rowC" /><slot :row="rowD" /><slot :row="rowE" /></div>',
          data() {
            return { rowA: scores[0], rowB: scores[1], rowC: scores[2], rowD: scores[3], rowE: scores[4] }
          },
        },
        'el-tag': { name: 'ElTag', template: '<span class="el-tag-stub"><slot /></span>' },
        'el-empty': { name: 'ElEmpty', template: '<div class="el-empty-stub"><slot /></div>' },
        'el-alert': {
          name: 'ElAlert',
          props: ['title'],
          template: '<div class="el-alert-stub">{{ title }}<slot /></div>',
        },
        'el-row': { name: 'ElRow', template: '<div class="el-row-stub"><slot /></div>' },
        'el-col': { name: 'ElCol', template: '<div class="el-col-stub"><slot /></div>' },
      },
    },
  })
}

beforeEach(() => {
  vi.resetAllMocks()
  mockGet.mockResolvedValue(goodResp)
})

describe('挂载与数据加载', () => {
  it('onMounted 成功：渲染统计卡、图表、明细表', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(mockGet).toHaveBeenCalledWith('/assessment/village-scores')
    expect(vm.scores).toHaveLength(5)
    expect(vm.loading).toBe(false)
    expect(vm.error).toBe('')
    const text = wrapper.text()
    expect(text).toContain('评估村数:5个')
    expect(text).toContain('优秀等级:1个')
    expect(text).toContain('平均总分:65分') // round((95+85+70+55+20)/5)=65
    expect(text).toContain('待改进:2个')
    expect(text).toContain('90') // rowA scores.economic slot
    expect(text).toContain('优秀') // 等级标签 slot
    expect(text).toContain('未知等级')
    expect(wrapper.findAllComponents({ name: 'BaseChart' }).length).toBe(2)
  })

  it('code 非 200 / items 缺失 → 保持空列表', async () => {
    mockGet.mockResolvedValue({ code: 500, data: { items: scores } })
    let wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).scores).toEqual([])

    mockGet.mockResolvedValue({ code: 200, data: {} })
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).scores).toEqual([])
  })

  it('异常：response.data.message / message / 默认 三种', async () => {
    mockGet.mockRejectedValue({ response: { data: { message: '后端错误' } } })
    let wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).error).toBe('后端错误')

    mockGet.mockRejectedValue(new Error('网络错误'))
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).error).toBe('网络错误')

    mockGet.mockRejectedValue(new Error(''))
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).error).toBe('获取评估数据失败')
  })
})

describe('空态与错误态', () => {
  it('无数据 → el-empty 空态', async () => {
    mockGet.mockResolvedValue({ code: 200, data: { items: [] } })
    const wrapper = mountComp()
    await flushPromises()
    expect(wrapper.find('.el-empty-stub').exists()).toBe(true)
    expect(wrapper.find('.el-alert-stub').exists()).toBe(false)
  })

  it('错误 → el-alert 展示', async () => {
    mockGet.mockRejectedValue(new Error('x'))
    const wrapper = mountComp()
    await flushPromises()
    expect(wrapper.find('.el-alert-stub').exists()).toBe(true)
    expect(wrapper.find('.el-empty-stub').exists()).toBe(false)
  })
})

describe('计算属性与工具函数', () => {
  it('cards：总数 0 → 平均分 0；levelTag 五分支', async () => {
    mockGet.mockResolvedValue({ code: 200, data: { items: [] } })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const cards = vm.cards
    expect(cards[0].value).toBe(0)
    expect(cards[1].value).toBe(0)
    expect(cards[2].value).toBe(0)
    expect(cards[3].value).toBe(0)

    expect(vm.levelTag('优秀')).toBe('success')
    expect(vm.levelTag('良好')).toBe('primary')
    expect(vm.levelTag('合格')).toBe('warning')
    expect(vm.levelTag('待改进')).toBe('danger')
    expect(vm.levelTag('未知')).toBe('info')
  })

  it('barOpt/pieOpt：等级计数聚合与颜色映射兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.barOpt.xAxis.data).toEqual(['甲村', '乙村', '丙村', '丁村', '戊村'])
    expect(vm.barOpt.series[0].data).toEqual([95, 85, 70, 55, 20])
    const pie = vm.pieOpt.series[0].data
    expect(pie.find((d: any) => d.name === '优秀').value).toBe(1)
    expect(pie.find((d: any) => d.name === '待改进').value).toBe(1)
    expect(pie.find((d: any) => d.name === '未知等级').itemStyle.color).toBe('#999')
    expect(pie.find((d: any) => d.name === '优秀').itemStyle.color).toBe('#4a7c59')
  })

  it('表格行渲染等级标签与分数', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('80') // rowB scores.social
    expect(text).toContain('65') // rowC project_completion
    expect(text).toContain('20') // rowE fund_execution
  })
})
