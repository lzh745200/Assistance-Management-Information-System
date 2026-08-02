/**
 * views/report/List.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：typeLabel/freqLabel 映射与兜底、loadList（items/data.items/数组/失败）、openDialog（新建/编辑）、
 * handleSave（无 formRef/校验失败/创建成功/更新成功/失败）、toggle/generate/download/delete 成功失败、
 * 模板：新增按钮、表格行（开关 change、四操作按钮）、空态、对话框表单与 footer。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

const {
  ElMessage,
  confirmMock,
  validateMock,
  reportApiMock,
} = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  confirmMock: vi.fn(),
  validateMock: vi.fn(),
  reportApiMock: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    toggle: vi.fn(),
    generate: vi.fn(),
    download: vi.fn(),
  },
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

vi.mock('@/api/report', () => ({ reportApi: reportApiMock }))

import ReportList from '@/views/report/List.vue'

const rowA = { id: 1, name: '月度汇总', report_type: 'comprehensive', format: 'xlsx', frequency: 'monthly', is_active: true, last_sent_at: '2024-06-01' }
const rowB = { id: 2, name: '村报表', report_type: 'supported_villages', format: '', frequency: 'weekly', is_active: false, last_sent_at: '' }
const rowC = { id: 3, name: '特殊报表', report_type: 'weird_type', format: 'pdf', frequency: 'weird', is_active: true, last_sent_at: '2024-06-02' }

function mountComp() {
  return mount(ReportList, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot name="header" /><slot /></div>',
        },
        'el-table': { name: 'ElTable', template: '<div class="el-table-stub"><slot /></div>' },
        'el-table-column': {
          name: 'ElTableColumn',
          template:
            '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /><slot :row="rowC" /></div>',
          data() {
            return { rowA, rowB, rowC }
          },
        },
        'el-dialog': {
          name: 'ElDialog',
          template: '<div class="el-dialog-stub"><slot /><slot name="footer" /></div>',
          emits: ['update:modelValue'],
        },
        'el-form': {
          name: 'ElForm',
          template: '<div class="el-form-stub"><slot /></div>',
          methods: { validate: () => validateMock() },
        },
        'el-form-item': {
          name: 'ElFormItem',
          template: '<div class="el-form-item-stub"><slot /></div>',
        },
        'el-input': {
          name: 'ElInput',
          template: '<div class="el-input-stub" />',
          emits: ['update:modelValue'],
        },
        'el-select': {
          name: 'ElSelect',
          template: '<div class="el-select-stub"><slot /></div>',
          emits: ['update:modelValue'],
        },
        'el-radio-group': {
          name: 'ElRadioGroup',
          template: '<div class="el-radio-group-stub"><slot /></div>',
          emits: ['update:modelValue'],
        },
        'el-input-number': {
          name: 'ElInputNumber',
          template: '<div class="el-input-number-stub" />',
          emits: ['update:modelValue'],
        },
        'el-switch': {
          name: 'ElSwitch',
          props: ['modelValue'],
          template:
            '<button class="el-switch-stub" @click="$emit(\'change\', !modelValue)" />',
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
  reportApiMock.list.mockResolvedValue({ items: [rowA, rowB, rowC] })
  reportApiMock.create.mockResolvedValue({})
  reportApiMock.update.mockResolvedValue({})
  reportApiMock.delete.mockResolvedValue({})
  reportApiMock.toggle.mockResolvedValue({})
  reportApiMock.generate.mockResolvedValue({})
  reportApiMock.download.mockResolvedValue(undefined)
  validateMock.mockResolvedValue(true)
  confirmMock.mockResolvedValue('confirm')
})

describe('挂载与列表', () => {
  it('onMounted：items 形态加载；表格渲染（typeLabel/freqLabel/format 兜底）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(reportApiMock.list).toHaveBeenCalled()
    expect(vm.subscriptions).toHaveLength(3)
    expect(vm.loading).toBe(false)
    const text = wrapper.text()
    expect(text).toContain('综合报表')
    expect(text).toContain('帮扶村报表')
    expect(text).toContain('weird_type') // 未知类型原样
    expect(text).toContain('每月')
    expect(text).toContain('每周')
    expect(text).toContain('weird') // 未知频率原样
    expect(text).toContain('xlsx') // rowB format 空 → 默认 xlsx
  })

  it('data.items / 裸数组 / null / 失败四种形态', async () => {
    reportApiMock.list.mockResolvedValue({ data: { items: [rowA] } })
    let wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).subscriptions).toHaveLength(1)

    reportApiMock.list.mockResolvedValue([rowB])
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).subscriptions).toHaveLength(1)

    reportApiMock.list.mockResolvedValue(null)
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).subscriptions).toEqual([])

    reportApiMock.list.mockRejectedValue(new Error('net'))
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).subscriptions).toEqual([])
    expect((wrapper.vm as any).loading).toBe(false)
  })

  it('空列表 → el-empty；「新增订阅」按钮', async () => {
    reportApiMock.list.mockResolvedValue({ items: [] })
    const wrapper = mountComp()
    await flushPromises()
    expect(wrapper.find('.el-empty-stub').exists()).toBe(true)
    await findBtn(wrapper, '新增订阅').trigger('click')
    const vm = wrapper.vm as any
    expect(vm.dialogVisible).toBe(true)
    expect(vm.editingId).toBeNull()
    expect(vm.form.name).toBe('')
  })
})

describe('openDialog 与 handleSave', () => {
  it('openDialog：编辑模式回填；编辑按钮点击', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await findBtn(wrapper, '编辑').trigger('click') // rowA
    expect(vm.editingId).toBe(1)
    expect(vm.form.name).toBe('月度汇总')
    expect(vm.dialogVisible).toBe(true)
  })

  it('handleSave：formRef 缺失 → 早退；校验失败 → 早退', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.formRef = undefined
    await vm.handleSave()
    expect(reportApiMock.create).not.toHaveBeenCalled()

    vm.formRef = { validate: validateMock }
    validateMock.mockResolvedValueOnce(false)
    await vm.handleSave()
    expect(reportApiMock.create).not.toHaveBeenCalled()
  })

  it('handleSave：新建成功 → 提示+关闭+刷新；「保存」按钮点击', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.dialogVisible = true
    await nextTick()
    await findBtn(wrapper, '保存').trigger('click')
    await flushPromises()
    expect(reportApiMock.create).toHaveBeenCalledWith(expect.objectContaining({ name: '' }))
    expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
    expect(vm.dialogVisible).toBe(false)
    expect(reportApiMock.list).toHaveBeenCalled()
    expect(vm.saving).toBe(false)
  })

  it('handleSave：更新成功 → 「已保存」；失败 → error', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.editingId = 2
    vm.form.name = '改后'
    await vm.handleSave()
    expect(reportApiMock.update).toHaveBeenCalledWith(2, expect.objectContaining({ name: '改后' }))
    expect(ElMessage.success).toHaveBeenCalledWith('已保存')

    reportApiMock.update.mockRejectedValue(new Error('net'))
    await vm.handleSave()
    expect(ElMessage.error).toHaveBeenCalledWith('保存失败')
    expect(vm.saving).toBe(false)
  })
})

describe('行操作', () => {
  it('toggle：成功切换状态（开关 change 事件）；失败提示', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const switches = wrapper.findAllComponents({ name: 'ElSwitch' })
    await switches[0].trigger('click') // rowA → toggle(1)
    await flushPromises()
    expect(reportApiMock.toggle).toHaveBeenCalledWith(1)
    expect(rowA.is_active).toBe(false)

    reportApiMock.toggle.mockRejectedValue(new Error('net'))
    await switches[1].trigger('click')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('操作失败')
  })

  it('handleGenerate 成功与失败（生成按钮）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await findBtn(wrapper, '生成').trigger('click')
    await flushPromises()
    expect(reportApiMock.generate).toHaveBeenCalledWith({ subscription_id: 1 })
    expect(ElMessage.success).toHaveBeenCalledWith('已生成')

    reportApiMock.generate.mockRejectedValue(new Error('net'))
    await findBtn(wrapper, '生成').trigger('click')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('生成失败')
  })

  it('handleDownload：无 id 早退；成功；失败（下载按钮）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.handleDownload({})
    expect(reportApiMock.download).not.toHaveBeenCalled()

    await findBtn(wrapper, '下载').trigger('click')
    await flushPromises()
    expect(reportApiMock.download).toHaveBeenCalledWith(1)

    reportApiMock.download.mockRejectedValue(new Error('net'))
    await findBtn(wrapper, '下载').trigger('click')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('下载失败')
  })

  it('handleDelete：确认 → 删除+提示+刷新；取消静默（删除按钮）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await findBtn(wrapper, '删除').trigger('click')
    await flushPromises()
    expect(confirmMock).toHaveBeenCalledWith('确定删除此订阅？', '提示', expect.objectContaining({ type: 'warning' }))
    expect(reportApiMock.delete).toHaveBeenCalledWith(1)
    expect(ElMessage.success).toHaveBeenCalledWith('已删除')
    expect(reportApiMock.list).toHaveBeenCalled()

    confirmMock.mockRejectedValueOnce(new Error('cancel'))
    await vm.handleDelete(rowB)
    expect(reportApiMock.delete.mock.calls.length).toBe(1)
  })
})

describe('对话框表单', () => {
  it('v-model 与取消按钮', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.dialogVisible = true
    await nextTick()
    const byName = (n: string) => wrapper.findAllComponents({ name: n })
    byName('ElInput')[0].vm.$emit('update:modelValue', '新名称')
    expect(vm.form.name).toBe('新名称')
    byName('ElSelect')[0].vm.$emit('update:modelValue', 'funds')
    expect(vm.form.report_type).toBe('funds')
    byName('ElRadioGroup')[0].vm.$emit('update:modelValue', 'pdf')
    expect(vm.form.format).toBe('pdf')
    byName('ElInputNumber')[0].vm.$emit('update:modelValue', 2025)
    expect(vm.form.year).toBe(2025)
    byName('ElSelect')[1].vm.$emit('update:modelValue', 'daily')
    expect(vm.form.frequency).toBe('daily')
    byName('ElInput')[1].vm.$emit('update:modelValue', 'a@b.c')
    expect(vm.form.email).toBe('a@b.c')

    await findBtn(wrapper, '取消').trigger('click')
    expect(vm.dialogVisible).toBe(false)
    vm.dialogVisible = true
    await nextTick()
    wrapper.findAllComponents({ name: 'ElDialog' })[0].vm.$emit('update:modelValue', false)
    expect(vm.dialogVisible).toBe(false)
  })
})
