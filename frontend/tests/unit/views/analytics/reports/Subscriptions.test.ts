/**
 * views/analytics/reports/Subscriptions.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：报表类型/周期字典映射两侧、状态切换两分支、立即生成（含 setTimeout 回调）、
 * 编辑回填、删除确认/取消、保存全分支（新建/编辑/stale id/校验失败/formRef 空/
 * resetFields 可选链空值）、模板内联事件与全部 v-model 处理器。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

// vi.mock 工厂提升求值，引用对象须先放入 vi.hoisted 初始化
const { ElMessage, confirmMock } = vi.hoisted(() => {
  return {
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
    confirmMock: vi.fn(),
  }
})

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

import Subscriptions from '@/views/analytics/reports/Subscriptions.vue'

// el-table-column 注入两行样本：已知/未知 reportType 与 frequency 各一侧，
// status active/paused 各一侧，覆盖模板中字典兜底与状态渲染的两类分支
const rowA = {
  id: '1',
  name: '月度帮扶村统计',
  reportType: 'village_stats',
  frequency: 'monthly',
  nextRun: '2026-05-01 08:00',
  status: 'active',
  lastRun: '2026-04-01 08:00',
}
const rowB = {
  id: '2',
  name: '特殊周期订阅',
  reportType: 'unknown_x',
  frequency: 'yearly',
  nextRun: '-',
  status: 'paused',
  lastRun: '-',
}

function mountComp() {
  // el-card/el-dialog 需渲染具名插槽（header/footer）；el-table-column 注入双样本行
  return mount(Subscriptions, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot name="header" /><slot /></div>',
        },
        'el-dialog': {
          name: 'ElDialog',
          template: '<div class="el-dialog-stub"><slot /><slot name="footer" /></div>',
          emits: ['update:modelValue'],
        },
        'el-table-column': {
          name: 'ElTableColumn',
          template: '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /></div>',
          data() {
            return { rowA: { ...rowA }, rowB: { ...rowB } }
          },
        },
      },
    },
  })
}

function findBtn(wrapper: any, text: string) {
  const btn = wrapper.findAll('el-button-stub').find((b: any) => b.text().includes(text))
  expect(btn, `按钮「${text}」`).toBeTruthy()
  return btn!
}

beforeEach(() => {
  vi.resetAllMocks()
  confirmMock.mockResolvedValue(undefined)
})

afterEach(() => {
  vi.useRealTimers()
})

describe('挂载渲染与字典映射', () => {
  it('挂载渲染订阅表：已知/未知 reportType 与 frequency 两侧兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('报表订阅管理')
    expect(text).toContain('帮扶村统计') // 已知 reportType → 映射文案
    expect(text).toContain('unknown_x') // 未知 reportType → 原样透传
    expect(text).toContain('每月') // 已知 frequency → frequencyMap
    expect(text).toContain('yearly') // 未知 frequency → || row.frequency 兜底
  })

  it('历史记录 success/error 两态均渲染（模板三元两侧）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('成功')
    expect(text).toContain('失败')
    expect(text).toContain('数据库连接超时，已重试')
  })

  it('getReportTypeLabel 全映射与未知透传', async () => {
    const wrapper = mountComp()
    const vm = wrapper.vm as any
    expect(vm.getReportTypeLabel('village_stats')).toBe('帮扶村统计')
    expect(vm.getReportTypeLabel('school_stats')).toBe('学校帮扶')
    expect(vm.getReportTypeLabel('project_progress')).toBe('项目进度')
    expect(vm.getReportTypeLabel('fund_usage')).toBe('经费使用')
    expect(vm.getReportTypeLabel('comprehensive')).toBe('综合汇总')
    expect(vm.getReportTypeLabel('custom_type')).toBe('custom_type')
  })

  it('getReportTypeTag 全映射与未知兜底 info', async () => {
    const wrapper = mountComp()
    const vm = wrapper.vm as any
    expect(vm.getReportTypeTag('village_stats')).toBe('success')
    expect(vm.getReportTypeTag('school_stats')).toBe('warning')
    expect(vm.getReportTypeTag('project_progress')).toBe('primary')
    expect(vm.getReportTypeTag('fund_usage')).toBe('danger')
    expect(vm.getReportTypeTag('comprehensive')).toBe('info')
    expect(vm.getReportTypeTag('whatever')).toBe('info')
  })

  it('handleStatusChange：active → 启用，其他 → 暂停', async () => {
    const wrapper = mountComp()
    const vm = wrapper.vm as any
    vm.handleStatusChange({ name: 'A', status: 'active' })
    expect(ElMessage.success).toHaveBeenCalledWith('已启用订阅：A')
    vm.handleStatusChange({ name: 'B', status: 'paused' })
    expect(ElMessage.success).toHaveBeenCalledWith('已暂停订阅：B')
  })
})

describe('操作列：立即生成 / 编辑 / 删除', () => {
  it('handleRunNow：先 info 提示，1500ms 后更新 lastRun 并前插历史记录', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vi.useFakeTimers()
    const row = vm.subscriptions[0]
    const before = vm.historyRecords.length
    vm.handleRunNow(row)
    expect(ElMessage.info).toHaveBeenCalledWith('正在生成报表：月度帮扶村统计...')
    vi.advanceTimersByTime(1500)
    expect(ElMessage.success).toHaveBeenCalledWith('报表生成成功：月度帮扶村统计')
    expect(vm.historyRecords).toHaveLength(before + 1)
    expect(vm.historyRecords[0]).toMatchObject({
      name: '月度帮扶村统计',
      status: 'success',
      detail: '手动触发生成',
    })
    expect(row.lastRun).not.toBe('2026-04-01 08:00')
  })

  it('点击「立即生成」按钮 → 触发模板内联 handleRunNow(row)', async () => {
    const wrapper = mountComp()
    await flushPromises()
    vi.useFakeTimers()
    await findBtn(wrapper, '立即生成').trigger('click')
    expect(ElMessage.info).toHaveBeenCalledWith(expect.stringContaining('正在生成报表'))
    vi.advanceTimersByTime(1500)
    expect(ElMessage.success).toHaveBeenCalledWith(expect.stringContaining('报表生成成功'))
  })

  it('handleEdit：回填表单并打开对话框，标题切到「编辑订阅」', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(wrapper.findComponent({ name: 'ElDialog' }).attributes('title')).toBe('新增订阅')
    vm.handleEdit({ ...rowA })
    await nextTick() // 触发 editingId ? '编辑订阅' : '新增订阅' 真侧渲染
    expect(vm.editingId).toBe('1')
    expect(vm.form).toMatchObject({
      name: '月度帮扶村统计',
      reportType: 'village_stats',
      frequency: 'monthly',
    })
    expect(vm.showAddDialog).toBe(true)
    expect(wrapper.findComponent({ name: 'ElDialog' }).attributes('title')).toBe('编辑订阅')
  })

  it('handleDelete：确认 → 过滤该订阅并提示；取消 → 不删除', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const before = vm.subscriptions.length
    await vm.handleDelete({ ...rowA })
    expect(confirmMock).toHaveBeenCalledWith(
      '确定要删除订阅「月度帮扶村统计」吗？',
      '确认删除',
      expect.objectContaining({ type: 'warning' })
    )
    expect(vm.subscriptions).toHaveLength(before - 1)
    expect(vm.subscriptions.some((s: any) => s.id === '1')).toBe(false)
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')

    confirmMock.mockRejectedValueOnce(new Error('cancel'))
    const len = vm.subscriptions.length
    await vm.handleDelete({ id: '2', name: '周度项目进度报告' })
    expect(vm.subscriptions).toHaveLength(len) // catch 分支：取消删除
  })

  it('点击「编辑」「删除」按钮 → 触发模板内联 handleEdit/handleDelete', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await findBtn(wrapper, '编辑').trigger('click')
    expect(vm.showAddDialog).toBe(true)
    expect(vm.editingId).toBe('1')
    await findBtn(wrapper, '删除').trigger('click')
    await flushPromises()
    expect(confirmMock).toHaveBeenCalled()
  })
})

describe('handleSave 全分支', () => {
  it('formRef 为空 → 可选链短路直接返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.formRef = undefined
    vm.handleSave()
    expect(ElMessage.success).not.toHaveBeenCalled()
  })

  it('校验未通过 → 不写数据不提示', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const before = vm.subscriptions.length
    vm.formRef = { validate: (cb: any) => cb(false) }
    vm.handleSave()
    expect(vm.subscriptions).toHaveLength(before)
    expect(ElMessage.success).not.toHaveBeenCalled()
  })

  it('新建：push 新订阅并提示创建成功，关闭弹窗并 resetFields', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const resetFields = vi.fn()
    vm.formRef = { validate: (cb: any) => cb(true), resetFields }
    vm.form.name = '新订阅'
    vm.form.reportType = 'comprehensive'
    const before = vm.subscriptions.length
    vm.handleSave()
    expect(vm.subscriptions).toHaveLength(before + 1)
    const added = vm.subscriptions[vm.subscriptions.length - 1]
    expect(added).toMatchObject({ name: '新订阅', reportType: 'comprehensive', status: 'active' })
    expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
    expect(vm.showAddDialog).toBe(false)
    expect(vm.editingId).toBeNull()
    expect(resetFields).toHaveBeenCalled()
  })

  it('编辑（idx >= 0）：替换对应订阅并提示更新成功', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.formRef = { validate: (cb: any) => cb(true), resetFields: vi.fn() }
    vm.handleEdit({ ...rowA })
    vm.form.name = '改名后的订阅'
    vm.handleSave()
    const updated = vm.subscriptions.find((s: any) => s.id === '1')
    expect(updated.name).toBe('改名后的订阅')
    expect(ElMessage.success).toHaveBeenCalledWith('更新成功')
  })

  it('编辑 stale id（idx < 0）：仍提示更新成功但不替换任何行', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.formRef = { validate: (cb: any) => cb(true), resetFields: vi.fn() }
    vm.editingId = 'not-exists'
    const snapshot = vm.subscriptions.map((s: any) => ({ ...s }))
    vm.handleSave()
    expect(ElMessage.success).toHaveBeenCalledWith('更新成功')
    expect(vm.subscriptions).toEqual(snapshot)
  })

  it('resetFields 可选链空值分支：validate 回调前置空 formRef', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.formRef = {
      validate: (cb: any) => {
        vm.formRef = undefined // 回调执行到末尾 formRef.value?.resetFields() 时已为空
        cb(true)
      },
    }
    vm.handleSave()
    expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
    expect(vm.showAddDialog).toBe(false)
  })
})

describe('模板交互：内联处理器与 v-model', () => {
  it('点击「新增订阅」→ showAddDialog = true；点击「取消」→ false', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await findBtn(wrapper, '新增订阅').trigger('click')
    expect(vm.showAddDialog).toBe(true)
    await findBtn(wrapper, '取消').trigger('click')
    expect(vm.showAddDialog).toBe(false)
  })

  it('点击「保存」→ 触发 handleSave（提交前重新赋 formRef mock）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.formRef = { validate: (cb: any) => cb(true), resetFields: vi.fn() }
    vm.form.name = '按钮触发的新订阅'
    await findBtn(wrapper, '保存').trigger('click')
    expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
  })

  it('对话框与表单控件 v-model 全部触发 update:modelValue', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    dialog.vm.$emit('update:modelValue', true)
    expect(vm.showAddDialog).toBe(true)

    const inputs = wrapper.findAllComponents({ name: 'ElInput' })
    expect(inputs.length).toBeGreaterThanOrEqual(2)
    for (const c of inputs) c.vm.$emit('update:modelValue', '输入值')
    expect(vm.form.name).toBe('输入值')
    expect(vm.form.remark).toBe('输入值')

    const selects = wrapper.findAllComponents({ name: 'ElSelect' })
    expect(selects.length).toBe(2)
    selects[0].vm.$emit('update:modelValue', 'fund_usage')
    selects[1].vm.$emit('update:modelValue', 'quarterly')
    expect(vm.form.reportType).toBe('fund_usage')
    expect(vm.form.frequency).toBe('quarterly')

    const radios = wrapper.findAllComponents({ name: 'ElRadioGroup' })
    expect(radios.length).toBe(1)
    radios[0].vm.$emit('update:modelValue', 'self')
    expect(vm.form.scope).toBe('self')
    await nextTick()
  })

  it('状态列 el-switch 触发 change 与 update:modelValue', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const switches = wrapper.findAllComponents({ name: 'ElSwitch' })
    expect(switches.length).toBeGreaterThan(0)
    switches[0].vm.$emit('change', 'paused')
    expect(ElMessage.success).toHaveBeenCalledWith(expect.stringContaining('订阅'))
    switches[0].vm.$emit('update:modelValue', 'paused') // v-model 内联赋值处理器
    await nextTick()
  })
})
