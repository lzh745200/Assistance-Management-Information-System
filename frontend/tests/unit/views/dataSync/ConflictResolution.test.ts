/**
 * views/dataSync/ConflictResolution.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：getConflictTypeTag/Label 三映射+兜底、loadConflicts（缺 syncLogId 早退、
 * response.data 数组 / items / data 三种形态、remote_data ?? 兜底、默认展开第一个、异常）、
 * resolveConflict（无 resolution 早退、成功移除、异常）、
 * resolveAll（空列表早退、确认后循环解决+跳转、取消静默、失败提示）、
 * 模板：空态 alert、折叠面板标题、radio v-model、解决按钮、collapse v-model。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const { ElMessage, confirmMock, mockGetConflicts, mockResolveConflict, pushSafeMock, routeQuery } =
  vi.hoisted(() => ({
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
    confirmMock: vi.fn(),
    mockGetConflicts: vi.fn(),
    mockResolveConflict: vi.fn(),
    pushSafeMock: vi.fn(),
    routeQuery: {} as Record<string, any>,
  }))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: routeQuery }),
  useRouter: () => ({ resolve: () => ({ name: 'X', matched: [1] }) }),
}))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ pushSafe: pushSafeMock }),
}))

vi.mock('@/api/dataSync', () => ({
  getConflicts: mockGetConflicts,
  resolveConflict: mockResolveConflict,
}))

import ConflictResolution from '@/views/dataSync/ConflictResolution.vue'

const conflictA = {
  id: 1,
  entity_type: 'supported_village',
  conflict_type: 'update',
  table_name: 'supported_villages',
  record_id: 5,
  import_data: { name: '甲村' },
  local_data: { name: '乙村' },
}
const conflictB = {
  id: 2,
  conflict_type: 'delete',
  table_name: 'x',
  record_id: 6,
  remote_data: { a: 1 },
}
const conflictC = {
  id: 3,
  conflict_type: 'insert',
  table_name: 'y',
  record_id: 7,
  import_data: { b: 2 },
}
const conflictD = { id: 4, conflict_type: 'weird', table_name: 'z', record_id: 8 }
const conflictE = { id: 5, table_name: 't', record_id: 9 }

function mountComp() {
  return mount(ConflictResolution, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot name="header" /><slot /></div>',
        },
        'el-collapse': {
          name: 'ElCollapse',
          template: '<div class="el-collapse-stub"><slot /></div>',
          emits: ['update:modelValue'],
        },
        'el-collapse-item': {
          name: 'ElCollapseItem',
          props: ['name'],
          template: '<div class="el-collapse-item-stub"><slot name="title" /><slot /></div>',
        },
        'el-tag': { name: 'ElTag', template: '<span class="el-tag-stub"><slot /></span>' },
        'el-radio-group': {
          name: 'ElRadioGroup',
          template: '<div class="el-radio-group-stub"><slot /></div>',
          emits: ['update:modelValue'],
        },
        'el-descriptions': {
          name: 'ElDescriptions',
          template: '<div class="el-descriptions-stub"><slot /></div>',
        },
        'el-descriptions-item': {
          name: 'ElDescriptionsItem',
          template: '<div class="el-descriptions-item-stub"><slot /></div>',
        },
        'el-alert': { name: 'ElAlert', template: '<div class="el-alert-stub"><slot /></div>' },
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
  routeQuery.syncLogId = '99'
  mockGetConflicts.mockResolvedValue({
    success: true,
    data: [conflictA, conflictB, conflictC, conflictD, conflictE],
  })
  mockResolveConflict.mockResolvedValue({})
  confirmMock.mockResolvedValue('confirm')
})

describe('挂载与加载', () => {
  it('onMounted：data 数组形态；remote_data ?? 兜底；默认展开第一个', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(mockGetConflicts).toHaveBeenCalledWith(99)
    expect(vm.conflicts).toHaveLength(5)
    // import_data ?? remote_data
    expect(vm.conflicts[0].remote_data).toEqual({ name: '甲村' })
    expect(vm.conflicts[1].remote_data).toEqual({ a: 1 })
    expect(vm.conflicts[2].remote_data).toEqual({ b: 2 })
    expect(vm.conflicts[3].remote_data).toBeUndefined()
    expect(vm.conflicts.every((c: any) => c.resolution === 'keep_local')).toBe(true)
    expect(vm.activeNames).toEqual([0])
    expect(vm.loading).toBe(false)
    const text = wrapper.text()
    expect(text).toContain('更新冲突')
    expect(text).toContain('删除冲突')
    expect(text).toContain('插入冲突')
    expect(text).toContain('weird') // 未知类型原样
    expect(text).toContain('supported_villages')
    expect(text).toContain('记录ID: 5')
    expect(text).toContain('甲村')
  })

  it('items / data 嵌套形态、data 为空对象与空列表', async () => {
    mockGetConflicts.mockResolvedValue({ success: true, data: { items: [conflictA] } })
    let wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).conflicts).toHaveLength(1)

    mockGetConflicts.mockResolvedValue({ success: true, data: { data: [conflictB] } })
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).conflicts).toHaveLength(1)

    mockGetConflicts.mockResolvedValue({ success: true, data: {} })
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).conflicts).toEqual([])

    mockGetConflicts.mockResolvedValue({ success: true, data: [] })
    wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.conflicts).toEqual([])
    expect(vm.activeNames).toEqual([])
    expect(wrapper.find('.el-alert-stub').exists()).toBe(true)
  })

  it('缺 syncLogId → 警告早退；请求异常 → error(message 或兜底)', async () => {
    delete routeQuery.syncLogId
    let wrapper = mountComp()
    await flushPromises()
    expect(ElMessage.warning).toHaveBeenCalledWith('缺少同步日志ID')
    expect(mockGetConflicts).not.toHaveBeenCalled()
    expect((wrapper.vm as any).loading).toBe(false)

    routeQuery.syncLogId = '1'
    mockGetConflicts.mockRejectedValue(new Error('网络错误'))
    wrapper = mountComp()
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('网络错误')

    mockGetConflicts.mockRejectedValue(new Error(''))
    wrapper = mountComp()
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('加载冲突数据失败')
  })

  it('response.success 为 false → 不更新列表', async () => {
    mockGetConflicts.mockResolvedValue({ success: false, data: [conflictA] })
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).conflicts).toEqual([])
  })
})

describe('单个解决', () => {
  it('无 resolution → 警告早退；成功 → 移除列表项', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.conflicts[0].resolution = undefined as any
    await vm.resolveConflict(vm.conflicts[0])
    expect(ElMessage.warning).toHaveBeenCalledWith('请选择解决方案')
    expect(mockResolveConflict).not.toHaveBeenCalled()

    vm.conflicts[0].resolution = 'use_import'
    await vm.resolveConflict(vm.conflicts[0])
    expect(mockResolveConflict).toHaveBeenCalledWith({ conflict_id: 1, resolution: 'use_import' })
    expect(ElMessage.success).toHaveBeenCalledWith('冲突已解决')
    expect(vm.conflicts).toHaveLength(4)
  })

  it('异常 → error(message 或兜底)；radio v-model 切换', async () => {
    mockResolveConflict.mockRejectedValue(new Error('失败原因'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const radioGroups = wrapper.findAllComponents({ name: 'ElRadioGroup' })
    radioGroups[0].vm.$emit('update:modelValue', 'merge')
    expect(vm.conflicts[0].resolution).toBe('merge')
    await vm.resolveConflict(vm.conflicts[0])
    expect(ElMessage.error).toHaveBeenCalledWith('失败原因')

    mockResolveConflict.mockRejectedValue(new Error(''))
    await vm.resolveConflict(vm.conflicts[1])
    expect(ElMessage.error).toHaveBeenCalledWith('解决冲突失败')
  })

  it('「解决此冲突」按钮真实点击（内联行参数）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await findBtn(wrapper, '解决此冲突').trigger('click')
    await flushPromises()
    expect(mockResolveConflict).toHaveBeenCalledWith(
      expect.objectContaining({ resolution: 'keep_local' })
    )
  })

  it('「批量解决」按钮 + collapse v-model', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    wrapper.findAllComponents({ name: 'ElCollapse' })[0].vm.$emit('update:modelValue', [1])
    expect(vm.activeNames).toEqual([1])
  })
})

describe('批量解决', () => {
  it('空列表 → info 早退', async () => {
    mockGetConflicts.mockResolvedValue({ success: true, data: [] })
    const wrapper = mountComp()
    await flushPromises()
    await (wrapper.vm as any).resolveAll()
    expect(ElMessage.info).toHaveBeenCalledWith('没有需要解决的冲突')
    expect(confirmMock).not.toHaveBeenCalled()
  })

  it('确认后循环解决 → 成功提示 + 清空 + 跳转导入页；resolution 缺失 → keep_local 兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.conflicts[1].resolution = undefined as any
    await vm.resolveAll()
    expect(confirmMock).toHaveBeenCalledWith(
      '确定要批量解决 5 个冲突吗？',
      '批量解决',
      expect.objectContaining({ type: 'warning' })
    )
    expect(mockResolveConflict).toHaveBeenCalledTimes(5)
    expect(mockResolveConflict).toHaveBeenCalledWith({ conflict_id: 3, resolution: 'keep_local' })
    expect(mockResolveConflict).toHaveBeenCalledWith({ conflict_id: 2, resolution: 'keep_local' })
    expect(ElMessage.success).toHaveBeenCalledWith('所有冲突已解决')
    expect(vm.conflicts).toEqual([])
    expect(pushSafeMock).toHaveBeenCalledWith({ name: 'DataSyncImport' })
  })

  it('取消 → 静默；失败（含空 message 兜底）', async () => {
    confirmMock.mockRejectedValueOnce(new Error('cancel'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.resolveAll()
    expect(mockResolveConflict).not.toHaveBeenCalled()

    mockResolveConflict.mockRejectedValueOnce(new Error('批量失败'))
    await vm.resolveAll()
    expect(ElMessage.error).toHaveBeenCalledWith('批量失败')

    mockResolveConflict.mockRejectedValueOnce(new Error(''))
    await vm.resolveAll()
    expect(ElMessage.error).toHaveBeenCalledWith('批量解决失败')
  })
})
