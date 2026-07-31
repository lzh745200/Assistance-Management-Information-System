/**
 * InteractiveResult.vue 组件测试
 *
 * 覆盖目标：src/views/ai/InteractiveResult.vue 100% statements
 * 场景：
 * 1. 服务状态检查 - available / 自定义状态 / 无 services / 失败
 * 2. 数据分析 - 成功（嵌套 flatten）/失败 / flattenObject 各分支
 * 3. 趋势预测 - predictions 数组 / 对象 / 空 / 失败（收入 + 经费）
 * 4. 异常检测 - 空输入演示数据 / JSON 数组 / 非数组 JSON / 非法 JSON / 失败
 * 5. 智能推荐 - 项目推荐（无ID/数组/非数组/失败）/ 系统推荐
 * 6. NLP 查询 - 空查询 / 成功 / 历史记录（>10 截断 / 点击回填）/ 失败 / 回车触发
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

// ==================== Mocks ====================

const mockGetStatus = vi.fn()
const mockAnalyze = vi.fn()
const mockGetRecommendations = vi.fn()
const mockForecastIncome = vi.fn()
const mockForecastFunds = vi.fn()
const mockDetectAnomalies = vi.fn()
const mockRecommendProjects = vi.fn()
const mockNlpQuery = vi.fn()

vi.mock('@/api/ai', () => ({
  getStatus: (...args: any[]) => mockGetStatus(...args),
  analyze: (...args: any[]) => mockAnalyze(...args),
  getRecommendations: (...args: any[]) => mockGetRecommendations(...args),
  forecastIncome: (...args: any[]) => mockForecastIncome(...args),
  forecastFunds: (...args: any[]) => mockForecastFunds(...args),
  predictTrend: vi.fn(),
  detectAnomalies: (...args: any[]) => mockDetectAnomalies(...args),
  recommendProjects: (...args: any[]) => mockRecommendProjects(...args),
  recommendFundAllocation: vi.fn(),
  nlpQuery: (...args: any[]) => mockNlpQuery(...args),
}))

const mockMessage = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
  info: vi.fn(),
}))
vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...(actual as object), ElMessage: mockMessage }
})

import InteractiveResult from '@/views/ai/InteractiveResult.vue'

// ==================== Stubs ====================

const stubs = {
  'el-icon': { template: '<i><slot/></i>' },
  'el-button': {
    template: '<button class="el-btn" :disabled="disabled" @click="$emit(\'click\')"><slot/></button>',
    props: ['type', 'disabled', 'loading'],
    emits: ['click'],
  },
  'el-tabs': {
    name: 'el-tabs',
    template: '<div class="el-tabs-stub"><slot/></div>',
    props: ['modelValue', 'type'],
    emits: ['update:modelValue'],
  },
  'el-tab-pane': {
    template: '<div class="tab-pane"><slot/></div>',
    props: ['label', 'name'],
  },
  'el-form': { template: '<form><slot/></form>', props: ['model', 'labelWidth', 'inline'] },
  'el-form-item': { template: '<div><slot/></div>', props: ['label'] },
  'el-radio-group': {
    name: 'el-radio-group',
    template: '<div class="el-radio-group-stub"><slot/></div>',
    props: ['modelValue'],
    emits: ['update:modelValue'],
  },
  'el-radio': { template: '<label><slot/></label>', props: ['value'] },
  'el-input': {
    name: 'el-input',
    template:
      '<input class="el-input-stub" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'type', 'rows', 'placeholder', 'clearable'],
    emits: ['update:modelValue'],
  },
  'el-select': {
    name: 'el-select',
    template: '<div class="el-select-stub"><slot/></div>',
    props: ['modelValue'],
    emits: ['update:modelValue'],
  },
  'el-option': { template: '<div></div>', props: ['label', 'value'] },
  'el-slider': {
    name: 'el-slider',
    template: '<div class="el-slider-stub"></div>',
    props: ['modelValue', 'min', 'max', 'showInput'],
    emits: ['update:modelValue'],
  },
  'el-input-number': {
    name: 'el-input-number',
    template: '<div class="el-input-number-stub"></div>',
    props: ['modelValue', 'min', 'placeholder'],
    emits: ['update:modelValue'],
  },
  'el-row': { template: '<div><slot/></div>', props: ['gutter'] },
  'el-col': { template: '<div><slot/></div>', props: ['span'] },
  'el-card': {
    template: '<div><div class="card-header"><slot name="header"/></div><slot/></div>',
    props: ['shadow'],
  },
  'el-table': { template: '<table><slot/></table>', props: ['data', 'stripe', 'size'] },
  'el-table-column': {
    template: '<td><slot :row="rowData" /></td>',
    props: ['prop', 'label', 'width', 'type'],
    setup() {
      return { rowData: { index: 5, value: 99, is_anomaly: true } }
    },
  },
  'el-tag': {
    template: '<span class="el-tag-stub" @click="$emit(\'click\')"><slot/></span>',
    props: ['type', 'size'],
    emits: ['click'],
  },
  'el-descriptions': { template: '<div><slot/></div>', props: ['column', 'border'] },
  'el-descriptions-item': { template: '<div><slot/></div>', props: ['label'] },
  'el-divider': { template: '<hr/>' },
  'el-empty': { template: '<div class="el-empty-stub"></div>', props: ['description', 'imageSize'] },
  'el-alert': {
    template: '<div class="el-alert-stub">{{ title }}</div>',
    props: ['title', 'type', 'closable', 'showIcon'],
  },
}

// ==================== Helpers ====================

function mountAI() {
  return mount(InteractiveResult, { global: { stubs } })
}

/** 按按钮文本查找并点击 */
async function clickButton(wrapper: any, text: string) {
  const btn = wrapper.findAll('.el-btn').find((b: any) => b.text().includes(text))
  expect(btn, `按钮 "${text}" 应存在`).toBeTruthy()
  await btn!.trigger('click')
  await flushPromises()
}

// ==================== 测试 ====================

beforeEach(() => {
  vi.clearAllMocks()
  mockGetStatus.mockResolvedValue({ data: { services: { local_analysis: { status: 'available' } } } })
})

describe('服务状态检查', () => {
  it('local_analysis 状态可用时显示"服务可用"', async () => {
    const wrapper = mountAI()
    await flushPromises()

    expect((wrapper.vm as any).serviceStatus).toBe('available')
    expect(wrapper.text()).toContain('服务可用')
  })

  it('envelope 嵌套 data.data.services 也能解析', async () => {
    mockGetStatus.mockResolvedValue({
      data: { data: { services: { local_analysis: { status: 'degraded' } } } },
    })
    const wrapper = mountAI()
    await flushPromises()

    expect((wrapper.vm as any).serviceStatus).toBe('degraded')
    expect(wrapper.text()).toContain('加载中...')
  })

  it('无 services 字段时默认 available', async () => {
    mockGetStatus.mockResolvedValue({})
    const wrapper = mountAI()
    await flushPromises()

    expect((wrapper.vm as any).serviceStatus).toBe('available')
  })

  it('状态接口失败时显示 unavailable', async () => {
    mockGetStatus.mockRejectedValue(new Error('down'))
    const wrapper = mountAI()
    await flushPromises()

    expect((wrapper.vm as any).serviceStatus).toBe('unavailable')
  })

  it('切换 Tab 更新 activeTab（el-tabs v-model）', async () => {
    const wrapper = mountAI()
    await flushPromises()

    const tabs = wrapper.findComponent({ name: 'el-tabs' })
    tabs.vm.$emit('update:modelValue', 'forecast')
    await nextTick()
    expect((wrapper.vm as any).activeTab).toBe('forecast')
  })
})

describe('数据分析', () => {
  it('分析成功：嵌套结果扁平化并渲染描述列表', async () => {
    mockAnalyze.mockResolvedValue({
      data: {
        data: {
          analysis_type: '统计分析',
          result: { 收入: { 均值: 100, 峰值: 200 }, 备注: 'ok' },
        },
      },
    })
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.analyzeForm.description = '年度收入分析'

    await clickButton(wrapper, '开始分析')

    expect(mockAnalyze).toHaveBeenCalledWith({
      analysis_type: 'summary',
      description: '年度收入分析',
    })
    expect(vm.analyzeResult.analysis_type).toBe('统计分析')
    expect(vm.analyzeResult.flattened).toEqual({ 均值: 100, 峰值: 200, 备注: 'ok' })
    expect(mockMessage.success).toHaveBeenCalledWith('分析完成')
    expect(wrapper.text()).toContain('统计分析')
  })

  it('分析说明为空时传 undefined', async () => {
    mockAnalyze.mockResolvedValue({ result: 'done' })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '开始分析')
    expect(mockAnalyze).toHaveBeenCalledWith({ analysis_type: 'summary', description: undefined })
  })

  it('分析失败：提示错误', async () => {
    mockAnalyze.mockRejectedValue(new Error('fail'))
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '开始分析')
    expect(mockMessage.error).toHaveBeenCalledWith('分析失败')
    expect((wrapper.vm as any).analyzeLoading).toBe(false)
  })

  it('分析类型 radio-group v-model 更新', async () => {
    const wrapper = mountAI()
    await flushPromises()

    const group = wrapper.findComponent({ name: 'el-radio-group' })
    group.vm.$emit('update:modelValue', 'trend')
    await nextTick()
    expect((wrapper.vm as any).analyzeForm.type).toBe('trend')

    // 分析说明 el-input v-model 更新
    const descInput = wrapper.findAll('.el-input-stub')[0]
    await descInput.setValue('补充说明')
    expect((wrapper.vm as any).analyzeForm.description).toBe('补充说明')
  })

  it('flattenObject 各分支：null / 非对象 / 嵌套 / 数组值', async () => {
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any

    expect(vm.flattenObject(null)).toEqual({})
    expect(vm.flattenObject('text')).toEqual({})
    expect(vm.flattenObject({ a: { b: { c: 1 } }, d: [1, 2], e: 5 })).toEqual({
      c: 1,
      d: [1, 2],
      e: 5,
    })
  })
})

describe('趋势预测', () => {
  it('收入预测成功：predictions 数组直接渲染', async () => {
    mockForecastIncome.mockResolvedValue({
      data: { predictions: [{ year: 2026, value: 123.4 }] },
    })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '预测')

    expect(mockForecastIncome).toHaveBeenCalledWith(2)
    expect((wrapper.vm as any).forecastItems).toEqual([{ year: 2026, value: 123.4 }])
    expect(wrapper.text()).toContain('2026: 123.4')
    expect(mockMessage.success).toHaveBeenCalledWith('预测完成')
  })

  it('收入预测成功：predicted 对象转为条目数组', async () => {
    mockForecastIncome.mockResolvedValue({ data: { predicted: { '2027年': 555 } } })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '预测')
    expect((wrapper.vm as any).forecastItems).toEqual([{ label: '2027年', value: 555 }])
    expect(wrapper.text()).toContain('2027年: 555')
  })

  it('收入预测成功：无 predictions/predicted 时为空数组', async () => {
    mockForecastIncome.mockResolvedValue({ data: {} })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '预测')
    expect((wrapper.vm as any).forecastItems).toEqual([])
  })

  it('收入预测失败：提示错误', async () => {
    mockForecastIncome.mockRejectedValue(new Error('fail'))
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '预测')
    expect(mockMessage.error).toHaveBeenCalledWith('预测失败')
  })

  it('预测年数 el-select v-model 更新', async () => {
    const wrapper = mountAI()
    await flushPromises()

    const select = wrapper.findAllComponents({ name: 'el-select' })[0]
    select.vm.$emit('update:modelValue', 5)
    await nextTick()
    expect((wrapper.vm as any).forecastYears).toBe(5)
  })

  it('经费预测成功：predictions 数组', async () => {
    mockForecastFunds.mockResolvedValue({
      data: { predictions: [{ year: 2026, value: '80%' }] },
    })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '执行预测')
    expect((wrapper.vm as any).fundForecastItems).toEqual([{ year: 2026, value: '80%' }])
    expect(wrapper.text()).toContain('2026: 80%')
  })

  it('经费预测成功：返回对象整体作为预测源', async () => {
    mockForecastFunds.mockResolvedValue({ '2028年': '90%' })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '执行预测')
    expect((wrapper.vm as any).fundForecastItems).toEqual([{ label: '2028年', value: '90%' }])
  })

  it('经费预测失败：提示错误', async () => {
    mockForecastFunds.mockRejectedValue(new Error('fail'))
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '执行预测')
    expect(mockMessage.error).toHaveBeenCalledWith('预测失败')
  })
})

describe('异常检测', () => {
  it('空输入：使用随机演示数据并提示', async () => {
    mockDetectAnomalies.mockResolvedValue({
      data: {
        anomalies: [
          { index: 5, value: 99, is_anomaly: true },
          { index: 6, value: 1, is_anomaly: false },
        ],
        anomaly_count: 1,
      },
    })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '检测异常')

    expect(mockMessage.info).toHaveBeenCalledWith('未输入数据，已使用随机示例数据进行演示')
    const payload = mockDetectAnomalies.mock.calls[0][0]
    expect(payload.data).toHaveLength(20)
    expect(payload.value_field).toBe('value')
    expect(payload.method).toBe('statistical')
    expect(payload.contamination).toBe(0.05)

    const vm = wrapper.vm as any
    expect(vm.anomalyColumns).toEqual(['index', 'value'])
    expect(mockMessage.success).toHaveBeenCalledWith('检测完成：发现 1 个异常')
    expect(wrapper.text()).toContain('异常检测结果')
  })

  it('合法 JSON 数组输入：直接作为检测数据', async () => {
    mockDetectAnomalies.mockResolvedValue({ data: { anomalies: [], anomaly_count: 0 } })
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.anomalyInput = '[{"value": 10}, {"value": 20}]'

    await clickButton(wrapper, '检测异常')

    const payload = mockDetectAnomalies.mock.calls[0][0]
    expect(payload.data).toEqual([{ value: 10 }, { value: 20 }])
    // 无异常时渲染 el-empty，成功消息使用 ?? 'N/A' 分支前值
    expect(mockMessage.success).toHaveBeenCalledWith('检测完成：发现 0 个异常')
    expect(wrapper.find('.el-empty-stub').exists()).toBe(true)
  })

  it('合法 JSON 非数组输入：包装为数组', async () => {
    mockDetectAnomalies.mockResolvedValue({ data: {} })
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.anomalyInput = '{"value": 7}'

    await clickButton(wrapper, '检测异常')
    expect(mockDetectAnomalies.mock.calls[0][0].data).toEqual([{ value: 7 }])
    // anomaly_count 缺省时消息显示 N/A
    expect(mockMessage.success).toHaveBeenCalledWith('检测完成：发现 N/A 个异常')
  })

  it('非法 JSON 输入：提示格式错误并中断', async () => {
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.anomalyInput = 'not-json'

    await clickButton(wrapper, '检测异常')

    expect(mockMessage.error).toHaveBeenCalledWith('数据格式错误，请检查JSON格式')
    expect(mockDetectAnomalies).not.toHaveBeenCalled()
    expect(vm.anomalyLoading).toBe(false)
  })

  it('检测接口失败：提示错误', async () => {
    mockDetectAnomalies.mockRejectedValue(new Error('fail'))
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '检测异常')
    expect(mockMessage.error).toHaveBeenCalledWith('异常检测失败')
  })

  it('检测方式 el-select 与敏感度 el-slider v-model 更新', async () => {
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any

    const selects = wrapper.findAllComponents({ name: 'el-select' })
    // 第二个 select 是检测方式
    selects[1].vm.$emit('update:modelValue', 'zscore')
    await nextTick()
    expect(vm.anomalyForm.method).toBe('zscore')

    const slider = wrapper.findComponent({ name: 'el-slider' })
    slider.vm.$emit('update:modelValue', 30)
    await nextTick()
    expect(vm.anomalyForm.contamination).toBe(30)
  })

  it('数据输入 textarea v-model 更新', async () => {
    const wrapper = mountAI()
    await flushPromises()

    const inputs = wrapper.findAll('.el-input-stub')
    // 第二个输入框是异常检测数据输入
    await inputs[1].setValue('[{"value":1}]')
    expect((wrapper.vm as any).anomalyInput).toBe('[{"value":1}]')
  })
})

describe('智能推荐', () => {
  it('村庄ID为空：警告并中断', async () => {
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.recommendVillageId = 0

    await clickButton(wrapper, '推荐项目')
    expect(mockMessage.warning).toHaveBeenCalledWith('请输入村庄ID')
    expect(mockRecommendProjects).not.toHaveBeenCalled()
  })

  it('推荐成功：渲染推荐列表与评分', async () => {
    mockRecommendProjects.mockResolvedValue({
      data: { items: [{ name: '道路硬化项目', score: 9.126 }] },
    })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '推荐项目')

    expect(mockRecommendProjects).toHaveBeenCalledWith(1, 5)
    expect((wrapper.vm as any).recommendResults).toHaveLength(1)
    expect(wrapper.text()).toContain('道路硬化项目')
    expect(wrapper.text()).toContain('9.1')
  })

  it('推荐成功：items 非数组时置空', async () => {
    mockRecommendProjects.mockResolvedValue({ data: { items: 'not-array' } })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '推荐项目')
    expect((wrapper.vm as any).recommendResults).toEqual([])
  })

  it('推荐成功：响应本身为数组（|| data 分支）', async () => {
    mockRecommendProjects.mockResolvedValue([{ title: '水利项目' }])
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '推荐项目')
    expect((wrapper.vm as any).recommendResults).toEqual([{ title: '水利项目' }])
    expect(wrapper.text()).toContain('水利项目')
  })

  it('推荐失败：提示错误', async () => {
    mockRecommendProjects.mockRejectedValue(new Error('fail'))
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '推荐项目')
    expect(mockMessage.error).toHaveBeenCalledWith('推荐失败')
  })

  it('系统推荐成功：渲染优先级标签', async () => {
    mockGetRecommendations.mockResolvedValue({
      data: {
        recommendations: [
          { priority: 'high', content: '尽快审批积压项目' },
          { priority: 'medium', content: '关注资金使用进度' },
          { priority: 'low', title: '常规巡检' },
        ],
      },
    })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '获取系统建议')

    expect(mockGetRecommendations).toHaveBeenCalledWith({ context: {} })
    expect((wrapper.vm as any).systemRecommendations).toHaveLength(3)
    expect(wrapper.text()).toContain('尽快审批积压项目')
    expect(mockMessage.success).toHaveBeenCalledWith('获取推荐成功')
  })

  it('系统推荐：非数组时置空；失败时提示错误', async () => {
    mockGetRecommendations.mockResolvedValue({ data: { recommendations: 'x' } })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '获取系统建议')
    expect((wrapper.vm as any).systemRecommendations).toEqual([])

    mockGetRecommendations.mockRejectedValue(new Error('fail'))
    await clickButton(wrapper, '获取系统建议')
    expect(mockMessage.error).toHaveBeenCalledWith('获取推荐失败')
  })

  it('村庄ID el-input-number 与推荐数 el-select v-model 更新', async () => {
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any

    const inputNumber = wrapper.findComponent({ name: 'el-input-number' })
    inputNumber.vm.$emit('update:modelValue', 42)
    await nextTick()
    expect(vm.recommendVillageId).toBe(42)

    const selects = wrapper.findAllComponents({ name: 'el-select' })
    // 第三个 select 是推荐数
    selects[2].vm.$emit('update:modelValue', 10)
    await nextTick()
    expect(vm.recommendLimit).toBe(10)
  })
})

describe('NLP 查询', () => {
  it('空查询：警告并中断', async () => {
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '查询')
    expect(mockMessage.warning).toHaveBeenCalledWith('请输入查询内容')
    expect(mockNlpQuery).not.toHaveBeenCalled()
  })

  it('查询成功：渲染答案并写入历史', async () => {
    mockNlpQuery.mockResolvedValue({ data: { answer: '李家村人均收入最高' } })
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any

    const input = wrapper.findAll('.el-input-stub')[2]
    await input.setValue('哪个村庄人均收入最高？')
    await clickButton(wrapper, '查询')

    expect(mockNlpQuery).toHaveBeenCalledWith('哪个村庄人均收入最高？')
    expect(vm.nlpResult.answer).toBe('李家村人均收入最高')
    expect(vm.nlpHistory).toEqual(['哪个村庄人均收入最高？'])
    expect(wrapper.text()).toContain('李家村人均收入最高')
    expect(wrapper.text()).toContain('查询历史')
  })

  it('回车触发查询（@keyup.enter）', async () => {
    mockNlpQuery.mockResolvedValue({ result: 'r' })
    const wrapper = mountAI()
    await flushPromises()

    const input = wrapper.findAll('.el-input-stub')[2]
    await input.setValue('项目总数是多少')
    await input.trigger('keyup', { key: 'Enter' })
    await flushPromises()

    expect(mockNlpQuery).toHaveBeenCalledWith('项目总数是多少')
  })

  it('历史记录超过10条时截断', async () => {
    mockNlpQuery.mockResolvedValue({ answer: 'a' })
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.nlpHistory = ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q10']
    vm.nlpForm.query = 'q11'

    await vm.runNlpQuery()
    expect(vm.nlpHistory).toHaveLength(10)
    expect(vm.nlpHistory[0]).toBe('q11')
  })

  it('点击历史标签回填查询框', async () => {
    mockNlpQuery.mockResolvedValue({ answer: 'a' })
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.nlpForm.query = '历史问题'
    await vm.runNlpQuery()
    await nextTick()

    const historyTag = wrapper.find('.history-block .el-tag-stub')
    await historyTag.trigger('click')
    expect(vm.nlpForm.query).toBe('历史问题')
  })

  it('查询失败：提示错误', async () => {
    mockNlpQuery.mockRejectedValue(new Error('fail'))
    const wrapper = mountAI()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.nlpForm.query = '查询失败的情况'

    await vm.runNlpQuery()
    expect(mockMessage.error).toHaveBeenCalledWith('查询失败')
    expect(vm.nlpLoading).toBe(false)
  })
})

// ==================== 分支覆盖率补测 ====================

describe('分支补测：script 零分支', () => {
  it('服务状态：local_analysis.status 缺失时回退 available（367 || 右侧）', async () => {
    mockGetStatus.mockResolvedValue({ data: { services: { local_analysis: {} } } })
    const wrapper = mountAI()
    await flushPromises()

    expect((wrapper.vm as any).serviceStatus).toBe('available')
  })

  it('数据分析：无 result 字段时 flattenObject 回退 inner 自身（388 || inner）', async () => {
    mockAnalyze.mockResolvedValue({ data: { data: { analysis_type: '概览', 备注: 'x' } } })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '开始分析')
    const vm = wrapper.vm as any
    expect(vm.analyzeResult.analysis_type).toBe('概览')
    expect(vm.analyzeResult.flattened).toEqual({ analysis_type: '概览', 备注: 'x' })
  })

  it('数据分析：响应为 null 时 flattenObject 回退空对象（388 || {}、384 ?? 右侧）', async () => {
    mockAnalyze.mockResolvedValue(null)
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '开始分析')
    expect((wrapper.vm as any).analyzeResult.flattened).toEqual({})
    expect(mockMessage.success).toHaveBeenCalledWith('分析完成')
  })

  it('收入预测：响应无 data 包装时回退 response 本身（403 ?? 右侧）', async () => {
    mockForecastIncome.mockResolvedValue({ predictions: [{ year: 2031, value: 42 }] })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '预测')
    expect((wrapper.vm as any).forecastItems).toEqual([{ year: 2031, value: 42 }])
    expect(wrapper.text()).toContain('2031: 42')
  })

  it('经费预测：响应为 null 时预测源回退空对象（424 || {} 右侧）', async () => {
    mockForecastFunds.mockResolvedValue(null)
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '执行预测')
    expect((wrapper.vm as any).fundForecastItems).toEqual([])
    expect(mockMessage.success).toHaveBeenCalledWith('预测完成')
  })

  it('异常检测：响应无 data 包装时回退 response 本身（464 ?? 右侧）', async () => {
    mockDetectAnomalies.mockResolvedValue({
      anomalies: [{ index: 1, value: 5, is_anomaly: false }],
      anomaly_count: 0,
    })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '检测异常')
    const vm = wrapper.vm as any
    expect(vm.anomalyResult.anomaly_count).toBe(0)
    expect(vm.anomalyColumns).toEqual(['index', 'value'])
    expect(mockMessage.success).toHaveBeenCalledWith('检测完成：发现 0 个异常')
  })

  it('项目推荐：data.data.items 嵌套时取内层 items（488 首操作数为真）', async () => {
    mockRecommendProjects.mockResolvedValue({
      data: { data: { items: [{ name: '嵌套推荐项目', score: 8 }] } },
    })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '推荐项目')
    expect((wrapper.vm as any).recommendResults).toEqual([{ name: '嵌套推荐项目', score: 8 }])
    expect(wrapper.text()).toContain('嵌套推荐项目')
  })

  it('项目推荐：响应为 null 时逐项回退至空数组（488 || [] 右侧）', async () => {
    mockRecommendProjects.mockResolvedValue(null)
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '推荐项目')
    expect((wrapper.vm as any).recommendResults).toEqual([])
    expect(mockMessage.success).toHaveBeenCalledWith('推荐完成')
  })

  it('系统推荐：data.data.recommendations 嵌套时取内层（504 首操作数为真）', async () => {
    mockGetRecommendations.mockResolvedValue({
      data: { data: { recommendations: [{ priority: 'low', content: '嵌套系统建议' }] } },
    })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '获取系统建议')
    expect((wrapper.vm as any).systemRecommendations).toHaveLength(1)
    expect(wrapper.text()).toContain('嵌套系统建议')
  })

  it('系统推荐：响应为 null 时回退空数组（503 ?? 右侧、504 || [] 右侧）', async () => {
    mockGetRecommendations.mockResolvedValue(null)
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '获取系统建议')
    expect((wrapper.vm as any).systemRecommendations).toEqual([])
    expect(mockMessage.success).toHaveBeenCalledWith('获取推荐成功')
  })
})

describe('分支补测：template 零分支', () => {
  it('异常标记列：is_anomaly=false 渲染"否"（156 三元否侧）', async () => {
    mockDetectAnomalies.mockResolvedValue({
      data: { anomalies: [{ index: 6, value: 1, is_anomaly: false }], anomaly_count: 0 },
    })
    const wrapper = mount(InteractiveResult, {
      global: {
        stubs: {
          ...stubs,
          'el-table-column': {
            template: '<td><slot :row="rowData" /></td>',
            props: ['prop', 'label', 'width', 'type'],
            setup() {
              return { rowData: { index: 6, value: 1, is_anomaly: false } }
            },
          },
        },
      },
    })
    await flushPromises()

    await clickButton(wrapper, '检测异常')
    expect(wrapper.find('table .el-tag-stub').text()).toBe('否')
  })

  it('推荐项无 name/title 时回退"推荐N"占位（200 模板字符串分支）', async () => {
    mockRecommendProjects.mockResolvedValue([{ score: 7.5 }])
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '推荐项目')
    expect(wrapper.text()).toContain('推荐1')
    expect(wrapper.text()).toContain('7.5')
  })

  it('系统推荐无 priority 时显示 info；字符串条目直接渲染（232/234 || 右侧）', async () => {
    mockGetRecommendations.mockResolvedValue({
      data: { recommendations: [{ content: '普通建议内容' }, '字符串建议'] },
    })
    const wrapper = mountAI()
    await flushPromises()

    await clickButton(wrapper, '获取系统建议')
    expect(wrapper.text()).toContain('info')
    expect(wrapper.text()).toContain('字符串建议')
  })
})
