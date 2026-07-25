/**
 * views/funds/Lifecycle.vue 覆盖率攻坚
 * 覆盖：七阶段步骤条全状态、七个页签面板分支、健康度卡片、全部处理器成功/失败/取消路径
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

// vi.mock 工厂会被提升到模块顶部注册，且在 import 链执行时求值；
// 直接引用下方的 const 会触发 TDZ 错误（Cannot access before initialization）。
// 因此所有被工厂引用的对象都放入 vi.hoisted 中先行初始化。
const { routeParams, mockPushSafe, ElMessage, confirmMock, api } = vi.hoisted(() => {
  return {
    routeParams: { projectId: '1' } as Record<string, string>,
    mockPushSafe: vi.fn(),
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
    confirmMock: vi.fn(),
    api: {
      getPhases: vi.fn(),
      advancePhase: vi.fn(),
      rollbackPhase: vi.fn(),
      initiate: vi.fn(),
      getReportTemplate: vi.fn(),
      lockBudget: vi.fn(),
      complianceCheck: vi.fn(),
      allocationPlan: vi.fn(),
      quotaLock: vi.fn(),
      transferLedger: vi.fn(),
      monitoringDeviation: vi.fn(),
      detectAnomalies: vi.fn(),
      createSettlement: vi.fn(),
      getPerformance: vi.fn(),
      getHealth: vi.fn(),
    },
  }
})

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: routeParams }),
}))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ pushSafe: mockPushSafe }),
  safeRouteParam: (v: any) => v,
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

vi.mock('@/api/fundLifecycle', () => ({ fundLifecycleApi: api }))

import Lifecycle from '@/views/funds/Lifecycle.vue'

const phasesFull = [
  { phase: 1, status: 'completed', completed_at: '2024-01-15T10:00:00', phase_label: '论证立项' },
  { phase: 2, status: 'in_progress', phase_label: '汇总审核' },
  { phase: 3, status: 'skipped', phase_label: '计划下达' },
  { phase: 4, status: 'not_started', phase_label: '军地对接' },
  { phase: 5, status: 'completed', completed_at: null, phase_label: '实施监管' },
]

const reportTpl = {
  project: { name: '产业路', type: '基建', budget: 100, leader: null },
  fund_summary: { total_planned: 80, fund_count: 3 },
}

function mountComp() {
  // setup.ts 的全局 el-* stub 默认不渲染插槽，需开启 renderStubDefaultSlot
  // 才能断言模板文本（按钮/卡片/页签内的内容）。
  // el-alert / el-page-header 未在全局 stub 列表中，且 element-plus 模块被 mock，
  // 真实组件无法解析——提供具名自定义 stub：alert 渲染 title，page-header 可触发 back。
  return mount(Lifecycle, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-alert': {
          template: '<div class="el-alert-stub">{{ title }}</div>',
          props: ['title'],
        },
        'el-page-header': {
          name: 'ElPageHeader',
          template: '<div class="el-page-header-stub"><slot name="content" /><slot /></div>',
          emits: ['back'],
        },
        // renderStubDefaultSlot 会让列作用域插槽以无 props 渲染（row 为 undefined 崩溃），
        // 自定义列 stub 注入样本行，让列模板三元表达式真实执行以覆盖语句
        'el-table-column': {
          name: 'ElTableColumn',
          template: '<div class="el-table-column-stub"><slot :row="row" /></div>',
          data() {
            return {
              row: {
                fund_name: '样例经费',
                type: '类型',
                message: '说明',
                severity: 'danger',
                budget_locked: true,
                status: 'danger',
              },
            }
          },
        },
      },
    },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  routeParams.projectId = '1'
  api.getPhases.mockResolvedValue({ phases: phasesFull, current_phase: 2 })
  api.getReportTemplate.mockResolvedValue(reportTpl)
  api.getHealth.mockResolvedValue({
    health_score: 85,
    details: {
      budget_execution: { score: 90 },
      payment_timeliness: { score: 70 },
      unknown_metric: { score: 55 },
    },
  })
})

describe('onMounted 与阶段加载', () => {
  it('有 projectId：加载阶段/报告模板/健康度全部分支', async () => {
    const wrapper = mountComp()
    await flushPromises()
    expect(api.getPhases).toHaveBeenCalledWith('1')
    expect(wrapper.vm.phases).toHaveLength(5)
    expect(wrapper.vm.currentPhase).toBe(2)
    expect(wrapper.vm.activeTab).toBe('phase2')
    expect(wrapper.vm.reportData?.project?.name).toBe('产业路')
    expect(wrapper.vm.healthData?.health_score).toBe(85)
    // 模板渲染：leader 为空 → 未指定；health 颜色 ≥80 分支；detailLabels 命中+回退
    await nextTick()
    expect(wrapper.text()).toContain('未指定')
  })

  it('无 projectId：onMounted 与 loadHealth 提前返回', async () => {
    routeParams.projectId = ''
    mountComp()
    await flushPromises()
    expect(api.getPhases).not.toHaveBeenCalled()
    expect(api.getHealth).not.toHaveBeenCalled()
  })

  it('getPhases 失败：错误提示（detail 与兜底文案）', async () => {
    api.getPhases.mockRejectedValue({ response: { data: { detail: '阶段错误' } } })
    api.getReportTemplate.mockRejectedValue(new Error('tpl'))
    mountComp()
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('阶段错误')

    api.getPhases.mockRejectedValue({})
    const w2 = mountComp()
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('加载阶段数据失败')
    expect(w2.vm.phases).toEqual([])
  })
})

describe('步骤条状态函数', () => {
  it('getStepStatus/getStepDesc 全分支（由模板 v-for 触发）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    expect(wrapper.vm.getStepStatus({ status: 'completed' })).toBe('success')
    expect(wrapper.vm.getStepStatus({ status: 'in_progress' })).toBe('process')
    expect(wrapper.vm.getStepStatus({ status: 'skipped' })).toBe('error')
    expect(wrapper.vm.getStepStatus({ status: 'not_started' })).toBe('wait')
    expect(wrapper.vm.getStepDesc({ status: 'completed', completed_at: '2024-01-15T00:00:00' })).toBe('2024-01-15')
    expect(wrapper.vm.getStepDesc({ status: 'completed', completed_at: null })).toBe('已完成')
    expect(wrapper.vm.getStepDesc({ status: 'in_progress' })).toBe('进行中')
    expect(wrapper.vm.getStepDesc({ status: 'not_started' })).toBe('')
  })

  it('当前阶段 not_started 时按钮文案为开始当前阶段', async () => {
    api.getPhases.mockResolvedValue({ phases: phasesFull, current_phase: 4 })
    const wrapper = mountComp()
    await flushPromises()
    await nextTick()
    expect(wrapper.text()).toContain('开始当前阶段')
  })
})

describe('推进/退回', () => {
  it('handleAdvance 确认后成功推进', async () => {
    confirmMock.mockResolvedValue(true)
    api.advancePhase.mockResolvedValue({ message: '已推进' })
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.handleAdvance()
    expect(api.advancePhase).toHaveBeenCalledWith('1')
    expect(ElMessage.success).toHaveBeenCalledWith('已推进')
    expect(api.getPhases).toHaveBeenCalledTimes(2)
  })

  it('handleAdvance 取消不报错；异常走 detail 与兜底', async () => {
    confirmMock.mockRejectedValue('cancel')
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.handleAdvance()
    expect(ElMessage.error).not.toHaveBeenCalled()

    confirmMock.mockResolvedValue(true)
    api.advancePhase.mockRejectedValue({ response: { data: { detail: '不可推进' } } })
    await wrapper.vm.handleAdvance()
    expect(ElMessage.error).toHaveBeenCalledWith('不可推进')

    api.advancePhase.mockRejectedValue({})
    await wrapper.vm.handleAdvance()
    expect(ElMessage.error).toHaveBeenCalledWith('推进失败')
  })

  it('handleRollback 成功与失败', async () => {
    confirmMock.mockResolvedValue(true)
    api.rollbackPhase.mockResolvedValue({})
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.handleRollback()
    expect(ElMessage.success).toHaveBeenCalledWith('操作成功')

    api.rollbackPhase.mockRejectedValue({ response: { data: { detail: '不可退回' } } })
    await wrapper.vm.handleRollback()
    expect(ElMessage.error).toHaveBeenCalledWith('不可退回')
  })
})

describe('阶段1-2 处理器', () => {
  it('handleInitiate 成功：写入报告数据并刷新阶段', async () => {
    api.initiate.mockResolvedValue({})
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.handleInitiate()
    expect(api.initiate).toHaveBeenCalledWith('1')
    expect(ElMessage.success).toHaveBeenCalledWith('论证立项已启动')
    expect(api.getPhases).toHaveBeenCalledTimes(2)
  })

  it('handleInitiate 失败', async () => {
    api.initiate.mockRejectedValue({})
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.handleInitiate()
    expect(ElMessage.error).toHaveBeenCalledWith('操作失败')
  })

  it('handleLockBudget 成功与失败', async () => {
    api.lockBudget.mockResolvedValue({ message: '预算基线已锁定' })
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.handleLockBudget()
    expect(ElMessage.success).toHaveBeenCalledWith('预算基线已锁定')
    api.lockBudget.mockRejectedValue({ response: { data: { detail: '锁定受限' } } })
    await wrapper.vm.handleLockBudget()
    expect(ElMessage.error).toHaveBeenCalledWith('锁定受限')
  })

  it('handleComplianceCheck 成功（含问题表三分支）与失败', async () => {
    api.complianceCheck.mockResolvedValue({
      compliant: false,
      total_issues: 3,
      issues: [
        { fund_name: 'a', type: 't', message: 'm', severity: 'danger' },
        { fund_name: 'b', type: 't', message: 'm', severity: 'warning' },
        { fund_name: 'c', type: 't', message: 'm', severity: 'other' },
      ],
    })
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.handleComplianceCheck()
    await nextTick()
    expect(wrapper.vm.complianceResult.total_issues).toBe(3)
    expect(wrapper.text()).toContain('发现 3 个问题')

    api.complianceCheck.mockResolvedValue({ compliant: true, issues: [] })
    await wrapper.vm.handleComplianceCheck()
    await nextTick()
    expect(wrapper.text()).toContain('合规性校验通过')

    api.complianceCheck.mockRejectedValue({})
    await wrapper.vm.handleComplianceCheck()
    expect(ElMessage.error).toHaveBeenCalledWith('校验失败')
  })
})

describe('阶段3-7 处理器', () => {
  it('loadAllocationPlan 成功（锁定/未锁定行）与失败', async () => {
    api.allocationPlan.mockResolvedValue({
      items: [
        { fund_id: 1, fund_name: '经费A', budget_locked: true },
        { fund_id: 2, fund_name: '经费B', budget_locked: false },
      ],
    })
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.loadAllocationPlan()
    await nextTick()
    expect(wrapper.vm.allocationItems).toHaveLength(2)

    api.allocationPlan.mockRejectedValue({})
    await wrapper.vm.loadAllocationPlan()
    expect(ElMessage.error).toHaveBeenCalledWith('加载失败')
  })

  it('handleQuotaLock 成功重载与失败', async () => {
    api.quotaLock.mockResolvedValue({ message: '额度已锁定' })
    api.allocationPlan.mockResolvedValue({ items: [] })
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.handleQuotaLock(7)
    expect(api.quotaLock).toHaveBeenCalledWith(7)
    expect(ElMessage.success).toHaveBeenCalledWith('额度已锁定')
    expect(api.allocationPlan).toHaveBeenCalled()

    api.quotaLock.mockRejectedValue({ response: { data: { detail: '额度不足' } } })
    await wrapper.vm.handleQuotaLock(7)
    expect(ElMessage.error).toHaveBeenCalledWith('额度不足')
  })

  it('loadTransferLedger 成功与失败', async () => {
    api.transferLedger.mockResolvedValue({
      total_military_to_local: 10,
      total_local_to_military: 4,
      net_transfer: 6,
    })
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.loadTransferLedger()
    await nextTick()
    expect(wrapper.vm.ledgerData.net_transfer).toBe(6)

    api.transferLedger.mockRejectedValue({})
    await wrapper.vm.loadTransferLedger()
    expect(ElMessage.error).toHaveBeenCalledWith('加载失败')
  })

  it('loadDeviation 成功（danger/warning/正常行）与失败', async () => {
    api.monitoringDeviation.mockResolvedValue({
      deviations: [
        { fund_name: 'a', status: 'danger' },
        { fund_name: 'b', status: 'warning' },
        { fund_name: 'c', status: 'ok' },
      ],
    })
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.loadDeviation()
    await nextTick()
    expect(wrapper.vm.deviations).toHaveLength(3)

    api.monitoringDeviation.mockRejectedValue({})
    await wrapper.vm.loadDeviation()
    expect(ElMessage.error).toHaveBeenCalledWith('加载失败')
  })

  it('handleDetect 成功与失败', async () => {
    api.detectAnomalies.mockResolvedValue({ message: '检测完成' })
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.handleDetect()
    await nextTick()
    expect(wrapper.vm.detectResult).toBe('检测完成')
    expect(ElMessage.success).toHaveBeenCalledWith('检测完成')

    api.detectAnomalies.mockRejectedValue({})
    await wrapper.vm.handleDetect()
    expect(ElMessage.error).toHaveBeenCalledWith('检测失败')
  })

  it('handleCreateSettlement 成功写绩效与失败', async () => {
    api.createSettlement.mockResolvedValue({ message: '决算报告已生成' })
    api.getPerformance.mockResolvedValue({
      budget_summary: { total_budget: 100, total_used: 60, execution_rate: 60 },
      anomaly_summary: { resolution_rate: 80 },
    })
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.handleCreateSettlement()
    await nextTick()
    expect(wrapper.vm.performanceData.budget_summary.execution_rate).toBe(60)

    api.createSettlement.mockRejectedValue({})
    await wrapper.vm.handleCreateSettlement()
    expect(ElMessage.error).toHaveBeenCalledWith('生成失败')
  })

  it('loadHealth 失败提示', async () => {
    api.getHealth.mockRejectedValue({ response: { data: { detail: '无数据' } } })
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.loadHealth()
    expect(ElMessage.error).toHaveBeenCalledWith('无数据')
  })
})

describe('导航按钮', () => {
  it('四个 pushSafe 内联处理器', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await nextTick()
    const texts = ['管理划转凭证', '合同管理', '查看异常列表', '查看详情']
    const expects = [
      '/funds/transfer-vouchers?project_id=1',
      '/funds/contracts?project_id=1',
      '/funds/anomalies?project_id=1',
      '/funds/settlement/1',
    ]
    const btns = wrapper.findAll('el-button-stub')
    expect(btns.length).toBeGreaterThan(0)
    for (let i = 0; i < texts.length; i++) {
      const target = btns.find((b) => b.text().includes(texts[i]))
      expect(target, texts[i]).toBeTruthy()
      await target!.trigger('click')
      expect(mockPushSafe).toHaveBeenCalledWith(expects[i])
    }
    // 页头返回
    const pageHeader = wrapper.findComponent({ name: 'ElPageHeader' })
    if (pageHeader.exists()) {
      await pageHeader.vm.$emit('back')
      expect(mockPushSafe).toHaveBeenCalledWith('/funds')
    }
  })
})
