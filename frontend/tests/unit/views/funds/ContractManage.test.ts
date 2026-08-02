/**
 * views/funds/ContractManage.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：onMounted 列表加载、状态筛选 change、分页、新建合同（校验失败/成功/失败）、
 * 付款登记（校验失败/成功/失败）、删除（取消/成功/失败）、模板分支。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const { ElMessage, confirmMock, lifecycleApi, pushSafeMock, routeBox } = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  confirmMock: vi.fn(),
  lifecycleApi: {
    listContracts: vi.fn(),
    createContract: vi.fn(),
    createContractPayment: vi.fn(),
    deleteContract: vi.fn(),
  },
  pushSafeMock: vi.fn(),
  routeBox: { query: {} as Record<string, any> },
}))

vi.mock('vue-router', () => ({
  useRoute: () => routeBox,
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

vi.mock('@/api/fundLifecycle', () => ({ fundLifecycleApi: lifecycleApi }))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ pushSafe: pushSafeMock }),
  safeRouteParam: (v: any) => Number(v) || v,
}))

import ContractManage from '@/views/funds/ContractManage.vue'

const contractDraft = {
  id: 1,
  contract_no: 'HT-001',
  contract_name: '基建合同',
  party_a: '甲方A',
  party_b: '乙方B',
  contract_amount: 100,
  paid_amount: 40,
  payment_progress: 40,
  status: 'draft',
  status_label: '草稿',
}

const contractActive = {
  id: 2,
  contract_no: 'HT-002',
  contract_name: '执行中合同',
  status: 'active',
  status_label: '执行中',
}

const contractCompleted = {
  id: 3,
  contract_no: 'HT-003',
  contract_name: '已完成合同',
  status: 'completed',
  status_label: '已完成',
}

const contractTerminated = {
  id: 4,
  contract_no: 'HT-004',
  contract_name: '已终止合同',
  status: 'terminated',
  status_label: '已终止',
}

function mountComp() {
  return mount(ContractManage, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-page-header': {
          name: 'ElPageHeader',
          template: '<div class="el-page-header-stub"><slot name="content" /><slot /></div>',
          emits: ['back'],
        },
        'el-card': { template: '<div class="el-card-stub"><slot /></div>' },
        'el-table': {
          template:
            '<div class="el-table-stub"><slot name="empty" /><slot name="default" /></div>',
        },
        'el-table-column': {
          name: 'ElTableColumn',
          template:
            '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /><slot :row="rowC" /><slot :row="rowD" /></div>',
          data() {
            return {
              rowA: { ...contractDraft },
              rowB: { ...contractActive },
              rowC: { ...contractCompleted },
              rowD: { ...contractTerminated },
            }
          },
        },
        'el-form': { template: '<div class="el-form-stub"><slot /></div>' },
        'el-form-item': { template: '<div class="el-form-item-stub"><slot /></div>' },
        'el-input': {
          template:
            '<div class="el-input-stub" @click="$emit(\'update:modelValue\', \'V\')" />',
        },
        'el-input-number': {
          template:
            '<div class="el-input-number-stub" @click="$emit(\'update:modelValue\', 5)" />',
        },
        'el-select': {
          template:
            '<div class="el-select-stub" @click="$emit(\'update:modelValue\', \'draft\'); $emit(\'change\', \'draft\')"><slot /></div>',
        },
        'el-option': { template: '<div class="el-option-stub" />' },
        'el-date-picker': {
          template:
            '<div class="el-date-picker-stub" @click="$emit(\'update:modelValue\', \'2024-01-01\')" />',
        },
        'el-button': {
          template: '<button class="el-button-stub" @click="$emit(\'click\')"><slot /></button>',
          emits: ['click'],
        },
        'el-pagination': {
          template:
            '<div class="el-pagination-stub" @click="$emit(\'current-change\'); $emit(\'update:currentPage\', 2)" />',
        },
        'el-progress': { template: '<div class="el-progress-stub" />' },
        'el-tag': { template: '<span class="el-tag-stub"><slot /></span>' },
        'el-dialog': {
          template:
            '<div class="el-dialog-stub" @click="$emit(\'update:modelValue\', false)"><slot /><slot name="footer" /></div>',
        },
      },
    },
  })
}

beforeEach(() => {
  vi.resetAllMocks()
  routeBox.query = {}
  lifecycleApi.listContracts.mockResolvedValue({
    items: [contractDraft, contractActive, contractCompleted, contractTerminated],
    total: 4,
  })
  lifecycleApi.createContract.mockResolvedValue({})
  lifecycleApi.createContractPayment.mockResolvedValue({})
  lifecycleApi.deleteContract.mockResolvedValue({})
  confirmMock.mockResolvedValue(undefined)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('挂载与列表加载', () => {
  it('onMounted 加载合同列表（无 project_id）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(lifecycleApi.listContracts).toHaveBeenCalledWith({
      project_id: undefined,
      status: undefined,
      page: 1,
      page_size: 20,
    })
    expect(vm.contracts).toHaveLength(4)
    expect(vm.total).toBe(4)
  })

  it('onMounted 带 project_id 查询参数', async () => {
    routeBox.query = { project_id: '7' }
    const wrapper = mountComp()
    await flushPromises()
    expect(lifecycleApi.listContracts).toHaveBeenCalledWith(
      expect.objectContaining({ project_id: 7 })
    )
  })

  it('loadData 失败 → 错误提示 + loading 复位', async () => {
    lifecycleApi.listContracts.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('加载失败')
    expect((wrapper.vm as any).loading).toBe(false)
  })

  it('listContracts 无 items → 空数组', async () => {
    lifecycleApi.listContracts.mockResolvedValue({})
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).contracts).toEqual([])
  })

  it('状态筛选 change → loadData', async () => {
    const wrapper = mountComp()
    await flushPromises()
    lifecycleApi.listContracts.mockClear()
    const sel = wrapper.find('.el-select-stub')
    await sel.trigger('click')
    await flushPromises()
    expect(lifecycleApi.listContracts).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'draft' })
    )
  })

  it('分页 current-change → loadData', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.page = 3
    lifecycleApi.listContracts.mockClear()
    await wrapper.find('.el-pagination-stub').trigger('click')
    await flushPromises()
    expect(lifecycleApi.listContracts).toHaveBeenCalledWith(
      expect.objectContaining({ page: 3 })
    )
  })

  it('页头返回 → pushSafe /funds', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const ph = wrapper.findComponent({ name: 'ElPageHeader' })
    await ph.vm.$emit('back')
    expect(pushSafeMock).toHaveBeenCalledWith('/funds')
  })
})

describe('新建合同', () => {
  it('校验失败（缺编号/名称）→ warning', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await (wrapper.vm as any).handleCreateContract()
    expect(ElMessage.warning).toHaveBeenCalledWith('请填写合同编号和名称')
    expect(lifecycleApi.createContract).not.toHaveBeenCalled()
  })

  it('创建成功 → 提示 + 关弹窗 + 重置页码 + 刷新', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.contractForm.contract_no = 'HT-X'
    vm.contractForm.contract_name = '新合同'
    vm.page = 5
    lifecycleApi.listContracts.mockClear()
    await vm.handleCreateContract()
    expect(lifecycleApi.createContract).toHaveBeenCalledWith(vm.contractForm)
    expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
    expect(vm.showCreateDialog).toBe(false)
    expect(vm.page).toBe(1)
    expect(lifecycleApi.listContracts).toHaveBeenCalled()
  })

  it('创建失败 → detail 与兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.contractForm.contract_no = 'HT-X'
    vm.contractForm.contract_name = '新合同'
    lifecycleApi.createContract.mockRejectedValueOnce({ response: { data: { detail: '编号重复' } } })
    await vm.handleCreateContract()
    expect(ElMessage.error).toHaveBeenCalledWith('编号重复')

    lifecycleApi.createContract.mockRejectedValueOnce(new Error('net'))
    await vm.handleCreateContract()
    expect(ElMessage.error).toHaveBeenCalledWith('创建失败')
  })

  it('新建按钮 → 打开弹窗', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const btn = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('新建合同'))
    await btn!.trigger('click')
    expect((wrapper.vm as any).showCreateDialog).toBe(true)
  })
})

describe('登记付款', () => {
  it('showPaymentDialog 重置表单并打开', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.paymentForm.amount = 99
    vm.paymentForm.payment_date = 'x'
    vm.showPaymentDialog(contractDraft)
    expect(vm.currentContractId).toBe(1)
    expect(vm.paymentForm.amount).toBe(0)
    expect(vm.paymentForm.payment_date).toBe('')
    expect(vm.paymentDialogVisible).toBe(true)
  })

  it('校验失败（缺金额/日期）→ warning', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await (wrapper.vm as any).handleCreatePayment()
    expect(ElMessage.warning).toHaveBeenCalledWith('请填写金额和日期')
  })

  it('提交成功 → 提示 + 关弹窗 + 刷新', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.currentContractId = 1
    vm.paymentForm.amount = 10
    vm.paymentForm.payment_date = '2024-01-01'
    lifecycleApi.listContracts.mockClear()
    await vm.handleCreatePayment()
    expect(lifecycleApi.createContractPayment).toHaveBeenCalledWith(1, vm.paymentForm)
    expect(ElMessage.success).toHaveBeenCalledWith('付款登记成功')
    expect(vm.paymentDialogVisible).toBe(false)
    expect(lifecycleApi.listContracts).toHaveBeenCalled()
  })

  it('提交失败 → detail 与兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.currentContractId = 1
    vm.paymentForm.amount = 10
    vm.paymentForm.payment_date = '2024-01-01'
    lifecycleApi.createContractPayment.mockRejectedValueOnce({ response: { data: { detail: '超预算' } } })
    await vm.handleCreatePayment()
    expect(ElMessage.error).toHaveBeenCalledWith('超预算')

    lifecycleApi.createContractPayment.mockRejectedValueOnce(new Error('net'))
    await vm.handleCreatePayment()
    expect(ElMessage.error).toHaveBeenCalledWith('登记失败')
  })

  it('付款按钮（操作列）→ 打开付款弹窗', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const btn = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('登记付款'))
    await btn!.trigger('click')
    expect((wrapper.vm as any).paymentDialogVisible).toBe(true)
  })
})

describe('删除合同', () => {
  it('确认后成功删除', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    lifecycleApi.listContracts.mockClear()
    await vm.handleDeleteContract(1)
    expect(confirmMock).toHaveBeenCalledWith('确认删除此合同？', '确认')
    expect(lifecycleApi.deleteContract).toHaveBeenCalledWith(1)
    expect(ElMessage.success).toHaveBeenCalledWith('已删除')
    expect(lifecycleApi.listContracts).toHaveBeenCalled()
  })

  it('取消 → 不删除不提示', async () => {
    const wrapper = mountComp()
    await flushPromises()
    confirmMock.mockRejectedValueOnce('cancel')
    await (wrapper.vm as any).handleDeleteContract(1)
    expect(lifecycleApi.deleteContract).not.toHaveBeenCalled()
    expect(ElMessage.error).not.toHaveBeenCalled()
  })

  it('删除失败 → detail 与兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    lifecycleApi.deleteContract.mockRejectedValueOnce({ response: { data: { detail: '有关联' } } })
    await vm.handleDeleteContract(1)
    expect(ElMessage.error).toHaveBeenCalledWith('有关联')

    lifecycleApi.deleteContract.mockRejectedValueOnce(new Error('net'))
    await vm.handleDeleteContract(1)
    expect(ElMessage.error).toHaveBeenCalledWith('删除失败')
  })

  it('草稿行渲染删除按钮并可点击', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const del = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('删除'))
    expect(del).toBeTruthy()
  })
})

describe('模板状态标签分支', () => {
  it('四种状态行均渲染（draft/active/completed/terminated）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('草稿')
    expect(wrapper.text()).toContain('执行中')
    expect(wrapper.text()).toContain('已完成')
    expect(wrapper.text()).toContain('已终止')
  })
})

describe('补缺：模板内联处理器（v-model/创建/提交/删除/分页）', () => {
  it('表单控件 v-model 更新 + 创建/提交/删除/分页按钮', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    for (const el of wrapper.findAll('.el-input-stub')) {
      await el.trigger('click')
    }
    for (const el of wrapper.findAll('.el-input-number-stub')) {
      await el.trigger('click')
    }
    for (const el of wrapper.findAll('.el-date-picker-stub')) {
      await el.trigger('click')
    }
    await flushPromises()
    expect(vm.contractForm.contract_no).toBe('V')
    expect(vm.contractForm.party_a).toBe('V')
    expect(vm.contractForm.contract_amount).toBe(5)
    expect(vm.contractForm.sign_date).toBe('2024-01-01')
    expect(vm.paymentForm.amount).toBe(5)
    expect(vm.paymentForm.payment_date).toBe('2024-01-01')

    vm.contractForm.contract_no = 'HT-X'
    vm.contractForm.contract_name = '新合同'
    const createBtn = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('创建'))
    lifecycleApi.listContracts.mockClear()
    await createBtn!.trigger('click')
    await flushPromises()
    expect(lifecycleApi.createContract).toHaveBeenCalled()

    vm.currentContractId = 1
    vm.paymentForm.amount = 10
    vm.paymentForm.payment_date = '2024-01-01'
    const submitBtn = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('提交'))
    lifecycleApi.listContracts.mockClear()
    await submitBtn!.trigger('click')
    await flushPromises()
    expect(lifecycleApi.createContractPayment).toHaveBeenCalled()

    const delBtn = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('删除'))
    lifecycleApi.deleteContract.mockClear()
    await delBtn!.trigger('click')
    await flushPromises()
    expect(lifecycleApi.deleteContract).toHaveBeenCalledWith(1)

    vm.page = 2
    await wrapper.find('.el-pagination-stub').trigger('click')
    await flushPromises()
    expect(vm.page).toBe(2)

    vm.showCreateDialog = true
    vm.paymentDialogVisible = true
    for (const dlg of wrapper.findAll('.el-dialog-stub')) {
      await dlg.trigger('click')
    }
    expect(vm.showCreateDialog).toBe(false)
    expect(vm.paymentDialogVisible).toBe(false)

    vm.showCreateDialog = true
    const cancelBtns = wrapper.findAll('.el-button-stub').filter((b) => b.text().includes('取消'))
    for (const cb of cancelBtns) {
      await cb.trigger('click')
    }
    expect(vm.showCreateDialog).toBe(false)
    expect(vm.paymentDialogVisible).toBe(false)
  })
})
