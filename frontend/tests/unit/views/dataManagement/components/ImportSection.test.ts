/**
 * views/dataManagement/components/ImportSection.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：onMounted 加载导入历史（data.items/items/失败）、模板下载成功/失败、
 * handleFileChange/handleExceed/handleClear（uploadRef 守卫）、
 * handleImport（未选文件早退、成功 success=true/false、异常）、
 * getStatusType 五分支、formatTime 两侧、
 * 模板：导入模式 radio v-model、开始导入/清除文件/确定按钮、结果对话框 v-model 与错误列表。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

const {
  ElMessage,
  mockDownloadTemplate,
  mockImportVillages,
  mockGetImportHistory,
  formatImportStatus,
} = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  mockDownloadTemplate: vi.fn(),
  mockImportVillages: vi.fn(),
  mockGetImportHistory: vi.fn(),
  formatImportStatus: vi.fn((s: string) => ({ text: `状态${s}`, type: 'info' })),
}))

vi.mock('element-plus', () => ({ ElMessage }))

vi.mock('@/api/import', () => ({
  downloadImportTemplateAndSave: mockDownloadTemplate,
  importVillages: mockImportVillages,
  getImportHistory: mockGetImportHistory,
  formatImportStatus,
  importEntities: vi.fn(),
}))

import ImportSection from '@/views/dataManagement/components/ImportSection.vue'

const rowA = {
  file_name: 'a.xlsx',
  status: 'completed',
  success_rows: 5,
  total_rows: 6,
  created_at: '2024-06-01 10:05:00',
}
const rowB = {
  file_name: 'b.xlsx',
  status: 'pending',
  success_rows: undefined,
  total_rows: 0,
  created_at: '',
}

function mountComp() {
  return mount(ImportSection, {
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
            '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /></div>',
          data() {
            return { rowA, rowB }
          },
        },
        'el-dialog': {
          name: 'ElDialog',
          template: '<div class="el-dialog-stub"><slot /><slot name="footer" /></div>',
          emits: ['update:modelValue'],
        },
        'el-radio-group': {
          name: 'ElRadioGroup',
          template: '<div class="el-radio-group-stub"><slot /></div>',
          emits: ['update:modelValue'],
        },
        'el-upload': {
          name: 'ElUpload',
          template: '<div class="el-upload-stub" />',
          methods: { clearFiles: vi.fn(), handleStart: vi.fn() },
        },
        'el-descriptions': {
          name: 'ElDescriptions',
          template: '<div class="el-descriptions-stub"><slot /></div>',
        },
        'el-descriptions-item': {
          name: 'ElDescriptionsItem',
          template: '<div class="el-descriptions-item-stub"><slot /></div>',
        },
        'el-divider': {
          name: 'ElDivider',
          template: '<div class="el-divider-stub"><slot /></div>',
        },
        'el-tag': { name: 'ElTag', template: '<span class="el-tag-stub"><slot /></span>' },
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
  formatImportStatus.mockImplementation((s: string) => ({ text: `状态${s}`, type: 'info' }))
  mockGetImportHistory.mockResolvedValue({ data: { items: [rowA, rowB] } })
  mockDownloadTemplate.mockResolvedValue(undefined)
  mockImportVillages.mockResolvedValue({
    success: true,
    total_rows: 6,
    success_rows: 5,
    failed_rows: 1,
    skipped_rows: 0,
    errors: [],
  })
})

describe('挂载与导入历史', () => {
  it('onMounted：data.items 形态；模板状态标签与结果列两侧', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(mockGetImportHistory).toHaveBeenCalledWith(1, 10)
    expect(vm.historyList).toEqual([rowA, rowB])
    expect(vm.loadingHistory).toBe(false)
    const text = wrapper.text()
    expect(text).toContain('状态completed')
    expect(text).toContain('5/6') // success_rows 有值
    expect(text).toContain('-') // rowB success_rows undefined
  })

  it('items 形态与失败兜底；刷新按钮', async () => {
    mockGetImportHistory.mockResolvedValue({ items: [rowA] })
    let wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).historyList).toEqual([rowA])

    mockGetImportHistory.mockRejectedValue(new Error('net'))
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).historyList).toEqual([])

    const refresh = wrapper
      .findAll('el-button-stub')
      .find((b: any) => b.text().trim() === '')
    expect(refresh).toBeTruthy()
    const base = mockGetImportHistory.mock.calls.length
    await refresh.trigger('click')
    await flushPromises()
    expect(mockGetImportHistory.mock.calls.length).toBe(base + 1)
  })
})

describe('模板下载', () => {
  it('成功调用 + 失败提示（按钮点击）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await findBtn(wrapper, '下载导入模板').trigger('click')
    await flushPromises()
    expect(mockDownloadTemplate).toHaveBeenCalledWith('supported_village', '帮扶村')

    mockDownloadTemplate.mockRejectedValue(new Error('net'))
    await findBtn(wrapper, '下载导入模板').trigger('click')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('模板下载失败，请重试')
  })
})

describe('文件选择与清除', () => {
  it('handleFileChange 保存 raw；handleClear 清空；handleExceed 换文件', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const clearFiles = vi.fn()
    const handleStart = vi.fn()
    vm.uploadRef = { clearFiles, handleStart }
    const file = { raw: { name: 'a.xlsx' } } as any
    vm.handleFileChange(file)
    expect(vm.selectedFile).toEqual({ name: 'a.xlsx' })

    const next = { raw: { name: 'b.xlsx' } } as any
    vm.handleExceed([next] as any)
    expect(clearFiles).toHaveBeenCalled()
    expect(handleStart).toHaveBeenCalledWith(next)

    vm.handleClear()
    expect(clearFiles).toHaveBeenCalled()
    expect(vm.selectedFile).toBeNull()
  })
})

describe('handleImport', () => {
  it('未选文件 → 警告早退', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await (wrapper.vm as any).handleImport()
    expect(ElMessage.warning).toHaveBeenCalledWith('请先选择文件')
    expect(mockImportVillages).not.toHaveBeenCalled()
  })

  it('成功（success=true）：提示 + emit + 清空 + 刷新历史；「开始导入」按钮触发', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.selectedFile = { name: 'a.xlsx' } as any
    await nextTick()
    await findBtn(wrapper, '开始导入').trigger('click')
    await flushPromises()
    expect(mockImportVillages).toHaveBeenCalledWith({ name: 'a.xlsx' }, 'incremental')
    expect(ElMessage.success).toHaveBeenCalledWith('导入成功：5条记录')
    expect(wrapper.emitted('import-complete')).toHaveLength(1)
    expect(vm.showResultDialog).toBe(true)
    expect(vm.importResult).toBeTruthy()
    expect(vm.selectedFile).toBeNull()
    expect(vm.importing).toBe(false)
  })

  it('成功但 success=false → 警告失败数；错误列表渲染', async () => {
    mockImportVillages.mockResolvedValue({
      success: false,
      total_rows: 3,
      success_rows: 1,
      failed_rows: 2,
      skipped_rows: 0,
      errors: [{ row_number: 2, field_name: 'name', message: '为空' }],
    })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.selectedFile = { name: 'c.xlsx' } as any
    await vm.handleImport()
    expect(ElMessage.warning).toHaveBeenCalledWith('导入完成，但有2条失败')
    expect(wrapper.emitted('import-complete')).toBeUndefined()
    expect(vm.importResult.errors).toHaveLength(1)
    await nextTick()
    expect(wrapper.text()).toContain('错误详情')
  })

  it('异常 → error；importMode 切换为 full 后载荷', async () => {
    mockImportVillages.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.selectedFile = { name: 'd.xlsx' } as any
    await nextTick()
    wrapper.findAllComponents({ name: 'ElRadioGroup' })[0].vm.$emit('update:modelValue', 'full')
    expect(vm.importMode).toBe('full')
    await vm.handleImport()
    expect(ElMessage.error).toHaveBeenCalledWith('导入失败，请检查文件格式')
    expect(vm.importing).toBe(false)
  })
})

describe('工具函数与对话框', () => {
  it('getStatusType 五分支', () => {
    const wrapper = mountComp()
    const vm = wrapper.vm as any
    expect(vm.getStatusType('completed')).toBe('success')
    expect(vm.getStatusType('failed')).toBe('danger')
    expect(vm.getStatusType('processing')).toBe('warning')
    expect(vm.getStatusType('pending')).toBe('info')
    expect(vm.getStatusType('weird')).toBe('info')
  })

  it('formatTime：空串与分钟补零', () => {
    const wrapper = mountComp()
    const vm = wrapper.vm as any
    expect(vm.formatTime('')).toBe('-')
    expect(vm.formatTime('2024-01-01T08:05:00')).toContain('8:05')
  })

  it('结果对话框：v-model 同步、「确定」按钮关闭', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.showResultDialog = true
    vm.importResult = { total_rows: 1, success_rows: 1, failed_rows: 0, skipped_rows: 0, errors: [] }
    await nextTick()
    await findBtn(wrapper, '确定').trigger('click')
    expect(vm.showResultDialog).toBe(false)
    vm.showResultDialog = true
    await nextTick()
    wrapper.findAllComponents({ name: 'ElDialog' })[0].vm.$emit('update:modelValue', false)
    expect(vm.showResultDialog).toBe(false)
  })
})
