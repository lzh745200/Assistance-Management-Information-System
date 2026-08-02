/**
 * views/effectiveness/Evaluation.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：flatResult（null/result 存在/过滤字段）、flatCompareResult、fieldLabel（映射+兜底）、
 * formatValue（null/百分比/金额/数字/字符串）、loadVillages（data/裸对象、name 兜底、失败）、
 * handleEvaluate（无村庄警告/成功/失败）、handleCompare（无村庄/同年警告/成功/失败）、
 * onMounted（无查询参数/带参数自动评估）、模板：评估按钮、对比按钮、结果与对比卡。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

const {
  ElMessage,
  mockApiRequest,
  mockEvaluateVillage,
  mockCompareEvaluations,
  routeQuery,
} = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  mockApiRequest: vi.fn(),
  mockEvaluateVillage: vi.fn(),
  mockCompareEvaluations: vi.fn(),
  routeQuery: {} as Record<string, any>,
}))

vi.mock('element-plus', () => ({ ElMessage }))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: routeQuery }),
  useRouter: () => ({ resolve: () => ({ name: 'X', matched: [1] }) }),
}))

vi.mock('@/api/effectiveness', () => ({
  evaluateVillage: mockEvaluateVillage,
  compareEvaluations: mockCompareEvaluations,
  getEvaluationReport: vi.fn(),
  getRankings: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  apiRequest: mockApiRequest,
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
}))

import Evaluation from '@/views/effectiveness/Evaluation.vue'

const villages = [
  { id: 1, name: '甲村' },
  { id: 2, village_name: '乙村' },
  { id: 3 },
]

const evalResult = {
  total_score: 90.5,
  economic: 85.2,
  level: '优秀',
  per_capita_income: 18000,
  total_funds: 500000,
  growth_rate: 0.12,
  project_completion_rate: 0.95,
  village_id: 99,
  village_name: '甲村',
}

const compareResult = {
  total_score: 80,
  economic: 70,
  per_capita_income: 12000,
}

function mountComp() {
  return mount(Evaluation, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-form': { name: 'ElForm', template: '<div class="el-form-stub"><slot /></div>' },
        'el-form-item': {
          name: 'ElFormItem',
          template: '<div class="el-form-item-stub"><slot /></div>',
        },
        'el-select': {
          name: 'ElSelect',
          template: '<div class="el-select-stub"><slot /></div>',
          emits: ['update:modelValue'],
        },
        'el-option': { name: 'ElOption', template: '<div class="el-option-stub"><slot /></div>' },
        'el-descriptions': {
          name: 'ElDescriptions',
          template: '<div class="el-descriptions-stub"><slot /></div>',
        },
        'el-descriptions-item': {
          name: 'ElDescriptionsItem',
          props: ['label'],
          template: '<div class="el-descriptions-item-stub">{{ label }}<slot /></div>',
        },
        'el-tag': { name: 'ElTag', template: '<span class="el-tag-stub"><slot /></span>' },
        'el-empty': { name: 'ElEmpty', template: '<div class="el-empty-stub"><slot /></div>' },
        'el-icon': { name: 'ElIcon', template: '<span class="el-icon-stub"><slot /></span>' },
      },
    },
  })
}

const findBtn = (wrapper: any, text: string) => {
  const btn = wrapper.findAll('el-button-stub').find((b: any) => b.text().includes(text))
  expect(btn, text).toBeTruthy()
  return btn!
}

beforeEach(() => {
  vi.resetAllMocks()
  Object.keys(routeQuery).forEach((k) => delete routeQuery[k])
  mockApiRequest.mockResolvedValue({ data: { items: villages } })
  mockEvaluateVillage.mockResolvedValue({ data: evalResult })
  mockCompareEvaluations.mockResolvedValue({ data: compareResult })
})

describe('挂载与村庄加载', () => {
  it('onMounted：加载村庄选项（name 兜底链）；无查询参数不自动评估', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(mockApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({ url: '/supported-villages', params: { page_size: 200 } })
    )
    expect(vm.villageOptions).toEqual([
      { id: 1, name: '甲村' },
      { id: 2, name: '乙村' },
      { id: 3, name: 'ID:3' },
    ])
    expect(mockEvaluateVillage).not.toHaveBeenCalled()
    expect(wrapper.find('.el-empty-stub').exists()).toBe(true)
  })

  it('loadVillages：裸对象/数组/嵌套形态；失败 → 空选项', async () => {
    mockApiRequest.mockResolvedValue({ items: villages })
    let wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).villageOptions).toHaveLength(3)

    // data 直接为数组 → Array.isArray 真侧
    mockApiRequest.mockResolvedValue({ data: villages })
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).villageOptions).toHaveLength(3)

    // inner 无 items 且非数组 → [] 兜底
    mockApiRequest.mockResolvedValue({ data: {} })
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).villageOptions).toEqual([])

    // response 为 null → ?. 短路
    mockApiRequest.mockResolvedValue(null)
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).villageOptions).toEqual([])

    mockApiRequest.mockRejectedValue(new Error('net'))
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).villageOptions).toEqual([])
  })

  it('onMounted 带查询参数 → 自动评估', async () => {
    routeQuery.villageId = '5'
    routeQuery.year = '2024'
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.evalForm.villageId).toBe(5)
    expect(vm.evalForm.year).toBe(2024)
    expect(mockEvaluateVillage).toHaveBeenCalledWith({ village_id: 5, year: 2024 })
    expect(vm.evaluationResult).toEqual(evalResult)
  })
})

describe('handleEvaluate', () => {
  it('未选村庄 → 警告早退', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.evalForm.villageId = 0
    await vm.handleEvaluate()
    expect(ElMessage.warning).toHaveBeenCalledWith('请选择村庄')
    expect(mockEvaluateVillage).not.toHaveBeenCalled()
  })

  it('成功：response?.data 形态；评估按钮点击触发', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.evalForm.villageId = 1
    vm.evalForm.year = 2025
    await findBtn(wrapper, '开始评估').trigger('click')
    await flushPromises()
    expect(mockEvaluateVillage).toHaveBeenCalledWith({ village_id: 1, year: 2025 })
    expect(vm.evaluationResult).toEqual(evalResult)
    expect(vm.compareResult).toBeNull()
    expect(ElMessage.success).toHaveBeenCalledWith('评估完成')
    expect(vm.evaluating).toBe(false)
    // 模板：评估报告卡渲染（descriptions + 标签）
    expect(wrapper.text()).toContain('2025年度')
    expect(wrapper.text()).toContain('总分')
  })

  it('成功：response 裸对象形态（?? 兜底）；评估中 loading 态', async () => {
    mockEvaluateVillage.mockResolvedValue(evalResult)
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.evalForm.villageId = 2
    vm.evaluating = true
    await nextTick()
    expect(wrapper.text()).toContain('正在评估中')
    await vm.handleEvaluate()
    expect(vm.evaluationResult).toEqual(evalResult)
  })

  it('失败 → error 提示，finally 复位', async () => {
    mockEvaluateVillage.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.evalForm.villageId = 1
    await vm.handleEvaluate()
    expect(ElMessage.error).toHaveBeenCalledWith('评估失败')
    expect(vm.evaluating).toBe(false)
  })
})

describe('handleCompare', () => {
  it('未选村庄 / 同年份 → 警告', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.evalForm.villageId = 0
    await vm.handleCompare()
    expect(ElMessage.warning).toHaveBeenCalledWith('请先完成评估')

    vm.evalForm.villageId = 1
    vm.compareForm.year1 = 2025
    vm.compareForm.year2 = 2025
    await vm.handleCompare()
    expect(ElMessage.warning).toHaveBeenCalledWith('请选择不同的年度进行对比')
    expect(mockCompareEvaluations).not.toHaveBeenCalled()
  })

  it('成功：数据加载 + 提示；「对比」按钮点击', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.evalForm.villageId = 1
    vm.compareForm.year1 = 2024
    vm.compareForm.year2 = 2025
    vm.evaluationResult = evalResult // 对比区块 v-if 依赖
    await nextTick()
    await findBtn(wrapper, '对比').trigger('click')
    await flushPromises()
    expect(mockCompareEvaluations).toHaveBeenCalledWith(1, 2024, 2025)
    expect(vm.compareResult).toEqual(compareResult)
    expect(ElMessage.success).toHaveBeenCalledWith('对比完成')
    expect(vm.comparing).toBe(false)
    expect(wrapper.text()).toContain('人均收入')
  })

  it('失败 → error 提示', async () => {
    mockCompareEvaluations.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.evalForm.villageId = 1
    await vm.handleCompare()
    expect(ElMessage.error).toHaveBeenCalledWith('对比失败')
    expect(vm.comparing).toBe(false)

    // response 无 data → ?? 兜底
    mockCompareEvaluations.mockResolvedValue(compareResult)
    await vm.handleCompare()
    expect(vm.compareResult).toEqual(compareResult)
  })
})

describe('计算属性与格式化', () => {
  it('flatResult：null / result 嵌套 / 过滤排除字段', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.flatResult).toEqual({})

    vm.evaluationResult = { result: { total_score: 1 } }
    expect(vm.flatResult).toEqual({ total_score: 1 })

    vm.evaluationResult = { ...evalResult }
    const flat = vm.flatResult
    expect(flat.village_id).toBeUndefined()
    expect(flat.village_name).toBeUndefined()
    expect(flat.total_score).toBe(90.5)
  })

  it('flatCompareResult：null / 非空', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.flatCompareResult).toEqual({})
    vm.compareResult = compareResult
    expect(vm.flatCompareResult).toEqual(compareResult)
  })

  it('fieldLabel：映射与下划线替换兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.fieldLabel('total_score')).toBe('总分')
    expect(vm.fieldLabel('economic')).toBe('经济得分')
    expect(vm.fieldLabel('social')).toBe('社会得分')
    expect(vm.fieldLabel('project_completion')).toBe('项目完成率')
    expect(vm.fieldLabel('fund_execution')).toBe('资金执行率')
    expect(vm.fieldLabel('level')).toBe('等级')
    expect(vm.fieldLabel('rank')).toBe('排名')
    expect(vm.fieldLabel('per_capita_income')).toBe('人均收入')
    expect(vm.fieldLabel('collective_income')).toBe('集体收入')
    expect(vm.fieldLabel('total_projects')).toBe('项目总数')
    expect(vm.fieldLabel('completed_projects')).toBe('已完成项目')
    expect(vm.fieldLabel('project_completion_rate')).toBe('项目完成率')
    expect(vm.fieldLabel('total_funds')).toBe('资金总额')
    expect(vm.fieldLabel('growth_rate')).toBe('增长率')
    expect(vm.fieldLabel('score')).toBe('得分')
    expect(vm.fieldLabel('custom_key')).toBe('custom key')
  })

  it('formatValue：null/百分比/金额/数字/字符串', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.formatValue('x', null)).toBe('-')
    expect(vm.formatValue('growth_rate', 0.12)).toBe('12.0%')
    expect(vm.formatValue('percent_x', 0.5)).toBe('50.0%')
    expect(vm.formatValue('per_capita_income', 18000)).toBe('18,000')
    expect(vm.formatValue('total_funds', 500000)).toBe('500,000')
    expect(vm.formatValue('amount_x', 1234)).toBe('1,234')
    expect(vm.formatValue('total_score', 90.5)).toBe('90.5')
    expect(vm.formatValue('level', '优秀')).toBe('优秀')
  })

  it('结果卡与对比结果卡模板渲染（descriptions 值）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.evaluationResult = evalResult
    vm.compareResult = compareResult
    await nextTick()
    const text = wrapper.text()
    expect(text).toContain('90.5')
    expect(text).toContain('12.0%')
    expect(text).toContain('18,000')
    expect(text).toContain('85.2')
    expect(text).toContain('80.0')
    expect(text).not.toContain('选择两个不同年度进行对比分析') // 对比结果已展示
  })
})

describe('表单 v-model', () => {
  it('村庄/年度/对比年度 select 同步', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.evaluationResult = evalResult // 对比表单 v-if 依赖
    await nextTick()
    const selects = wrapper.findAllComponents({ name: 'ElSelect' })
    selects[0].vm.$emit('update:modelValue', 7)
    expect(vm.evalForm.villageId).toBe(7)
    selects[1].vm.$emit('update:modelValue', 2023)
    expect(vm.evalForm.year).toBe(2023)
    selects[2].vm.$emit('update:modelValue', 2022)
    expect(vm.compareForm.year1).toBe(2022)
    selects[3].vm.$emit('update:modelValue', 2026)
    expect(vm.compareForm.year2).toBe(2026)
  })
})
