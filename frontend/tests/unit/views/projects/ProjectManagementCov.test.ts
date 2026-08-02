/**
 * views/projects/ProjectManagement.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：loadProjects 成功/兜底/失败与 keyword/status ||undefined 两侧、handleSearch/handleReset、
 * handleCreate/handleEdit/handleView、handleDelete 取消/成功/失败、handleSelectionChange、
 * handleSubmit 全分支（无 formRef/submitting 中/校验失败/创建/编辑/编辑无 currentProject/创建失败/编辑失败）、
 * handleDialogClose/resetForm（formRef 有无两侧）、handleExport 成功/失败、
 * handleImport（fileInput 有无两侧）、handleFileChange 无文件/成功（含进度回调）/失败、
 * 分页与全部 v-model/内联点击、状态与优先级 map 命中及 || 兜底、列插槽两行样本。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

// vi.mock 工厂提升求值，引用对象须先放入 vi.hoisted 初始化（TDZ）
const { ElMessage, confirmMock, logInfo, api } = vi.hoisted(() => {
  return {
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
    confirmMock: vi.fn(),
    logInfo: vi.fn(),
    api: {
      list: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      exportList: vi.fn(),
      importData: vi.fn(),
    },
  }
})

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

vi.mock('@/api/projects', () => ({ projectApi: api }))

vi.mock('@/utils/logger', () => ({
  logger: { error: vi.fn(), warn: vi.fn(), info: logInfo, debug: vi.fn() },
}))

import ProjectManagement from '@/views/projects/ProjectManagement.vue'

// el-table-column 插槽样本行：rowB 的 status/priority 为未知值，覆盖 || 兜底侧
const slotRowA = {
  id: 1,
  name: '甲项目',
  description: '描述甲',
  status: 'pending',
  priority: 'low',
  start_date: '2024-01-01',
  end_date: '2024-06-01',
}
const slotRowB = {
  id: 2,
  name: '乙项目',
  description: '描述乙',
  status: 'archived',
  priority: 'urgent',
  start_date: '2024-02-01',
  end_date: '2024-07-01',
}

const stubs = {
  'el-dialog': {
    name: 'ElDialog',
    template: '<div class="el-dialog-stub"><slot /><slot name="footer" /></div>',
    props: ['modelValue', 'title'],
    emits: ['update:modelValue', 'close'],
  },
  'el-table-column': {
    name: 'ElTableColumn',
    template: '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /></div>',
    data() {
      return { rowA: slotRowA, rowB: slotRowB }
    },
  },
}

// 用例卸载注册表：避免跨测试污染
const liveWrappers: any[] = []

function mountComp() {
  const w = mount(ProjectManagement, { global: { renderStubDefaultSlot: true, stubs } })
  liveWrappers.push(w)
  return w
}

function findBtn(wrapper: any, text: string) {
  const btn = wrapper.findAll('el-button-stub').find((b: any) => b.text().trim() === text)
  expect(btn, `按钮「${text}」`).toBeTruthy()
  return btn!
}

beforeEach(() => {
  vi.resetAllMocks()
  api.list.mockResolvedValue({
    data: {
      items: [
        { id: 1, name: '项目A', status: 'in_progress', priority: 'high' },
        { id: 2, name: '项目B', status: 'completed', priority: 'medium' },
      ],
      total: 2,
    },
  })
  api.create.mockResolvedValue({})
  api.update.mockResolvedValue({})
  api.delete.mockResolvedValue({})
  api.exportList.mockResolvedValue({})
  api.importData.mockResolvedValue({ imported: 1 })
  confirmMock.mockResolvedValue(undefined)
})

afterEach(() => {
  while (liveWrappers.length) liveWrappers.pop().unmount()
  vi.restoreAllMocks()
})

/** 生成可通过校验的 formRef mock（callback 形式 validate） */
function makeFormRef(valid = true) {
  return { validate: vi.fn((cb: any) => cb(valid)), resetFields: vi.fn() }
}

// ==================== 测试 ====================

describe('挂载与数据加载', () => {
  it('onMounted 加载成功：items/total 值侧，表格渲染', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(api.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 20,
      keyword: undefined,
      status: undefined,
    })
    expect(vm.projects).toHaveLength(2)
    expect(vm.pagination.total).toBe(2)
    expect(vm.loading).toBe(false)
    expect(wrapper.text()).toContain('项目管理')
  })

  it('loadProjects：items/total 缺失走 || 兜底；失败提示', async () => {
    api.list.mockResolvedValue({ data: {} })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.projects).toEqual([])
    expect(vm.pagination.total).toBe(0)

    api.list.mockRejectedValue(new Error('net'))
    await vm.loadProjects()
    expect(ElMessage.error).toHaveBeenCalledWith('加载项目列表失败')
    expect(vm.loading).toBe(false)
  })

  it('loadProjects 携带 keyword/status 值侧', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.filterForm.search = '道路'
    vm.filterForm.status = 'pending'
    await vm.loadProjects()
    expect(api.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ keyword: '道路', status: 'pending' })
    )
  })
})

describe('搜索 / 重置 / 筛选交互', () => {
  it('handleSearch 复位页码；handleReset 清空并搜索', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.pagination.page = 5
    vm.handleSearch()
    expect(vm.pagination.page).toBe(1)

    vm.filterForm.search = 'x'
    vm.filterForm.status = 'pending'
    vm.filterForm.priority = 'high'
    vm.handleReset()
    expect(vm.filterForm).toMatchObject({ search: '', status: '', priority: '' })
  })

  it('搜索/重置按钮点击；el-input v-model 与 @clear；两个 el-select v-model 与 @change', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    const input = wrapper.findAllComponents({ name: 'ElInput' })[0]
    input.vm.$emit('update:modelValue', '桥梁')
    expect(vm.filterForm.search).toBe('桥梁')
    input.vm.$emit('clear')
    expect(vm.pagination.page).toBe(1)

    const selects = wrapper.findAllComponents({ name: 'ElSelect' })
    selects[0].vm.$emit('update:modelValue', 'completed')
    expect(vm.filterForm.status).toBe('completed')
    selects[0].vm.$emit('change')
    selects[1].vm.$emit('update:modelValue', 'high')
    expect(vm.filterForm.priority).toBe('high')
    selects[1].vm.$emit('change')
    await flushPromises()

    await findBtn(wrapper, '搜索').trigger('click')
    await findBtn(wrapper, '重置').trigger('click')
    expect(vm.filterForm.search).toBe('')
  })

  it('handleSelectionChange 写入选中行（ElTable selection-change）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    wrapper.findComponent({ name: 'ElTable' }).vm.$emit('selection-change', [slotRowA])
    expect(vm.selectedProjects).toEqual([slotRowA])
  })

  it('分页：v-model 两侧 onUpdate 与 size-change/current-change', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const pager = wrapper.findComponent({ name: 'ElPagination' })
    pager.vm.$emit('update:current-page', 3)
    expect(vm.pagination.page).toBe(3)
    pager.vm.$emit('update:page-size', 50)
    expect(vm.pagination.page_size).toBe(50)

    pager.vm.$emit('size-change', 100)
    await flushPromises()
    expect(vm.pagination.page_size).toBe(100)
    expect(vm.pagination.page).toBe(1)

    pager.vm.$emit('current-change', 4)
    await flushPromises()
    expect(vm.pagination.page).toBe(4)
  })
})

describe('列插槽与状态/优先级映射', () => {
  it('列插槽两行：map 命中侧与 || 兜底侧文本', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('待处理') // pending 命中
    expect(text).toContain('低') // low 命中
    expect(text).toContain('archived') // status 未知 → || status 兜底
    expect(text).toContain('urgent') // priority 未知 → || priority 兜底
  })

  it('getStatusType/Text 与 getPriorityType/Text 全映射与兜底', async () => {
    const wrapper = mountComp()
    const vm = wrapper.vm as any
    expect(vm.getStatusType('pending')).toBe('info')
    expect(vm.getStatusType('in_progress')).toBe('warning')
    expect(vm.getStatusType('completed')).toBe('success')
    expect(vm.getStatusType('cancelled')).toBe('danger')
    expect(vm.getStatusType('other')).toBe('info')
    expect(vm.getStatusText('pending')).toBe('待处理')
    expect(vm.getStatusText('in_progress')).toBe('进行中')
    expect(vm.getStatusText('completed')).toBe('已完成')
    expect(vm.getStatusText('cancelled')).toBe('已取消')
    expect(vm.getStatusText('other')).toBe('other')
    expect(vm.getPriorityType('low')).toBe('info')
    expect(vm.getPriorityType('medium')).toBe('warning')
    expect(vm.getPriorityType('high')).toBe('danger')
    expect(vm.getPriorityType('other')).toBe('info')
    expect(vm.getPriorityText('low')).toBe('低')
    expect(vm.getPriorityText('medium')).toBe('中')
    expect(vm.getPriorityText('high')).toBe('高')
    expect(vm.getPriorityText('other')).toBe('other')
  })

  it('操作列 查看/编辑/删除 按钮点击', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    await findBtn(wrapper, '查看').trigger('click')
    expect(vm.dialogMode).toBe('view')
    expect(vm.dialogTitle).toBe('查看项目')
    expect(vm.currentProject).toEqual(slotRowA)
    expect(vm.formData.name).toBe('甲项目')

    await findBtn(wrapper, '编辑').trigger('click')
    expect(vm.dialogMode).toBe('edit')
    expect(vm.dialogTitle).toBe('编辑项目')

    await findBtn(wrapper, '删除').trigger('click')
    await flushPromises()
    expect(confirmMock).toHaveBeenCalled()
    expect(api.delete).toHaveBeenCalledWith(1)
  })
})

describe('对话框与表单', () => {
  it('新增项目按钮打开对话框并重置表单；dialog v-model onUpdate；取消按钮内联关闭', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // handleCreate 内部走 resetForm → formRef.resetFields：先换成 mock（stub 实例无该方法）
    vm.formRef = makeFormRef()

    await findBtn(wrapper, '新增项目').trigger('click')
    expect(vm.dialogVisible).toBe(true)
    expect(vm.dialogMode).toBe('create')
    expect(vm.dialogTitle).toBe('新增项目')
    expect(vm.formData.name).toBe('')

    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    dialog.vm.$emit('update:modelValue', false)
    expect(vm.dialogVisible).toBe(false)

    vm.dialogVisible = true
    await nextTick()
    await findBtn(wrapper, '取消').trigger('click') // @click="dialogVisible = false"
    expect(vm.dialogVisible).toBe(false)
  })

  it('dialog @close 触发 handleDialogClose → resetForm（formRef 有/无两侧）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const resetFields = vi.fn()
    vm.formRef = { resetFields, validate: vi.fn() }
    vm.formData.name = '脏数据'
    wrapper.findComponent({ name: 'ElDialog' }).vm.$emit('close')
    expect(resetFields).toHaveBeenCalled()
    expect(vm.formData.name).toBe('')
    expect(vm.formData.status).toBe('pending')

    vm.formRef = undefined
    expect(() => vm.handleDialogClose()).not.toThrow() // formRef?.resetFields() 空侧
  })

  it('对话框内表单 v-model 全同步（输入框/下拉/日期选择器）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.formRef = makeFormRef() // handleCreate → resetForm 需要 resetFields
    vm.handleCreate()
    await nextTick()

    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    const inputs = dialog.findAllComponents({ name: 'ElInput' })
    inputs[0].vm.$emit('update:modelValue', '新项目')
    expect(vm.formData.name).toBe('新项目')
    inputs[1].vm.$emit('update:modelValue', '这是项目描述')
    expect(vm.formData.description).toBe('这是项目描述')

    const selects = dialog.findAllComponents({ name: 'ElSelect' })
    selects[0].vm.$emit('update:modelValue', 'in_progress')
    expect(vm.formData.status).toBe('in_progress')
    selects[1].vm.$emit('update:modelValue', 'high')
    expect(vm.formData.priority).toBe('high')

    const pickers = dialog.findAllComponents({ name: 'ElDatePicker' })
    expect(pickers).toHaveLength(2)
    pickers[0].vm.$emit('update:modelValue', '2024-03-01')
    expect(vm.formData.start_date).toBe('2024-03-01')
    pickers[1].vm.$emit('update:modelValue', '2024-09-01')
    expect(vm.formData.end_date).toBe('2024-09-01')
  })

  it('handleSubmit 创建成功：校验通过 → create → 关闭对话框并刷新', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const formRefMock = makeFormRef()
    vm.formRef = formRefMock // handleCreate → resetForm 需要 resetFields
    vm.handleCreate()
    vm.formData.name = '新项目'
    vm.formRef = formRefMock // 每次调用前重新赋值（重渲染会重同步模板 ref）
    await vm.handleSubmit()
    await flushPromises()
    expect(formRefMock.validate).toHaveBeenCalled()
    expect(api.create).toHaveBeenCalledWith(vm.formData)
    expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
    expect(vm.dialogVisible).toBe(false)
    expect(vm.pagination.page).toBe(1)
    expect(vm.submitting).toBe(false)
  })

  it('handleSubmit 编辑成功：确定按钮点击 → update', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const formRefMock = makeFormRef()
    vm.handleEdit({ ...slotRowA })
    expect(vm.dialogMode).toBe('edit')

    vm.formRef = formRefMock
    await findBtn(wrapper, '确定').trigger('click')
    await flushPromises()
    expect(api.update).toHaveBeenCalledWith(1, vm.formData)
    expect(ElMessage.success).toHaveBeenCalledWith('更新成功')
  })

  it('handleSubmit：无 formRef 早退；submitting 中早退；校验失败不发请求', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    vm.formRef = undefined
    await vm.handleSubmit()
    expect(api.create).not.toHaveBeenCalled()

    const formRefMock = makeFormRef()
    vm.formRef = formRefMock
    vm.submitting = true
    await vm.handleSubmit()
    expect(formRefMock.validate).not.toHaveBeenCalled()
    vm.submitting = false

    vm.formRef = makeFormRef(false)
    await vm.handleSubmit()
    expect(api.create).not.toHaveBeenCalled()
  })

  it('handleSubmit：编辑模式但 currentProject 为空 → 不发 create/update', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.dialogMode = 'edit'
    vm.currentProject = null
    vm.formRef = makeFormRef()
    await vm.handleSubmit()
    await flushPromises()
    expect(api.create).not.toHaveBeenCalled()
    expect(api.update).not.toHaveBeenCalled()
    expect(vm.dialogVisible).toBe(false)
  })

  it('handleSubmit 失败：创建 → 创建失败；编辑 → 更新失败；submitting 复位', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    api.create.mockRejectedValueOnce(new Error('dup'))
    vm.formRef = makeFormRef() // handleCreate → resetForm 需要 resetFields
    vm.handleCreate()
    vm.formRef = makeFormRef()
    await vm.handleSubmit()
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('创建失败')
    expect(vm.submitting).toBe(false)

    api.update.mockRejectedValueOnce(new Error('conflict'))
    vm.handleEdit({ ...slotRowA })
    vm.formRef = makeFormRef()
    await vm.handleSubmit()
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('更新失败')
  })
})

describe('删除全分支', () => {
  it('取消确认 → 不发请求', async () => {
    confirmMock.mockRejectedValue('cancel')
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.handleDelete(slotRowA)
    expect(api.delete).not.toHaveBeenCalled()
  })

  it('删除成功：复位页码并刷新；删除失败提示', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.pagination.page = 3

    await vm.handleDelete(slotRowA)
    expect(api.delete).toHaveBeenCalledWith(1)
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    expect(vm.pagination.page).toBe(1)

    api.delete.mockRejectedValueOnce(new Error('db'))
    await vm.handleDelete(slotRowA)
    expect(ElMessage.error).toHaveBeenCalledWith('删除失败')
  })
})

describe('导出 / 导入', () => {
  it('handleExport 成功（参数空侧）与失败；参数值侧', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    await findBtn(wrapper, '导出数据').trigger('click')
    await flushPromises()
    expect(api.exportList).toHaveBeenCalledWith({ keyword: undefined, status: undefined })
    expect(ElMessage.success).toHaveBeenCalledWith('导出成功')

    vm.filterForm.search = '桥'
    vm.filterForm.status = 'pending'
    await vm.handleExport()
    expect(api.exportList).toHaveBeenLastCalledWith({ keyword: '桥', status: 'pending' })

    api.exportList.mockRejectedValueOnce(new Error('down'))
    await vm.handleExport()
    expect(ElMessage.error).toHaveBeenCalledWith('导出失败')
  })

  it('handleImport：fileInput 存在 → click；不存在 → 可选链空侧', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    const input = wrapper.find('input[type="file"]')
    const clickSpy = vi.spyOn(input.element as HTMLInputElement, 'click')
    await findBtn(wrapper, '导入数据').trigger('click')
    expect(clickSpy).toHaveBeenCalled()

    vm.fileInput = undefined
    expect(() => vm.handleImport()).not.toThrow()
  })

  it('handleFileChange：无文件早退', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.handleFileChange({ target: { files: [] } })
    expect(api.importData).not.toHaveBeenCalled()
  })

  it('handleFileChange 成功：进度回调 → logger.info；复位页码并清空 input.value', async () => {
    api.importData.mockImplementation((_f: any, _mode: any, onProgress: any) => {
      onProgress(42)
      return Promise.resolve({ imported: 1 })
    })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.pagination.page = 3

    const target = { files: [new File(['x'], 'a.xlsx')], value: 'a.xlsx' }
    await vm.handleFileChange({ target })
    await flushPromises()
    expect(api.importData).toHaveBeenCalledWith(
      target.files[0],
      'incremental',
      expect.any(Function)
    )
    expect(logInfo).toHaveBeenCalledWith('上传进度: 42%')
    expect(ElMessage.success).toHaveBeenCalledWith('导入成功')
    expect(vm.pagination.page).toBe(1)
    expect(target.value).toBe('')
  })

  it('handleFileChange 失败：提示导入失败且清空 input.value', async () => {
    api.importData.mockRejectedValueOnce(new Error('bad'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const target = { files: [new File(['x'], 'a.xlsx')], value: 'a.xlsx' }
    await vm.handleFileChange({ target })
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('导入失败')
    expect(target.value).toBe('')
  })
})
