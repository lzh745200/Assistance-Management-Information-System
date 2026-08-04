/**
 * views/system/AuditManagement.vue 覆盖率攻坚
 * 覆盖：统计/日志/登录/告警加载、tab 懒加载、筛选、告警处理、工具函数
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import { nextTick } from 'vue'

enableAutoUnmount(afterEach)

const { ElMessage, ElMessageBox, auditApi } = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  ElMessageBox: { confirm: vi.fn(), alert: vi.fn(), prompt: vi.fn() },
  auditApi: {
    getStats: vi.fn(),
    getLogs: vi.fn(),
    getLoginAttempts: vi.fn(),
    getSecurityEvents: vi.fn(),
    resolveSecurityEvent: vi.fn(),
  },
}))

vi.mock('@/api/audit', () => ({
  auditApi,
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox,
  ElNotification: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
}))

import AuditManagement from '@/views/system/AuditManagement.vue'

const statsData = {
  today_operations: 10,
  active_users: 3,
  failed_operations: 2,
  warnings: 1,
}

const logsData = {
  items: [
    { id: 1, created_at: '2024-01-01T10:00:00Z', username: 'admin', user_id: 1, action: 'login', resource_type: '系统', resource_id: '1', detail: '登录成功', status: 'success', ip_address: '10.0.0.1' },
    { id: 2, created_at: '2024-01-02T10:00:00Z', user_id: 2, action: 'delete_project', detail: '删除', status: 'failed', ip_address: '10.0.0.2' },
    { id: 3, created_at: '2024-01-03T10:00:00Z', username: 'op', action: 'unknown_action', status: 'success' },
    { id: 4 },
    { id: 5, resource_type: '项目' },
  ],
}

const loginData = {
  items: [
    { id: 1, attempt_time: '2024-01-01T10:00:00Z', username: 'admin', success: true, ip_address: '10.0.0.1', user_agent: 'Chrome' },
    { id: 2, attempt_time: '2024-01-02T10:00:00Z', username: 'op', success: false, ip_address: '10.0.0.2', user_agent: 'Firefox' },
    { id: 3 },
  ],
}

const alertsData = {
  items: [
    { id: 1, created_at: '2024-01-01T10:00:00Z', severity: 'high', event_type: 'abnormal_login', description: '异地登录', resolved: false },
    { id: 2, created_at: '2024-01-02T10:00:00Z', severity: 'medium', event_type: 'config_change', description: '配置变更', resolved: true },
    { id: 3, created_at: '2024-01-03T10:00:00Z', severity: 'low', event_type: 'x', description: '低危', resolved: false },
    { id: 4 },
  ],
}

async function mountComp() {
  const w = mount(AuditManagement, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-tabs': {
          name: 'ElTabs',
          props: ['modelValue'],
          emits: ['update:modelValue', 'tab-change'],
          template:
            '<div class="el-tabs-stub"><slot /></div>',
        },
        'el-tab-pane': { name: 'ElTabPane', template: '<div class="el-tab-pane-stub"><slot /></div>' },
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot /><slot name="header" /></div>',
        },
        'el-select': {
          name: 'ElSelect',
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template:
            '<select class="el-select-stub" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
        },
        'el-option': { name: 'ElOption', props: ['value'], template: '<option :value="value"><slot /></option>' },
        'el-input': {
          name: 'ElInput',
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template:
            '<input class="el-input-stub" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        'el-date-picker': {
          name: 'ElDatePicker',
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template:
            '<div class="el-date-stub" @click="$emit(\'update:modelValue\', [\'2024-01-01\', \'2024-01-31\'])"><slot /></div>',
        },
        'el-button': {
          name: 'ElButton',
          template: '<button class="el-button-stub"><slot /></button>',
        },
        'el-table': { name: 'ElTable', template: '<table class="el-table-stub"><slot /></table>' },
        'el-table-column': {
          name: 'ElTableColumn',
          template: '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /></div>',
          data() {
            return {
              rowA: { action: 'login', type: 'login', level: 'high', success: true, handled: false },
              rowB: { action: 'delete_project', type: 'logout', level: 'medium', success: false, handled: true },
            }
          },
        },
        'el-tag': { name: 'ElTag', template: '<span class="el-tag-stub"><slot /></span>' },
      },
    },
  })
  await flushPromises()
  await nextTick()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  auditApi.getStats.mockResolvedValue(statsData)
  auditApi.getLogs.mockResolvedValue(logsData)
  auditApi.getLoginAttempts.mockResolvedValue(loginData)
  auditApi.getSecurityEvents.mockResolvedValue(alertsData)
  auditApi.resolveSecurityEvent.mockResolvedValue({})
  ElMessageBox.prompt.mockResolvedValue({ value: '已处理' })
})

describe('AuditManagement.vue', () => {
  it('渲染并加载统计/审计日志', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    expect(auditApi.getStats).toHaveBeenCalled()
    expect(auditApi.getLogs).toHaveBeenCalledWith(expect.objectContaining({ page: 1, page_size: 50 }))
    expect(vm.stats.todayOps).toBe(10)
    expect(vm.stats.activeUsers).toBe(3)
    expect(vm.stats.failures).toBe(2)
    expect(vm.stats.warnings).toBe(1)
    expect(vm.auditLogs.length).toBe(5)
    expect(vm.auditLogs[0].user).toBe('admin')
    expect(vm.auditLogs[1].user).toBe('用户2')
    expect(vm.auditLogs[2].action).toBe('unknown_action')
  })

  it('统计字段缺失 → 0 兜底', async () => {
    auditApi.getStats.mockResolvedValue({ total_operations: 5 })
    const w = await mountComp()
    const vm = w.vm as any
    expect(vm.stats.todayOps).toBe(5)
    expect(vm.stats.activeUsers).toBe(0)
    expect(vm.stats.failures).toBe(0)
    expect(vm.stats.warnings).toBe(0)
  })

  it('统计全部缺失 → 全 0', async () => {
    auditApi.getStats.mockResolvedValue({})
    const w = await mountComp()
    const vm = w.vm as any
    expect(vm.stats.todayOps).toBe(0)
    expect(vm.stats.activeUsers).toBe(0)
  })

  it('带用户筛选加载日志', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.filters.user = 'admin'
    await vm.loadAuditLogs()
    expect(auditApi.getLogs).toHaveBeenLastCalledWith(
      expect.objectContaining({ user_id: undefined })
    )
  })

  it('加载统计失败 → 静默', async () => {
    auditApi.getStats.mockRejectedValue(new Error('boom'))
    const w = await mountComp()
    expect((w.vm as any).stats.todayOps).toBe(0)
  })

  it('加载日志失败 → 空列表', async () => {
    auditApi.getLogs.mockRejectedValue(new Error('boom'))
    const w = await mountComp()
    expect((w.vm as any).auditLogs).toEqual([])
    expect((w.vm as any).loading).toBe(false)
  })

  it('带筛选加载日志（action/日期）', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.filters.action = 'login'
    vm.filters.dateRange = ['2024-01-01', '2024-01-31']
    await vm.handleSearch()
    expect(auditApi.getLogs).toHaveBeenLastCalledWith(
      expect.objectContaining({ action: 'login', start_date: '2024-01-01', end_date: '2024-01-31' })
    )
  })

  it('handleReset 重置筛选并重新加载', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.filters.action = 'login'
    vm.filters.user = 'admin'
    vm.filters.dateRange = ['2024-01-01', '2024-01-31']
    await vm.handleReset()
    expect(vm.filters.action).toBe('')
    expect(vm.filters.user).toBe('')
    expect(vm.filters.dateRange).toBeNull()
    expect(auditApi.getLogs).toHaveBeenCalled()
  })

  it('筛选输入：action select / user input / 日期选择', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    const select = w.find('.el-select-stub')
    await select.setValue('data_modify')
    expect(vm.filters.action).toBe('data_modify')
    const input = w.find('.el-input-stub')
    await input.setValue('admin')
    expect(vm.filters.user).toBe('admin')
    await w.find('.el-date-stub').trigger('click')
    expect(vm.filters.dateRange).toEqual(['2024-01-01', '2024-01-31'])
  })

  it('查询/重置按钮点击', async () => {
    const w = await mountComp()
    const searchBtn = w
      .findAll('button')
      .find((b) => b.text().includes('查询'))
    await searchBtn!.trigger('click')
    expect(auditApi.getLogs).toHaveBeenCalled()
    const resetBtn = w
      .findAll('button')
      .find((b) => b.text().includes('重置'))
    await resetBtn!.trigger('click')
    expect(auditApi.getLogs).toHaveBeenCalled()
  })

  it('tab 切换：登录日志懒加载', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    const tabs = w.findComponent({ name: 'ElTabs' })
    tabs.vm.$emit('update:modelValue', 'login')
    await nextTick()
    tabs.vm.$emit('tab-change', 'login')
    await nextTick()
    await flushPromises()
    expect(auditApi.getLoginAttempts).toHaveBeenCalled()
    expect(vm.loginLogs.length).toBe(3)
    expect(vm.loginLogs[0].type).toBe('login')
  })

  it('tab 切换：告警懒加载', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    const tabs = w.findComponent({ name: 'ElTabs' })
    tabs.vm.$emit('update:modelValue', 'alerts')
    await nextTick()
    tabs.vm.$emit('tab-change', 'alerts')
    await nextTick()
    await flushPromises()
    expect(auditApi.getSecurityEvents).toHaveBeenCalled()
    expect(vm.alerts.length).toBe(4)
    expect(vm.alerts[0].level).toBe('high')
    expect(vm.alerts[2].level).toBe('low')
  })

  it('登录日志加载失败 → 空列表', async () => {
    auditApi.getLoginAttempts.mockRejectedValue(new Error('boom'))
    const w = await mountComp()
    const vm = w.vm as any
    vm.loginLogs = []
    await vm.loadLoginLogs()
    expect(vm.loginLogs).toEqual([])
  })

  it('告警加载失败 → 空列表', async () => {
    auditApi.getSecurityEvents.mockRejectedValue(new Error('boom'))
    const w = await mountComp()
    const vm = w.vm as any
    vm.alerts = []
    await vm.loadAlerts()
    expect(vm.alerts).toEqual([])
  })

  it('handleAlert：确认 → 处理成功', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    const row = { id: 1, handled: false }
    await vm.handleAlert(row)
    expect(ElMessageBox.prompt).toHaveBeenCalled()
    expect(auditApi.resolveSecurityEvent).toHaveBeenCalledWith(1, '已处理')
    expect(row.handled).toBe(true)
    expect(ElMessage.success).toHaveBeenCalledWith('告警已标记为已处理')
  })

  it('handleAlert：空备注 → 默认"已处理"', async () => {
    ElMessageBox.prompt.mockResolvedValue({ value: '' })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleAlert({ id: 2, handled: false })
    expect(auditApi.resolveSecurityEvent).toHaveBeenCalledWith(2, '已处理')
  })

  it('handleAlert：用户取消 → 无操作', async () => {
    ElMessageBox.prompt.mockRejectedValue('cancel')
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleAlert({ id: 1, handled: false })
    expect(auditApi.resolveSecurityEvent).not.toHaveBeenCalled()
  })

  it('日志响应缺失 items → || [] 兜底为空列表', async () => {
    auditApi.getLogs.mockResolvedValue({})
    const w = await mountComp()
    expect((w.vm as any).auditLogs).toEqual([])
  })

  it('登录日志响应缺失 items → || [] 兜底为空列表', async () => {
    auditApi.getLoginAttempts.mockResolvedValue({})
    const w = await mountComp()
    const vm = w.vm as any
    await vm.loadLoginLogs()
    expect(vm.loginLogs).toEqual([])
  })

  it('告警响应缺失 items → || [] 兜底为空列表', async () => {
    auditApi.getSecurityEvents.mockResolvedValue({})
    const w = await mountComp()
    const vm = w.vm as any
    await vm.loadAlerts()
    expect(vm.alerts).toEqual([])
  })

  it('工具函数：actionTagType / actionName / getLevelText', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    expect(vm.actionTagType('login')).toBe('success')
    expect(vm.actionTagType('data_modify')).toBe('primary')
    expect(vm.actionTagType('data_import')).toBe('info')
    expect(vm.actionTagType('data_export')).toBe('success')
    expect(vm.actionTagType('backup')).toBe('warning')
    expect(vm.actionTagType('permission')).toBe('danger')
    expect(vm.actionTagType('create_project')).toBe('primary')
    expect(vm.actionTagType('update_project')).toBe('primary')
    expect(vm.actionTagType('delete_project')).toBe('danger')
    expect(vm.actionTagType('create_organization')).toBe('primary')
    expect(vm.actionTagType('update_organization')).toBe('primary')
    expect(vm.actionTagType('delete_organization')).toBe('danger')
    expect(vm.actionTagType('create_user')).toBe('primary')
    expect(vm.actionTagType('update_user')).toBe('primary')
    expect(vm.actionTagType('delete_user')).toBe('danger')
    expect(vm.actionTagType('system_config')).toBe('warning')
    expect(vm.actionTagType('file_upload')).toBe('info')
    expect(vm.actionTagType('file_download')).toBe('info')
    expect(vm.actionTagType('unknown')).toBe('info')
    expect(vm.actionName('login')).toBe('登录')
    expect(vm.actionName('data_modify')).toBe('数据修改')
    expect(vm.actionName('xyz')).toBe('xyz')
    expect(vm.getLevelText('high')).toBe('高')
    expect(vm.getLevelText('medium')).toBe('中')
    expect(vm.getLevelText('low')).toBe('低')
    expect(vm.getLevelText('other')).toBe('other')
  })

  it('告警行按钮（处理）点击 → 处理流程', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.alerts = [{ id: 1, handled: false }, { id: 2, handled: true }]
    await nextTick()
    const handleBtns = w.findAll('button').filter((b) => b.text().includes('处理'))
    expect(handleBtns.length).toBeGreaterThan(0)
    await handleBtns[0].trigger('click')
    expect(ElMessageBox.prompt).toHaveBeenCalled()
    expect(auditApi.resolveSecurityEvent).toHaveBeenCalled()
  })
})
