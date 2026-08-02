/**
 * views/system/SecretsManagement.vue 覆盖率攻坚
 * 覆盖：状态/版本加载、轮换、创建、撤销、清理、工具函数
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import { nextTick } from 'vue'

enableAutoUnmount(afterEach)

const { ElMessage, ElMessageBox, secretsApi } = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  ElMessageBox: { confirm: vi.fn(), alert: vi.fn() },
  secretsApi: {
    getStatus: vi.fn(),
    getVersions: vi.fn(),
    rotateSecrets: vi.fn(),
    createSecret: vi.fn(),
    revokeSecret: vi.fn(),
    cleanup: vi.fn(),
  },
}))

vi.mock('@/api/secrets', () => ({
  secretsApi,
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox,
  ElNotification: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
}))

import SecretsManagement from '@/views/system/SecretsManagement.vue'

const statusData = {
  total_versions: 5,
  active_versions: 2,
  latest_version: { version_id: 'v5' },
  requires_rotation: true,
}

const versionsData = {
  versions: [
    { version_id: 'v1', created_at: 1700000000, is_active: true, key_type: 'fernet' },
    { version_id: 'v2', created_at: 1600000000, is_active: false, revoked_at: 1650000000, key_type: 'aes' },
    { version_id: 'v3', created_at: 1500000000, is_active: false, key_type: 'chacha20' },
    { version_id: 'v4', key_type: 'fernet' },
  ],
  count: 4,
}

async function mountComp() {
  const w = mount(SecretsManagement, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-row': { name: 'ElRow', template: '<div class="el-row-stub"><slot /></div>' },
        'el-col': { name: 'ElCol', template: '<div class="el-col-stub"><slot /></div>' },
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot /><slot name="header" /></div>',
        },
        'el-statistic': {
          name: 'ElStatistic',
          template: '<div class="el-statistic-stub"><slot /></div>',
          props: ['title', 'value'],
        },
        'el-tag': { name: 'ElTag', template: '<span class="el-tag-stub"><slot /></span>' },
        'el-button': {
          name: 'ElButton',
          template: '<button class="el-button-stub"><slot /></button>',
        },
        'el-table': { name: 'ElTable', template: '<table class="el-table-stub"><slot /></table>' },
        'el-table-column': {
          name: 'ElTableColumn',
          template: '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /><slot :row="rowC" /><slot :row="rowD" /></div>',
          data() {
            return {
              rowA: { version_id: 'v1', created_at: 1700000000, is_active: true, key_type: 'fernet' },
              rowB: { version_id: 'v2', created_at: 1600000000, is_active: false, revoked_at: 1650000000, key_type: 'aes' },
              rowC: { version_id: 'v3', created_at: 1500000000, is_active: false, key_type: 'chacha20' },
              rowD: { version_id: 'v4', key_type: 'fernet' },
            }
          },
        },
        'el-dialog': {
          name: 'ElDialog',
          template: '<div class="el-dialog-stub"><slot /><slot name="footer" /></div>',
          emits: ['update:modelValue'],
        },
        'el-form': { name: 'ElForm', template: '<form><slot /></form>' },
        'el-form-item': { name: 'ElFormItem', template: '<div><slot /></div>' },
        'el-select': {
          name: 'ElSelect',
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template:
            '<select class="el-select-stub" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
        },
        'el-option': { name: 'ElOption', template: '<option :value="value"><slot /></option>' },
        'el-input-number': {
          name: 'ElInputNumber',
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template:
            '<input class="el-input-number-stub" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
      },
    },
  })
  await flushPromises()
  await nextTick()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  secretsApi.getStatus.mockResolvedValue(statusData)
  secretsApi.getVersions.mockResolvedValue(versionsData)
  secretsApi.rotateSecrets.mockResolvedValue({ message: '轮换完成', new_version: 'v6' })
  secretsApi.createSecret.mockResolvedValue({ message: '创建成功' })
  secretsApi.revokeSecret.mockResolvedValue({ message: '已撤销' })
  secretsApi.cleanup.mockResolvedValue({ message: '清理完成', deleted_count: 2 })
  ElMessageBox.confirm.mockResolvedValue('confirm')
})

describe('SecretsManagement.vue', () => {
  it('渲染并加载状态/版本', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    expect(secretsApi.getStatus).toHaveBeenCalled()
    expect(secretsApi.getVersions).toHaveBeenCalled()
    expect(vm.status.total_versions).toBe(5)
    expect(vm.versions.length).toBe(4)
    expect(vm.status.requires_rotation).toBe(true)
  })

  it('加载状态失败 → 错误提示', async () => {
    secretsApi.getStatus.mockRejectedValue(new Error('status failed'))
    const w = await mountComp()
    expect(ElMessage.error).toHaveBeenCalledWith('status failed')
    expect((w.vm as any).loadingStatus).toBe(false)
  })

  it('加载状态失败（非 Error）→ 默认文案', async () => {
    secretsApi.getStatus.mockRejectedValue('oops')
    const w = await mountComp()
    expect(ElMessage.error).toHaveBeenCalledWith('获取密钥状态失败')
  })

  it('加载版本失败 → 错误提示', async () => {
    secretsApi.getVersions.mockRejectedValue(new Error('versions failed'))
    const w = await mountComp()
    expect(ElMessage.error).toHaveBeenCalledWith('versions failed')
    expect((w.vm as any).loadingVersions).toBe(false)
  })

  it('加载版本失败（非 Error）→ 默认文案', async () => {
    secretsApi.getVersions.mockRejectedValue('oops')
    const w = await mountComp()
    expect(ElMessage.error).toHaveBeenCalledWith('获取密钥版本失败')
  })

  it('refreshAll 并行刷新', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vi.clearAllMocks()
    secretsApi.getStatus.mockResolvedValue(statusData)
    secretsApi.getVersions.mockResolvedValue(versionsData)
    await vm.refreshAll()
    expect(secretsApi.getStatus).toHaveBeenCalled()
    expect(secretsApi.getVersions).toHaveBeenCalled()
  })

  it('handleRotate：确认 → 轮换成功并刷新', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleRotate()
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(secretsApi.rotateSecrets).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('轮换完成')
    expect(vm.loadingRotate).toBe(false)
  })

  it('handleRotate：无 message → 默认文案', async () => {
    secretsApi.rotateSecrets.mockResolvedValue({})
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleRotate()
    expect(ElMessage.success).toHaveBeenCalledWith('密钥轮换成功')
  })

  it('handleRotate：用户取消 → 返回', async () => {
    ElMessageBox.confirm.mockRejectedValue('cancel')
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleRotate()
    expect(secretsApi.rotateSecrets).not.toHaveBeenCalled()
  })

  it('handleRotate：失败 → 错误提示', async () => {
    secretsApi.rotateSecrets.mockRejectedValue(new Error('rotate failed'))
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleRotate()
    expect(ElMessage.error).toHaveBeenCalledWith('rotate failed')
  })

  it('handleRotate：失败非 Error → 默认文案', async () => {
    secretsApi.rotateSecrets.mockRejectedValue('oops')
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleRotate()
    expect(ElMessage.error).toHaveBeenCalledWith('密钥轮换失败')
  })

  it('handleCreate：创建成功（无过期天数）', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleCreate()
    expect(secretsApi.createSecret).toHaveBeenCalledWith({ key_type: 'fernet' })
    expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
    expect(vm.createDialogVisible).toBe(false)
    expect(vm.createForm.key_type).toBe('fernet')
  })

  it('handleCreate：带过期天数', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.createForm.expires_days = 90
    await vm.handleCreate()
    expect(secretsApi.createSecret).toHaveBeenCalledWith({ key_type: 'fernet', expires_days: 90 })
  })

  it('handleCreate：失败 → 错误提示', async () => {
    secretsApi.createSecret.mockRejectedValue(new Error('create failed'))
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleCreate()
    expect(ElMessage.error).toHaveBeenCalledWith('create failed')
    expect(vm.loadingCreate).toBe(false)
  })

  it('handleCreate：无 message → 默认成功文案', async () => {
    secretsApi.createSecret.mockResolvedValue({})
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleCreate()
    expect(ElMessage.success).toHaveBeenCalledWith('密钥创建成功')
  })

  it('handleCreate：失败非 Error → 默认文案', async () => {
    secretsApi.createSecret.mockRejectedValue('oops')
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleCreate()
    expect(ElMessage.error).toHaveBeenCalledWith('创建密钥失败')
  })

  it('openCreateDialog 打开对话框', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.createForm.key_type = 'aes'
    vm.openCreateDialog()
    expect(vm.createForm.key_type).toBe('fernet')
    expect(vm.createDialogVisible).toBe(true)
  })

  it('handleRevoke：确认 → 撤销成功', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleRevoke({ version_id: 'v1', is_active: true })
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(secretsApi.revokeSecret).toHaveBeenCalledWith('v1')
    expect(ElMessage.success).toHaveBeenCalledWith('已撤销')
    expect(vm.revokingId).toBeNull()
  })

  it('handleRevoke：无 message → 默认文案', async () => {
    secretsApi.revokeSecret.mockResolvedValue({})
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleRevoke({ version_id: 'v1' })
    expect(ElMessage.success).toHaveBeenCalledWith('密钥已撤销')
  })

  it('handleRevoke：用户取消 → 返回', async () => {
    ElMessageBox.confirm.mockRejectedValue('cancel')
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleRevoke({ version_id: 'v1' })
    expect(secretsApi.revokeSecret).not.toHaveBeenCalled()
  })

  it('handleRevoke：失败 → 错误提示', async () => {
    secretsApi.revokeSecret.mockRejectedValue(new Error('revoke failed'))
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleRevoke({ version_id: 'v1' })
    expect(ElMessage.error).toHaveBeenCalledWith('revoke failed')
  })

  it('handleRevoke：失败非 Error → 默认文案', async () => {
    secretsApi.revokeSecret.mockRejectedValue('oops')
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleRevoke({ version_id: 'v1' })
    expect(ElMessage.error).toHaveBeenCalledWith('撤销密钥失败')
  })

  it('handleCleanup：确认 → 清理成功', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleCleanup()
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(secretsApi.cleanup).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('清理完成')
    expect(vm.loadingCleanup).toBe(false)
  })

  it('handleCleanup：无 message → 默认文案', async () => {
    secretsApi.cleanup.mockResolvedValue({ deleted_count: 3 })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleCleanup()
    expect(ElMessage.success).toHaveBeenCalledWith('清理了 3 个过期密钥')
  })

  it('handleCleanup：用户取消 → 返回', async () => {
    ElMessageBox.confirm.mockRejectedValue('cancel')
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleCleanup()
    expect(secretsApi.cleanup).not.toHaveBeenCalled()
  })

  it('handleCleanup：失败 → 错误提示', async () => {
    secretsApi.cleanup.mockRejectedValue(new Error('cleanup failed'))
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleCleanup()
    expect(ElMessage.error).toHaveBeenCalledWith('cleanup failed')
  })

  it('handleCleanup：失败非 Error → 默认文案', async () => {
    secretsApi.cleanup.mockRejectedValue('oops')
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleCleanup()
    expect(ElMessage.error).toHaveBeenCalledWith('清理失败')
  })

  it('工具函数：formatTime / getStatusType / getStatusText', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    expect(vm.formatTime(undefined)).toBe('-')
    expect(vm.formatTime(1700000000)).toContain('2023')
    expect(vm.getStatusType({ is_active: true })).toBe('success')
    expect(vm.getStatusType({ is_active: false, revoked_at: 1 })).toBe('danger')
    expect(vm.getStatusType({ is_active: false, revoked_at: undefined })).toBe('warning')
    expect(vm.getStatusText({ is_active: true })).toBe('活跃')
    expect(vm.getStatusText({ is_active: false, revoked_at: 1 })).toBe('已撤销')
    expect(vm.getStatusText({ is_active: false, revoked_at: undefined })).toBe('已过期')
  })

  it('创建对话框：密钥类型 select + 过期天数输入 + 取消按钮', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.openCreateDialog()
    await nextTick()
    const select = w.find('.el-select-stub')
    await select.setValue('aes')
    expect(vm.createForm.key_type).toBe('aes')
    const num = w.find('.el-input-number-stub')
    await num.setValue('30')
    expect(vm.createForm.expires_days).toBe('30')
    const cancelBtn = w
      .findAll('button')
      .find((b) => b.text().includes('取消'))
    await cancelBtn!.trigger('click')
    await nextTick()
    expect(vm.createDialogVisible).toBe(false)
    // 对话框 update:modelValue 关闭
    vm.openCreateDialog()
    await nextTick()
    const dialog = w.findComponent({ name: 'ElDialog' })
    dialog.vm.$emit('update:modelValue', false)
    await nextTick()
    expect(vm.createDialogVisible).toBe(false)
  })

  it('撤销按钮（表格行）点击 → 撤销接口', async () => {
    const w = await mountComp()
    await nextTick()
    const revokeBtns = w.findAll('button').filter((b) => b.text().includes('撤销'))
    expect(revokeBtns.length).toBeGreaterThan(0)
    await revokeBtns[0].trigger('click')
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(secretsApi.revokeSecret).toHaveBeenCalledWith('v1')
  })
})
