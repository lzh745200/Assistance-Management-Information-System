/**
 * views/dataManagement/components/BackupSection.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：onMounted 加载备份列表+定时配置（成功/失败）、snake_case 字段映射、
 * 创建备份（成功/后端失败/异常）、预览（成功/异常）、恢复（无选中早退/成功+定时刷新/后端失败/异常）、
 * 删除（确认/取消/后端失败）、定时配置加载与保存（成功/异常）、
 * 模板：创建按钮、定时开关 change、保存配置、刷新、行操作三按钮、三个对话框 v-model、表单控件 v-model。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

const {
  ElMessage,
  confirmMock,
  mockGetBackupList,
  mockGetBackupStats,
  mockRestoreBackup,
  mockDeleteBackup,
  mockGet,
  mockPost,
  mockPut,
} = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  confirmMock: vi.fn(),
  mockGetBackupList: vi.fn(),
  mockGetBackupStats: vi.fn(),
  mockRestoreBackup: vi.fn(),
  mockDeleteBackup: vi.fn(),
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  put: mockPut,
  del: vi.fn(),
  apiRequest: vi.fn(),
}))

vi.mock('@/api/backup', () => ({
  getBackupList: mockGetBackupList,
  restoreBackup: mockRestoreBackup,
  deleteBackup: mockDeleteBackup,
  getBackupStats: mockGetBackupStats,
  createBackup: vi.fn(),
}))

import BackupSection from '@/views/dataManagement/components/BackupSection.vue'

const rowA = {
  id: 1,
  filename: 'backup_a.zip',
  file_size: 2 * 1024 * 1024,
  created_at: '2024-06-01 10:00:00',
  description: '日常备份',
  compressed: true,
}
const rowB = {
  backup_id: 'b2',
  file_name: 'backup_b.zip',
  file_size: 1024,
  created_at: '2024-06-02 11:00:00',
  description: '',
  compressed: false,
}
const rowC = {
  id: 3,
  filename: 'db.sqlite',
  file_size: 10,
  created_at: '2024-06-03 12:00:00',
  description: '',
  compressed: false,
  compressed_size: 3,
  size: 10,
  name: 'db.sqlite',
}

function mountComp() {
  return mount(BackupSection, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot name="header" /><slot /></div>',
        },
        'el-statistic': {
          name: 'ElStatistic',
          props: ['value', 'title', 'formatter'],
          template:
            '<div class="el-statistic-stub">{{ formatter ? formatter(value) : value }}</div>',
        },
        'el-dialog': {
          name: 'ElDialog',
          template: '<div class="el-dialog-stub"><slot /><slot name="footer" /></div>',
          emits: ['update:modelValue'],
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
        'el-switch': {
          name: 'ElSwitch',
          props: ['modelValue'],
          template:
            '<button class="el-switch-stub" @click="$emit(\'update:modelValue\', !modelValue); $emit(\'change\')" />',
        },
        'el-select': {
          name: 'ElSelect',
          template: '<div class="el-select-stub"><slot /></div>',
          emits: ['update:modelValue'],
        },
        'el-input-number': {
          name: 'ElInputNumber',
          template: '<div class="el-input-number-stub" />',
          emits: ['update:modelValue'],
        },
        'el-time-select': {
          name: 'ElTimeSelect',
          template: '<div class="el-time-select-stub" />',
          emits: ['update:modelValue'],
        },
        'el-checkbox': {
          name: 'ElCheckbox',
          template: '<div class="el-checkbox-stub" />',
          emits: ['update:modelValue'],
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
  mockGetBackupList.mockResolvedValue({ items: [rowA, { ...rowB }] })
  mockGetBackupStats.mockResolvedValue({
    total_backups: 2,
    total_size: 2 * 1024 * 1024 + 1024,
    auto_backup_enabled: true,
  })
  mockGet.mockResolvedValue({ enabled: true, interval_hours: 12, keep_count: 10, running: true, time_of_day: '03:00' })
  mockRestoreBackup.mockResolvedValue({ success: true })
  mockDeleteBackup.mockResolvedValue({ success: true, message: '删除成功' })
  mockPost.mockResolvedValue({ success: true })
  mockPut.mockResolvedValue({})
  confirmMock.mockResolvedValue('confirm')
})

describe('挂载与加载', () => {
  it('onMounted：加载备份列表与统计、定时配置（snake_case 映射与 ?? 兜底）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    expect(mockGetBackupList).toHaveBeenCalled()
    expect(mockGetBackupStats).toHaveBeenCalled()
    expect(mockGet).toHaveBeenCalledWith('/system/backup/schedule')
    expect(vm.backups).toHaveLength(2)
    // snake_case 映射：file_name → filename, backup_id → id
    expect(vm.backups[1].filename).toBe('backup_b.zip')
    expect(vm.backups[1].id).toBe('b2')
    expect(vm.backups[0].filename).toBe('backup_a.zip')
    expect(vm.stats.total_backups).toBe(2)
    expect(vm.stats.auto_backup_enabled).toBe(true)
    expect(vm.scheduleConfig.enabled).toBe(true)
    expect(vm.scheduleConfig.interval_hours).toBe(12)
    expect(vm.scheduleConfig.keep_count).toBe(10)
    expect(vm.scheduleConfig.time_of_day).toBe('03:00')
    expect(vm.scheduleRunning).toBe(true)
    expect(vm.loading).toBe(false)
    // 模板渲染：统计卡片、已启用标签、定时运行提示
    const text = wrapper.text()
    expect(text).toContain('2.00') // formatter 调用
    expect(text).toContain('已启用')
    expect(text).toContain('定时备份已启动运行中')
  })

  it('加载失败 → logger.error 兜底，不抛错', async () => {
    mockGetBackupList.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).loading).toBe(false)
  })

  it('loadSchedule 异常 → 静默忽略', async () => {
    mockGet.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).scheduleRunning).toBe(false)
  })

  it('列表项为 null/items 缺失 → ?? [] 兜底', async () => {
    mockGetBackupList.mockResolvedValue({})
    let wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).backups).toEqual([])

    mockGetBackupList.mockResolvedValue(null)
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).backups).toEqual([])
  })
})

describe('创建备份', () => {
  it('openCreateDialog 重置表单并打开对话框', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.createForm.description = 'x'
    vm.openCreateDialog()
    expect(vm.createForm.description).toBe('')
    expect(vm.createForm.include_uploads).toBe(true)
    expect(vm.showCreateDialog).toBe(true)
  })

  it('点击「创建备份」按钮打开对话框（模板）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await findBtn(wrapper, '创建备份').trigger('click')
    expect((wrapper.vm as any).showCreateDialog).toBe(true)
  })

  it('handleCreateBackup 成功：post 载荷（密码为空 → undefined）、emit、刷新列表', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.createForm.description = '日常'
    vm.createForm.password = ''
    await vm.handleCreateBackup()
    expect(mockPost).toHaveBeenCalledWith('/system/backup', {
      description: '日常',
      include_uploads: true,
      password: undefined,
    })
    expect(ElMessage.success).toHaveBeenCalledWith('备份创建成功')
    expect(wrapper.emitted('backup-complete')).toHaveLength(1)
    expect(vm.creating).toBe(false)
    expect(mockGetBackupList).toHaveBeenCalled()
  })

  it('handleCreateBackup 后端失败 → error(res.message)；异常 → error 兜底', async () => {
    mockPost.mockResolvedValue({ success: false, message: '磁盘不足' })
    let wrapper = mountComp()
    await flushPromises()
    await (wrapper.vm as any).handleCreateBackup()
    expect(ElMessage.error).toHaveBeenCalledWith('磁盘不足')

    mockPost.mockResolvedValue({ success: false })
    wrapper = mountComp()
    await flushPromises()
    await (wrapper.vm as any).handleCreateBackup()
    expect(ElMessage.error).toHaveBeenCalledWith('备份创建失败')

    mockPost.mockRejectedValue(new Error('net'))
    wrapper = mountComp()
    await flushPromises()
    await (wrapper.vm as any).handleCreateBackup()
    expect(ElMessage.error).toHaveBeenCalledWith('备份创建失败')
  })

  it('对话框内「创建备份」按钮触发 + 「取消」关闭 + v-model 同步', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.showCreateDialog = true
    await nextTick()
    const dialogs = wrapper.findAllComponents({ name: 'ElDialog' })
    expect(dialogs.length).toBe(3)
    // 取消按钮
    const cancels = wrapper.findAll('el-button-stub').filter((b: any) => b.text().trim() === '取消')
    await cancels[0].trigger('click')
    expect(vm.showCreateDialog).toBe(false)

    // 创建按钮（对话框 footer）
    vm.showCreateDialog = true
    await nextTick()
    const footerBtn = dialogs[0]
      .findAll('el-button-stub')
      .find((b: any) => b.text().trim() === '创建备份')
    await footerBtn.trigger('click')
    await flushPromises()
    expect(mockPost).toHaveBeenCalled()
  })

  it('对话框 v-model：emit update:modelValue 同步（创建/预览/恢复）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const dialogs = wrapper.findAllComponents({ name: 'ElDialog' })
    vm.showCreateDialog = true
    vm.showPreviewDialog = true
    vm.showRestoreDialog = true
    await nextTick()
    // 恢复对话框「取消」内联 setter
    await dialogs[2].findAll('el-button-stub')[0].trigger('click')
    expect(vm.showRestoreDialog).toBe(false)
    vm.showRestoreDialog = true
    await nextTick()
    dialogs[0].vm.$emit('update:modelValue', false)
    dialogs[1].vm.$emit('update:modelValue', false)
    dialogs[2].vm.$emit('update:modelValue', false)
    expect(vm.showCreateDialog).toBe(false)
    expect(vm.showPreviewDialog).toBe(false)
    expect(vm.showRestoreDialog).toBe(false)
  })
})

describe('预览与恢复', () => {
  it('handlePreview 成功：加载清单并打开对话框', async () => {
    mockGet.mockResolvedValue({ filename: 'a.zip', files: [{ name: 'db.sqlite', size: 10, compressed_size: 5 }], meta: { description: 'd', created_at: '2024', contents: ['db'] } })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.handlePreview(rowA)
    expect(mockGet).toHaveBeenCalledWith('/system/backup/preview/backup_a.zip')
    expect(vm.previewData.filename).toBe('a.zip')
    expect(vm.showPreviewDialog).toBe(true)
    expect(vm.previewing).toBeNull()
    expect(wrapper.text()).toContain('db')

    // contents 缺失 → ?? [] 兜底渲染
    mockGet.mockResolvedValue({ files: [], meta: { created_at: '2024' } })
    await vm.handlePreview(rowB)
    expect(vm.previewData.meta.contents).toBeUndefined()
    expect(vm.showPreviewDialog).toBe(true)
  })

  it('handlePreview 异常 → error；预览模板行内按钮点击', async () => {
    mockGet.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.handlePreview(rowB)
    expect(ElMessage.error).toHaveBeenCalledWith('加载备份预览失败')

    mockGet.mockResolvedValue({ files: [], meta: {} })
    await findBtn(wrapper, '预览').trigger('click') // rowA
    await flushPromises()
    expect(mockGet).toHaveBeenCalledWith('/system/backup/preview/backup_a.zip')
  })

  it('handleRestore 设置选中项并打开确认框（模板行按钮）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await findBtn(wrapper, '恢复').trigger('click') // rowA
    expect(vm.selectedBackup).toEqual(rowA)
    expect(vm.showRestoreDialog).toBe(true)
  })

  it('confirmRestore：无选中早退；成功 → emit + 3 秒后刷新页面', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    await vm.confirmRestore() // selectedBackup null → 早退
    expect(mockRestoreBackup).not.toHaveBeenCalled()

    vm.selectedBackup = { ...rowA }
    const reload = vi.fn()
    Object.defineProperty(window, 'location', { value: { reload }, writable: true })
    vi.useFakeTimers()
    await vm.confirmRestore()
    expect(mockRestoreBackup).toHaveBeenCalledWith('backup_a.zip')
    expect(ElMessage.success).toHaveBeenCalledWith('恢复成功，页面将在 3 秒后刷新')
    expect(vm.showRestoreDialog).toBe(false)
    expect(wrapper.emitted('backup-complete')).toHaveLength(1)
    await vi.advanceTimersByTimeAsync(3000)
    expect(reload).toHaveBeenCalled()
    vi.useRealTimers()
  })

  it('confirmRestore：后端失败（含/无 message）/ 异常 → error；按钮点击触发', async () => {
    mockRestoreBackup.mockResolvedValue({ success: false, message: '文件损坏' })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.selectedBackup = { ...rowA }
    await vm.confirmRestore()
    expect(ElMessage.error).toHaveBeenCalledWith('文件损坏')

    mockRestoreBackup.mockResolvedValue({ success: false })
    await vm.confirmRestore()
    expect(ElMessage.error).toHaveBeenCalledWith('恢复失败')

    mockRestoreBackup.mockRejectedValue(new Error('net'))
    await vm.confirmRestore()
    expect(ElMessage.error).toHaveBeenCalledWith('恢复失败')

    mockRestoreBackup.mockResolvedValue({ success: true })
    await findBtn(wrapper, '确认恢复').trigger('click')
    await flushPromises()
    expect(mockRestoreBackup).toHaveBeenCalledWith('backup_a.zip')
    expect(vm.restoring).toBe(false)
  })
})

describe('删除备份', () => {
  it('确认后成功 → 删除+刷新列表（模板行按钮）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await findBtn(wrapper, '删除').trigger('click')
    await flushPromises()
    expect(confirmMock).toHaveBeenCalledWith(
      '确定要删除备份 "backup_a.zip" 吗？',
      '删除确认',
      expect.objectContaining({ type: 'warning' })
    )
    expect(mockDeleteBackup).toHaveBeenCalledWith('backup_a.zip')
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    expect(mockGetBackupList).toHaveBeenCalled()
  })

  it('取消确认 → 静默；后端失败 → error(res.message)', async () => {
    confirmMock.mockRejectedValueOnce(new Error('cancel'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.handleDelete(rowB)
    expect(mockDeleteBackup).not.toHaveBeenCalled()

    mockDeleteBackup.mockResolvedValue({ success: false, message: '文件不存在' })
    await vm.handleDelete(rowB)
    expect(ElMessage.error).toHaveBeenCalledWith('文件不存在')

    mockDeleteBackup.mockResolvedValue({ success: false })
    await vm.handleDelete(rowB)
    expect(ElMessage.error).toHaveBeenCalledWith('删除失败')

    mockDeleteBackup.mockResolvedValue({ success: true })
    await vm.handleDelete(rowB)
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
  })
})

describe('定时备份配置', () => {
  it('saveSchedule 成功：保存并重载配置；开关 change 事件触发', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.scheduleConfig.enabled = true
    vm.scheduleConfig.interval_hours = 24
    vm.scheduleConfig.keep_count = 7
    vm.scheduleConfig.time_of_day = '02:00'
    await vm.saveSchedule()
    expect(mockPut).toHaveBeenCalledWith('/system/backup/schedule', {
      enabled: true,
      interval_hours: 24,
      keep_count: 7,
      time_of_day: '02:00',
    })
    expect(ElMessage.success).toHaveBeenCalledWith('定时备份配置已保存')
    expect(mockGet).toHaveBeenCalledWith('/system/backup/schedule')

    // 模板：开关 change → saveSchedule
    const base = mockPut.mock.calls.length
    const switches = wrapper.findAllComponents({ name: 'ElSwitch' })
    switches[0].vm.$emit('change')
    await flushPromises()
    expect(mockPut.mock.calls.length).toBe(base + 1)
  })

  it('saveSchedule 异常 → error；保存配置按钮点击触发', async () => {
    mockPut.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.scheduleConfig.enabled = true
    await vm.saveSchedule()
    expect(ElMessage.error).toHaveBeenCalledWith('保存定时备份配置失败')

    mockPut.mockResolvedValue({})
    await findBtn(wrapper, '保存配置').trigger('click')
    await flushPromises()
    expect(mockPut).toHaveBeenCalled()
    expect(vm.savingSchedule).toBe(false)
  })

  it('表单控件 v-model：间隔/保留份数/每日时间/复选框/开关/输入框', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const byName = (n: string) => wrapper.findAllComponents({ name: n })
    byName('ElSelect')[0].vm.$emit('update:modelValue', 12)
    expect(vm.scheduleConfig.interval_hours).toBe(12)
    byName('ElInputNumber')[0].vm.$emit('update:modelValue', 3)
    expect(vm.scheduleConfig.keep_count).toBe(3)
    byName('ElTimeSelect')[0].vm.$emit('update:modelValue', '05:00')
    expect(vm.scheduleConfig.time_of_day).toBe('05:00')
    const checkboxes = wrapper.findAllComponents({ name: 'ElCheckbox' })
    checkboxes[0].vm.$emit('update:modelValue', false)
    expect(vm.createForm.include_uploads).toBe(false)
    checkboxes[1].vm.$emit('update:modelValue', false)
    expect(vm.createForm.include_config).toBe(false)
    // el-switch 模板按钮点击 → update:modelValue + change
    const switches = wrapper.findAllComponents({ name: 'ElSwitch' })
    await switches[0].trigger('click')
    expect(vm.scheduleConfig.enabled).toBe(true)
    await flushPromises()
    // 创建对话框输入框 v-model
    const inputs = wrapper.findAllComponents({ name: 'ElInput' })
    inputs[0].vm.$emit('update:modelValue', '描述X')
    inputs[1].vm.$emit('update:modelValue', 'pwdX')
    expect(vm.createForm.description).toBe('描述X')
    expect(vm.createForm.password).toBe('pwdX')
  })

  it('刷新按钮触发 loadBackups（模板）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const base = mockGetBackupList.mock.calls.length
    await findBtn(wrapper, '刷新').trigger('click')
    await flushPromises()
    expect(mockGetBackupList.mock.calls.length).toBe(base + 1)
  })
})
