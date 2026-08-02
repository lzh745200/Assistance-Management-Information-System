/**
 * views/approval/Overview.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：stats 计算属性（全部计数器与类型判断）、statusLabel/getTypeLabel/statusTagType/getTypeTagType
 * 全部映射与兜底、formatDate、filteredTasks（applicant/dateRange 两侧）、loadData（status 参数/失败）、
 * resetFilters、saveReminder、handleAutoApproveAll（空早退/确认成功/取消）、
 * handleExportLog（空警告/导出 CSV）、模板按钮与 v-model。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

const {
  ElMessage,
  confirmMock,
  mockGetAllTasks,
  mockAutoApproveAll,
  formatMock,
  exportUtilMock,
} = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  confirmMock: vi.fn(),
  mockGetAllTasks: vi.fn(),
  mockAutoApproveAll: vi.fn(),
  formatMock: { formatDateTimeLocale: vi.fn((d: any) => (d ? '已格式化' : '-')) },
  exportUtilMock: { exportToCSV: vi.fn() },
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

vi.mock('@/api/approval', () => ({
  getAllTasks: mockGetAllTasks,
  autoApproveAll: mockAutoApproveAll,
}))

vi.mock('@/utils', () => ({
  exportUtil: exportUtilMock,
  format: formatMock,
}))

import Overview from '@/views/approval/Overview.vue'

const now = Date.now()
const todayISO = new Date(now).toISOString()
const oldISO = new Date(now - 30 * 24 * 3600 * 1000).toISOString() // 30 天前 → overdue

// 覆盖全部状态/类型组合
const tasks = [
  { id: 1, title: 'T1', status: 'pending', type: 'data_change', applicant_name: '张三', created_at: oldISO, reviewed_at: '', reviewer_name: '审批员' },
  { id: 2, title: 'T2', status: 'pending', type: 'data_import', applicant_name: '李四', created_at: todayISO },
  { id: 3, title: 'T3', status: 'approved', type: 'data_export', applicant_name: '王五', created_at: todayISO },
  { id: 4, title: 'T4', status: 'rejected', type: 'system', applicant_name: '赵六', created_at: todayISO },
  { id: 5, title: 'T5', status: 'withdrawn', type: 'export', applicant_name: '钱七', created_at: todayISO },
  { id: 6, title: 'T6', status: 'pending', type: 'DATA_IMPORT', applicant_name: '孙八', created_at: todayISO },
  { id: 7, title: 'T7', status: 'approved', type: 'pending', applicant_name: '周九', created_at: todayISO },
  { id: 8, title: 'T8', status: 'approved', type: 'completed', applicant_name: '吴十', created_at: todayISO },
  { id: 9, title: 'T9', status: 'rejected', type: 'failed', applicant_name: '郑一', created_at: todayISO },
  { id: 10, title: 'T10', status: 'pending', type: 'weird', applicant_name: '何二', created_at: todayISO },
]

function mountComp() {
  return mount(Overview, {
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
            return { rowA: tasks[0], rowB: tasks[1], rowC: tasks[4] }
          },
        },
        'el-select': {
          name: 'ElSelect',
          template: '<div class="el-select-stub"><slot /></div>',
          emits: ['update:modelValue'],
        },
        'el-input': {
          name: 'ElInput',
          template: '<div class="el-input-stub" />',
          emits: ['update:modelValue'],
        },
        'el-date-picker': {
          name: 'ElDatePicker',
          template: '<div class="el-date-picker-stub" />',
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
            '<button class="el-switch-stub" @click="$emit(\'update:modelValue\', !modelValue)" />',
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
  formatMock.formatDateTimeLocale.mockImplementation((d: any) => (d ? '已格式化' : '-'))
  mockGetAllTasks.mockResolvedValue(tasks)
  mockAutoApproveAll.mockResolvedValue({ success: [1, 2], failed: [{ id: 3, reason: 'x' }] })
  confirmMock.mockResolvedValue('confirm')
})

describe('挂载与统计', () => {
  it('onMounted 加载任务；stats 全计数器与类型判断', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(mockGetAllTasks).toHaveBeenCalledWith({})
    expect(vm.allTasks).toHaveLength(10)
    const s = vm.stats
    expect(s.total).toBe(10)
    expect(s.pending).toBe(4) // T1 T2 T6 T10
    expect(s.approved).toBe(3)
    expect(s.rejected).toBe(2)
    expect(s.overdue).toBe(1) // T1 pending 且 30 天前
    expect(s.today).toBe(9)
    expect(s.exports).toBe(2) // T3 data_export, T5 export
    expect(s.dataChanges).toBe(5) // T1/T2/T3/T5/T6
    expect(vm.loading).toBe(false)
  })

  it('filteredTasks：applicant 过滤（匹配/不匹配/缺失 applicant_name）与 dateRange 过滤', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.filters.applicant = '张三'
    expect(vm.filteredTasks).toHaveLength(1)
    vm.filters.applicant = '不存在'
    expect(vm.filteredTasks).toHaveLength(0)
    vm.filters.applicant = ''
    vm.allTasks.push({ id: 99, title: 'T99', status: 'pending', type: '', created_at: todayISO } as any)
    vm.filters.applicant = 'x' // 缺失 applicant_name → '' 兜底分支
    expect(vm.filteredTasks).toHaveLength(0)
    vm.filters.applicant = ''
    vm.filters.dateRange = [oldISO, todayISO]
    expect(vm.filteredTasks.length).toBeGreaterThan(0)
    expect(vm.filteredTasks.every((t: any) => new Date(t.created_at).getTime() >= new Date(oldISO).getTime())).toBe(true)
    vm.filters.dateRange = null
    expect(vm.filteredTasks).toHaveLength(11)
  })

  it('loadData：status 过滤参数；失败 → 空列表', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.filters.status = 'data_change'
    await vm.loadData()
    expect(mockGetAllTasks).toHaveBeenCalledWith({ entity_type: 'data_change' })

    mockGetAllTasks.mockRejectedValue(new Error('net'))
    await vm.loadData()
    expect(vm.allTasks).toEqual([])
    expect(vm.loading).toBe(false)
  })

  it('resetFilters 清空并重载；「查询」「重置」按钮', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.filters.status = 'system'
    vm.filters.applicant = 'x'
    vm.filters.dateRange = [oldISO, todayISO]
    await findBtn(wrapper, '重置').trigger('click')
    await flushPromises()
    expect(vm.filters.status).toBe('')
    expect(vm.filters.applicant).toBe('')
    expect(vm.filters.dateRange).toBeNull()

    const base = mockGetAllTasks.mock.calls.length
    await findBtn(wrapper, '查询').trigger('click')
    await flushPromises()
    expect(mockGetAllTasks.mock.calls.length).toBe(base + 1)
  })
})

describe('标签映射函数', () => {
  it('statusLabel/getTypeLabel 映射与兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.statusLabel('pending')).toBe('待处理')
    expect(vm.statusLabel('approved')).toBe('已完成')
    expect(vm.statusLabel('rejected')).toBe('已驳回')
    expect(vm.statusLabel('withdrawn')).toBe('已撤回')
    expect(vm.statusLabel('weird')).toBe('weird')
    expect(vm.getTypeLabel('data_change')).toBe('数据变更')
    expect(vm.getTypeLabel('data_import')).toBe('数据导入')
    expect(vm.getTypeLabel('data_export')).toBe('数据导出')
    expect(vm.getTypeLabel('system')).toBe('系统设置')
    expect(vm.getTypeLabel('')).toBe('其他')
    expect(vm.getTypeLabel('unknown')).toBe('unknown')
  })

  it('statusTagType 映射与兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.statusTagType('pending')).toBe('warning')
    expect(vm.statusTagType('approved')).toBe('success')
    expect(vm.statusTagType('rejected')).toBe('danger')
    expect(vm.statusTagType('withdrawn')).toBe('info')
    expect(vm.statusTagType('weird')).toBe('info')
  })

  it('getTypeTagType 全部分支', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.getTypeTagType('data_import')).toBe('primary')
    expect(vm.getTypeTagType('data_change')).toBe('primary')
    expect(vm.getTypeTagType('data_export')).toBe('success')
    expect(vm.getTypeTagType('system')).toBe('info')
    expect(vm.getTypeTagType('pending')).toBe('warning')
    expect(vm.getTypeTagType('approved')).toBe('success')
    expect(vm.getTypeTagType('completed')).toBe('success')
    expect(vm.getTypeTagType('rejected')).toBe('danger')
    expect(vm.getTypeTagType('failed')).toBe('danger')
    expect(vm.getTypeTagType('misc')).toBe('info')
    expect(vm.getTypeTagType(undefined as any)).toBe('info') // type 缺失 → ''
  })

  it('formatDate 委托 format 工具', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.formatDate('2024-01-01')).toBe('已格式化')
    expect(vm.formatDate('')).toBe('-')
  })
})

describe('提醒设置与自动审批', () => {
  it('saveReminder 提示；overdueDays/开关 v-model', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await findBtn(wrapper, '保存设置').trigger('click')
    expect(ElMessage.success).toHaveBeenCalledWith('提醒规则已保存')

    wrapper.findAllComponents({ name: 'ElInputNumber' })[0].vm.$emit('update:modelValue', 7)
    expect(vm.reminderConfig.overdueDays).toBe(7)
    const switches = wrapper.findAllComponents({ name: 'ElSwitch' })
    await switches[0].trigger('click')
    expect(vm.reminderConfig.enabled).toBe(false)
  })

  it('handleAutoApproveAll：pending 为 0 → 早退；确认成功 → 提示+重载；取消静默', async () => {
    mockGetAllTasks.mockResolvedValueOnce([
      { id: 1, title: 'A', status: 'approved', type: '', created_at: todayISO },
    ])
    let wrapper = mountComp()
    await flushPromises()
    await (wrapper.vm as any).handleAutoApproveAll()
    expect(confirmMock).not.toHaveBeenCalled()

    wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.handleAutoApproveAll()
    expect(confirmMock).toHaveBeenCalledWith(
      '确定要一键处理所有 4 个待处理任务吗？',
      '一键全部处理',
      expect.objectContaining({ type: 'warning' })
    )
    expect(mockAutoApproveAll).toHaveBeenCalledWith('单机版一键批量处理')
    expect(ElMessage.success).toHaveBeenCalledWith(
      '批量处理完成：成功 2，失败 1'
    )
    expect(mockGetAllTasks).toHaveBeenCalled()
    expect(vm.autoApproving).toBe(false)

    confirmMock.mockRejectedValueOnce(new Error('cancel'))
    await vm.handleAutoApproveAll()
    expect(vm.autoApproving).toBe(false)
  })

  it('「一键通过全部」按钮点击触发', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await findBtn(wrapper, '一键通过全部').trigger('click')
    await flushPromises()
    expect(mockAutoApproveAll).toHaveBeenCalled()
  })
})

describe('导出日志', () => {
  it('空列表 → 警告早退', async () => {
    mockGetAllTasks.mockResolvedValueOnce([])
    const wrapper = mountComp()
    await flushPromises()
    await (wrapper.vm as any).handleExportLog()
    expect(ElMessage.warning).toHaveBeenCalledWith('当前没有可导出的数据')
    expect(exportUtilMock.exportToCSV).not.toHaveBeenCalled()
  })

  it('非空 → 导出 CSV + 提示；「导出当前查询结果」按钮；缺字段 ?? 兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // 覆盖 title/applicant_name/type 缺失的 ?? 兜底
    vm.allTasks.push({
      id: 88,
      status: 'pending',
      created_at: todayISO,
      reviewer_name: undefined,
      reviewed_at: undefined,
    } as any)
    await findBtn(wrapper, '导出当前查询结果').trigger('click')
    expect(exportUtilMock.exportToCSV).toHaveBeenCalled()
    const data = exportUtilMock.exportToCSV.mock.calls[0][0]
    expect(data[0]).toMatchObject({
      操作内容: 'T1',
      操作人: '张三',
      类型: '数据变更',
      状态: '待处理',
    })
    expect(data[10]).toMatchObject({
      操作内容: '',
      操作人: '',
      类型: '其他',
      状态: '待处理',
      处理人: '',
      处理时间: '-',
    })
    expect(ElMessage.success).toHaveBeenCalledWith('操作日志已导出')
  })
})

describe('表单 v-model', () => {
  it('status/applicant/dateRange 同步', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const byName = (n: string) => wrapper.findAllComponents({ name: n })
    byName('ElSelect')[0].vm.$emit('update:modelValue', 'data_export')
    expect(vm.filters.status).toBe('data_export')
    byName('ElInput')[0].vm.$emit('update:modelValue', '某人')
    expect(vm.filters.applicant).toBe('某人')
    byName('ElDatePicker')[0].vm.$emit('update:modelValue', [oldISO, todayISO])
    expect(vm.filters.dateRange).toEqual([oldISO, todayISO])
  })
})
