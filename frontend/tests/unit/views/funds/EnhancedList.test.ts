/**
 * views/funds/EnhancedList.vue 覆盖率攻坚
 * 覆盖：初始化加载、统计卡片(computed fallback/server)、搜索/重置/分页、
 * 状态过滤、CRUD 全路径、快速审批/拨付、导出/模板下载、
 * 批量删除/导出/取消选择、下拉选项加载异常、错误态重试。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const {
  ElMessage,
  confirmMock,
  mockGet,
  mockDel,
  mockApiRequest,
  fundApiMock,
  getVillagesMock,
  schoolsListMock,
  downloadTemplateMock,
  pushSafeMock,
  logError,
} = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  confirmMock: vi.fn(),
  mockGet: vi.fn(),
  mockDel: vi.fn(),
  mockApiRequest: vi.fn(),
  fundApiMock: {
    exportList: vi.fn(),
    approve: vi.fn(),
    allocate: vi.fn(),
  },
  getVillagesMock: vi.fn(),
  schoolsListMock: vi.fn(),
  downloadTemplateMock: vi.fn(),
  pushSafeMock: vi.fn(),
  logError: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: vi.fn(),
  put: vi.fn(),
  del: mockDel,
  apiRequest: mockApiRequest,
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('@/api/funds', () => ({
  fundApi: fundApiMock,
}))

vi.mock('@/api/supportedVillage', () => ({
  getSupportedVillages: getVillagesMock,
}))

vi.mock('@/api/schools', () => ({
  schoolsApi: { list: schoolsListMock },
}))

vi.mock('@/api/import', () => ({
  downloadImportTemplateAndSave: downloadTemplateMock,
}))

vi.mock('@/config/enums', () => ({
  getFundTypeLabel: (t: string) => `类型_${t}`,
  getFundStatusLabel: (s: string) => `状态_${s}`,
}))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ pushSafe: pushSafeMock }),
}))

vi.mock('@/utils/logger', () => ({
  logger: { error: logError, warn: vi.fn(), info: vi.fn(), debug: vi.fn() },
}))

import EnhancedList from '@/views/funds/EnhancedList.vue'

const sampleFund = {
  id: 1,
  name: '测试经费',
  type: 'project',
  amount: 100.5,
  status: 'pending',
  project_name: '项目A',
  source: '财政拨款',
  date: '2024-01-01',
  project_id: 5,
  health_score: 85,
  lifecycle_phase: 1,
}

const sampleFund2 = {
  id: 2,
  name: '已拨付经费',
  type: 'operation',
  amount: 200,
  status: 'allocated',
  project_name: '项目B',
  source: '自筹',
  date: '2024-02-01',
}

function defaultGetImpl(url: string) {
  if (url === '/funds/statistics/overview') {
    return Promise.resolve({
      data: {
        total_amount: 500,
        total_allocated: 300,
        by_status: { pending: { count: 3 }, planned: { count: 2 } },
        total_count: 10,
      },
    })
  }
  return Promise.resolve({ data: {} })
}

function mountComp() {
  return mount(EnhancedList, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-table': {
          template:
            '<div class="el-table-stub"><slot name="empty" /><slot name="default" /></div>',
        },
        'el-table-column': {
          template: '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /></div>',
          data() {
            return {
              rowA: { ...sampleFund },
              rowB: { ...sampleFund2, status: 'approved', health_score: null, lifecycle_phase: null },
            }
          },
        },
        'el-card': { template: '<div class="el-card-stub"><slot /></div>' },
        'el-form': { template: '<div class="el-form-stub"><slot /></div>' },
        'el-form-item': { template: '<div class="el-form-item-stub"><slot /></div>' },
        'el-input': { template: '<div class="el-input-stub" />' },
        'el-select': { template: '<div class="el-select-stub"><slot /></div>' },
        'el-option': { template: '<div class="el-option-stub" />' },
        'el-button': {
          template: '<button class="el-button-stub" @click="$emit(\'click\')"><slot /></button>',
          emits: ['click'],
        },
        'el-pagination': { template: '<div class="el-pagination-stub" />' },
        'el-tag': { template: '<span class="el-tag-stub"><slot /></span>' },
        'el-icon': { template: '<span class="el-icon-stub"><slot /></span>' },
        'el-link': {
          template: '<a class="el-link-stub" @click="$emit(\'click\')"><slot /></a>',
          emits: ['click'],
        },
        'el-popconfirm': {
          template: '<div class="el-popconfirm-stub"><slot name="reference" /></div>',
        },
        'el-progress': { template: '<div class="el-progress-stub" />' },
        'el-result': { template: '<div class="el-result-stub"><slot name="extra" /></div>' },
        'el-empty': { template: '<div class="el-empty-stub" />' },
      },
    },
  })
}

beforeEach(() => {
  vi.resetAllMocks()
  mockGet.mockImplementation(defaultGetImpl)
  mockApiRequest.mockResolvedValue({ data: { items: [sampleFund], total: 1 } })
  mockDel.mockResolvedValue({})
  fundApiMock.exportList.mockResolvedValue({})
  fundApiMock.approve.mockResolvedValue({})
  fundApiMock.allocate.mockResolvedValue({})
  getVillagesMock.mockResolvedValue({ data: { items: [{ id: 1, village_name: '村A' }] } })
  schoolsListMock.mockResolvedValue({ data: { items: [{ id: 1, school_name: '校A' }] } })
  downloadTemplateMock.mockResolvedValue({})
  confirmMock.mockResolvedValue(undefined)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('挂载与初始化', () => {
  it('onMounted 并行加载经费列表/统计/村庄/学校', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(mockApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({ method: 'GET', url: '/funds' })
    )
    expect(vm.tableData).toHaveLength(1)
    expect(vm.total).toBe(1)
    expect(mockGet).toHaveBeenCalledWith('/funds/statistics/overview')
    expect(vm.serverStats).toBeTruthy()
    expect(getVillagesMock).toHaveBeenCalledWith({ page: 1, page_size: 200 })
    expect(vm.villageOptions).toEqual([{ id: 1, name: '村A' }])
    expect(schoolsListMock).toHaveBeenCalledWith({ page: 1, page_size: 200 })
    expect(vm.schoolOptions).toEqual([{ id: 1, name: '校A' }])
  })

  it('loadStats 异常 → 不阻塞', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url === '/funds/statistics/overview') return Promise.reject(new Error('net'))
      return defaultGetImpl(url)
    })
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).serverStats).toBeNull()
  })

  it('loadVillageOptions 异常 → 空列表', async () => {
    getVillagesMock.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).villageOptions).toEqual([])
  })

  it('loadSchoolOptions 异常 → 空列表', async () => {
    schoolsListMock.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).schoolOptions).toEqual([])
  })

  it('fetchData 失败 → error=true 并提示', async () => {
    mockApiRequest.mockRejectedValue(new Error('boom'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.error).toBe(true)
    expect(logError).toHaveBeenCalled()
    expect(ElMessage.error).toHaveBeenCalledWith('数据加载失败，请稍后重试')
    expect(vm.loading).toBe(false)
  })

  it('fetchData：resData.data.items 嵌套格式也能解析', async () => {
    mockApiRequest.mockResolvedValue({
      data: { data: { items: [sampleFund, sampleFund2], total: 2 } },
    })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.tableData).toHaveLength(2)
    expect(vm.total).toBe(2)
  })

  it('fetchData：数组直返格式也能解析', async () => {
    mockApiRequest.mockResolvedValue({ data: [sampleFund] })
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).tableData).toHaveLength(1)
  })
})

describe('统计卡片 computed', () => {
  it('serverStats 可用 → 使用服务端数据', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.stats.totalAmount).toBe('500.00')
    expect(vm.stats.allocatedAmount).toBe('300.00')
    expect(vm.stats.pendingCount).toBe(3)
    expect(vm.stats.plannedCount).toBe(2)
    expect(vm.stats.totalCount).toBe(10)
  })

  it('serverStats 不可用 → 回退到当前页数据', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url === '/funds/statistics/overview') return Promise.resolve({ data: null })
      return defaultGetImpl(url)
    })
    mockApiRequest.mockResolvedValue({
      data: { items: [sampleFund, sampleFund2], total: 2 },
    })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.stats.totalAmount).toBe('300.50')
    expect(vm.stats.allocatedAmount).toBe('200.00')
    expect(vm.stats.pendingCount).toBe(1)
    expect(vm.stats.plannedCount).toBe(0)
    expect(vm.stats.totalCount).toBe(2)
  })
})

describe('formatAmount', () => {
  it('正常数字 → 千分位+2位小数', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.formatAmount(1234567.8)).toBe('1,234,567.80')
  })
  it('NaN → 0.00', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.formatAmount('abc')).toBe('0.00')
  })
})

describe('搜索 / 重置 / 分页 / 状态过滤', () => {
  it('handleSearch 回第 1 页并刷新', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.currentPage = 3
    vm.filterForm.keyword = '测试'
    vm.filterForm.type = 'project'
    mockApiRequest.mockClear()
    vm.handleSearch()
    await flushPromises()
    expect(vm.currentPage).toBe(1)
    expect(mockApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        params: expect.objectContaining({ keyword: '测试', fund_type: 'project' }),
      })
    )
  })

  it('handleReset 清空所有筛选并刷新', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.filterForm.keyword = 'x'
    vm.filterForm.type = 'project'
    vm.filterForm.status = 'pending'
    vm.filterForm.village_id = 1
    vm.filterForm.school_id = 2
    mockApiRequest.mockClear()
    vm.handleReset()
    await flushPromises()
    expect(vm.filterForm).toEqual({
      keyword: '',
      type: '',
      status: '',
      village_id: '',
      school_id: '',
    })
    expect(mockApiRequest).toHaveBeenCalled()
  })

  it('filterByStatus 设置状态并刷新', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    mockApiRequest.mockClear()
    vm.filterByStatus('allocated')
    await flushPromises()
    expect(vm.filterForm.status).toBe('allocated')
    expect(vm.currentPage).toBe(1)
    expect(mockApiRequest).toHaveBeenCalled()
  })

  it('handleSizeChange 回第 1 页', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.currentPage = 5
    mockApiRequest.mockClear()
    vm.handleSizeChange()
    await flushPromises()
    expect(vm.currentPage).toBe(1)
  })

  it('handlePageChange 刷新', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    mockApiRequest.mockClear()
    vm.handlePageChange()
    await flushPromises()
    expect(mockApiRequest).toHaveBeenCalled()
  })
})

describe('导航操作', () => {
  it('handleCreate → pushSafe /funds/create', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.handleCreate()
    expect(pushSafeMock).toHaveBeenCalledWith('/funds/create')
  })
  it('handleView → pushSafe /funds/{id}', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.handleView({ id: 42 })
    expect(pushSafeMock).toHaveBeenCalledWith('/funds/42')
  })
  it('handleEdit → pushSafe /funds/{id}/edit', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.handleEdit({ id: 42 })
    expect(pushSafeMock).toHaveBeenCalledWith('/funds/42/edit')
  })
})

describe('删除经费', () => {
  it('删除成功 → 列表过滤 + 刷新 + 统计', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    mockApiRequest.mockClear()
    mockGet.mockClear()
    await vm.handleDelete(sampleFund)
    expect(mockDel).toHaveBeenCalledWith('/funds/1')
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    expect(vm.tableData).toEqual([])
    expect(vm.total).toBe(0)
    expect(mockApiRequest).toHaveBeenCalled()
    expect(mockGet).toHaveBeenCalledWith('/funds/statistics/overview')
  })

  it('删除失败 → 展示 detail', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    mockDel.mockRejectedValueOnce({ response: { data: { detail: '存在关联' } } })
    await vm.handleDelete(sampleFund)
    expect(ElMessage.error).toHaveBeenCalledWith('删除失败: 存在关联')
  })

  it('删除失败 → 兜底 message', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    mockDel.mockRejectedValueOnce(new Error('网络错误'))
    await vm.handleDelete(sampleFund)
    expect(ElMessage.error).toHaveBeenCalledWith('删除失败: 网络错误')
  })

  it('重复删除（loading 中）→ 直接返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.deleting[1] = true
    mockDel.mockClear()
    await vm.handleDelete(sampleFund)
    expect(mockDel).not.toHaveBeenCalled()
  })
})

describe('快速审批 / 拨付', () => {
  it('quickApprove 成功 → 刷新列表和统计', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    mockApiRequest.mockClear()
    await vm.quickApprove(sampleFund)
    expect(fundApiMock.approve).toHaveBeenCalledWith(1, {})
    expect(ElMessage.success).toHaveBeenCalledWith('审批成功')
    expect(mockApiRequest).toHaveBeenCalled()
  })

  it('quickApprove 失败 → detail', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    fundApiMock.approve.mockRejectedValueOnce({ response: { data: { detail: '无权限' } } })
    await vm.quickApprove(sampleFund)
    expect(ElMessage.error).toHaveBeenCalledWith('无权限')
  })

  it('quickApprove 重复 → 直接返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.approving[1] = true
    fundApiMock.approve.mockClear()
    await vm.quickApprove(sampleFund)
    expect(fundApiMock.approve).not.toHaveBeenCalled()
  })

  it('quickAllocate 成功 → 刷新列表和统计', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    mockApiRequest.mockClear()
    await vm.quickAllocate({ ...sampleFund, status: 'approved' })
    expect(fundApiMock.allocate).toHaveBeenCalledWith(1, {})
    expect(ElMessage.success).toHaveBeenCalledWith('拨付成功')
    expect(mockApiRequest).toHaveBeenCalled()
  })

  it('quickAllocate 失败 → 兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    fundApiMock.allocate.mockRejectedValueOnce(new Error('net'))
    await vm.quickAllocate({ ...sampleFund, status: 'approved' })
    expect(ElMessage.error).toHaveBeenCalledWith('拨付失败')
  })

  it('quickAllocate 重复 → 直接返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.allocating[1] = true
    fundApiMock.allocate.mockClear()
    await vm.quickAllocate(sampleFund)
    expect(fundApiMock.allocate).not.toHaveBeenCalled()
  })
})

describe('导出 / 模板下载', () => {
  it('handleExport 成功', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.filterForm.keyword = 'kw'
    vm.filterForm.type = 'project'
    vm.filterForm.status = 'pending'
    await vm.handleExport()
    expect(fundApiMock.exportList).toHaveBeenCalledWith({
      search: 'kw',
      type: 'project',
      status: 'pending',
    })
    expect(vm.exporting).toBe(false)
  })

  it('handleExport 失败 → 错误提示', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    fundApiMock.exportList.mockRejectedValueOnce(new Error('net'))
    await vm.handleExport()
    expect(ElMessage.error).toHaveBeenCalledWith('导出失败')
    expect(vm.exporting).toBe(false)
  })

  it('handleExport 重复 → 直接返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.exporting = true
    fundApiMock.exportList.mockClear()
    await vm.handleExport()
    expect(fundApiMock.exportList).not.toHaveBeenCalled()
  })

  it('handleDownloadTemplate 成功', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.handleDownloadTemplate()
    expect(downloadTemplateMock).toHaveBeenCalledWith('fund', '经费')
  })

  it('handleDownloadTemplate 失败 → 错误提示', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    downloadTemplateMock.mockRejectedValueOnce(new Error('net'))
    await vm.handleDownloadTemplate()
    expect(ElMessage.error).toHaveBeenCalledWith('模板下载失败，请重试')
  })
})

describe('批量操作', () => {
  it('handleSelectionChange → 更新 selectedRows', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.handleSelectionChange([sampleFund, sampleFund2])
    expect(vm.selectedRows).toHaveLength(2)
  })

  it('clearSelection → 调用 tableRef.clearSelection 并清空', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.tableRef = { clearSelection: vi.fn() }
    vm.selectedRows = [sampleFund]
    vm.clearSelection()
    expect(vm.tableRef.clearSelection).toHaveBeenCalled()
    expect(vm.selectedRows).toEqual([])
  })

  it('handleBatchDelete 成功 → 部分成功提示', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.selectedRows = [sampleFund, { ...sampleFund2, id: 999 }]
    mockDel.mockImplementation((url: string) => {
      if (url.includes('999')) return Promise.reject(new Error('not found'))
      return Promise.resolve({})
    })
    mockApiRequest.mockClear()
    await vm.handleBatchDelete()
    expect(confirmMock).toHaveBeenCalledWith(
      expect.stringContaining('2'),
      '批量删除确认',
      expect.any(Object)
    )
    expect(ElMessage.success).toHaveBeenCalledWith('成功删除 1 条记录')
    expect(ElMessage.warning).toHaveBeenCalledWith('1 条记录删除失败')
    expect(vm.batchDeleting).toBe(false)
    expect(mockApiRequest).toHaveBeenCalled()
  })

  it('handleBatchDelete 取消确认 → 不执行', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.selectedRows = [sampleFund]
    confirmMock.mockRejectedValueOnce('cancel')
    mockDel.mockClear()
    await vm.handleBatchDelete()
    expect(mockDel).not.toHaveBeenCalled()
  })

  it('handleBatchDelete 空选择 → 直接返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.selectedRows = []
    confirmMock.mockClear()
    await vm.handleBatchDelete()
    expect(confirmMock).not.toHaveBeenCalled()
  })

  it('handleBatchExport 成功', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.handleBatchExport()
    expect(fundApiMock.exportList).toHaveBeenCalledWith({})
    expect(vm.exporting).toBe(false)
  })

  it('handleBatchExport 失败 → 错误提示', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    fundApiMock.exportList.mockRejectedValueOnce(new Error('net'))
    await vm.handleBatchExport()
    expect(ElMessage.error).toHaveBeenCalledWith('导出失败')
  })

  it('handleBatchExport 重复 → 直接返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.exporting = true
    fundApiMock.exportList.mockClear()
    await vm.handleBatchExport()
    expect(fundApiMock.exportList).not.toHaveBeenCalled()
  })
})

describe('字典映射函数', () => {
  it('getStatusType 全映射与兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.getStatusType('pending')).toBe('warning')
    expect(vm.getStatusType('planned')).toBe('info')
    expect(vm.getStatusType('approved')).toBe('primary')
    expect(vm.getStatusType('allocated')).toBe('info')
    expect(vm.getStatusType('in_use')).toBe('primary')
    expect(vm.getStatusType('completed')).toBe('success')
    expect(vm.getStatusType('audited')).toBe('success')
    expect(vm.getStatusType('unknown')).toBe('info')
  })
})

describe('下拉选项字段兜底', () => {
  it('villageOptions：village_name/name/兜底', async () => {
    getVillagesMock.mockResolvedValue({
      data: {
        items: [
          { id: 1, village_name: 'V1' },
          { id: 2, name: 'V2' },
          { id: 3 },
        ],
      },
    })
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).villageOptions).toEqual([
      { id: 1, name: 'V1' },
      { id: 2, name: 'V2' },
      { id: 3, name: '村3' },
    ])
  })

  it('schoolOptions：school_name/name/兜底', async () => {
    schoolsListMock.mockResolvedValue({
      data: {
        items: [
          { id: 1, school_name: 'S1' },
          { id: 2, name: 'S2' },
          { id: 3 },
        ],
      },
    })
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).schoolOptions).toEqual([
      { id: 1, name: 'S1' },
      { id: 2, name: 'S2' },
      { id: 3, name: '学校3' },
    ])
  })

  it('villageOptions：数组直返格式', async () => {
    getVillagesMock.mockResolvedValue({ data: [{ id: 1, village_name: '直返村' }] })
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).villageOptions).toEqual([{ id: 1, name: '直返村' }])
  })
})
