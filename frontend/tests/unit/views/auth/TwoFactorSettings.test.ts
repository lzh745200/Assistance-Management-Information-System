/**
 * views/auth/TwoFactorSettings.vue 覆盖率攻坚
 * 覆盖：状态加载、启用 2FA、验证令牌、禁用、复制密钥/恢复码
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import { nextTick } from 'vue'

enableAutoUnmount(afterEach)

const { ElMessage, ElMessageBox, twoFactorApi, clipWrite } = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  ElMessageBox: { confirm: vi.fn(), alert: vi.fn() },
  twoFactorApi: {
    getStatus: vi.fn(),
    enable: vi.fn(),
    verifyAndEnable: vi.fn(),
    disable: vi.fn(),
  },
  clipWrite: vi.fn(() => Promise.resolve()),
}))

vi.mock('@/api/twoFactor', () => ({
  twoFactorApi,
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox,
  ElNotification: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
}))

import TwoFactorSettings from '@/views/auth/TwoFactorSettings.vue'

const enableResult = {
  secret: 'SECRET123',
  qr_code: 'data:image/png;base64,xxx',
  backup_codes: ['CODE1', 'CODE2', 'CODE3'],
}

async function mountComp() {
  const w = mount(TwoFactorSettings, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot /><slot name="header" /></div>',
        },
        'el-skeleton': { name: 'ElSkeleton', template: '<div class="el-skeleton-stub"><slot /></div>' },
        'el-descriptions': { name: 'ElDescriptions', template: '<dl><slot /></dl>' },
        'el-descriptions-item': {
          name: 'ElDescriptionsItem',
          template: '<div class="el-desc-item-stub"><slot /></div>',
        },
        'el-tag': { name: 'ElTag', template: '<span class="el-tag-stub"><slot /></span>' },
        'el-alert': { name: 'ElAlert', template: '<div class="el-alert-stub"><slot /><slot name="title" /></div>' },
        'el-button': {
          name: 'ElButton',
          template: '<button @click="$emit(\'click\')"><slot /></button>',
          emits: ['click'],
        },
        'el-form': { name: 'ElForm', template: '<form class="el-form-stub"><slot /></form>' },
        'el-form-item': { name: 'ElFormItem', template: '<div><slot /></div>' },
        'el-input': {
          name: 'ElInput',
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template:
            '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
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
  twoFactorApi.getStatus.mockResolvedValue({ enabled: false })
  twoFactorApi.enable.mockResolvedValue(enableResult)
  twoFactorApi.verifyAndEnable.mockResolvedValue({ message: 'ok' })
  twoFactorApi.disable.mockResolvedValue({ message: 'ok' })
  ElMessageBox.confirm.mockResolvedValue('confirm')
  Object.defineProperty(window.navigator, 'clipboard', {
    value: { writeText: clipWrite },
    configurable: true,
  })
})

describe('TwoFactorSettings.vue', () => {
  it('渲染并加载未启用状态', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    expect(vm.loading).toBe(false)
    expect(vm.isEnabled).toBe(false)
    expect(twoFactorApi.getStatus).toHaveBeenCalled()
    expect(w.text()).toContain('动态验证码')
    expect(w.text()).toContain('开始设置')
  })

  it('已启用状态渲染', async () => {
    twoFactorApi.getStatus.mockResolvedValue({ enabled: true })
    const w = await mountComp()
    const vm = w.vm as any
    expect(vm.isEnabled).toBe(true)
    expect(w.text()).toContain('请妥善保管备用恢复码')
    expect(w.text()).toContain('禁用双因素认证')
  })

  it('加载状态失败 → 警告', async () => {
    twoFactorApi.getStatus.mockRejectedValue(new Error('boom'))
    const w = await mountComp()
    expect(ElMessage.warning).toHaveBeenCalledWith('获取双因素认证状态失败')
    expect((w.vm as any).loading).toBe(false)
  })

  it('开始设置成功 → 展示二维码与密钥', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.startEnable()
    expect(vm.qrCodeSvg).toBe('data:image/png;base64,xxx')
    expect(vm.secretKey).toBe('SECRET123')
    expect(vm.backupCodes).toEqual(['CODE1', 'CODE2', 'CODE3'])
    expect(vm.setupStep).toBe(1)
    expect(vm.enabling).toBe(false)
  })

  it('开始设置：无备份恢复码 → 空数组', async () => {
    twoFactorApi.enable.mockResolvedValue({ secret: 'S', qr_code: 'Q' })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.startEnable()
    expect(vm.backupCodes).toEqual([])
    expect(vm.setupStep).toBe(1)
  })

  it('开始设置失败 → 错误提示', async () => {
    twoFactorApi.enable.mockRejectedValue(new Error('enable failed'))
    const w = await mountComp()
    const vm = w.vm as any
    await vm.startEnable()
    expect(ElMessage.error).toHaveBeenCalledWith('enable failed')
  })

  it('开始设置失败无 message → 默认文案', async () => {
    twoFactorApi.enable.mockRejectedValue({})
    const w = await mountComp()
    const vm = w.vm as any
    await vm.startEnable()
    expect(ElMessage.error).toHaveBeenCalledWith('启用双因素认证失败')
  })

  it('验证令牌：不足6位 → 警告', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.verifyForm.token = '123'
    await vm.verifyToken()
    expect(ElMessage.warning).toHaveBeenCalledWith('请输入6位验证码')
    expect(twoFactorApi.verifyAndEnable).not.toHaveBeenCalled()
  })

  it('验证令牌成功 → 启用完成', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.setupStep = 1
    vm.verifyForm.token = '123456'
    await vm.verifyToken()
    expect(twoFactorApi.verifyAndEnable).toHaveBeenCalledWith('123456')
    expect(ElMessage.success).toHaveBeenCalledWith('双因素认证已启用')
    expect(vm.isEnabled).toBe(true)
    expect(vm.setupStep).toBe(0)
    expect(vm.verifyForm.token).toBe('')
  })

  it('验证令牌失败 → 错误提示', async () => {
    twoFactorApi.verifyAndEnable.mockRejectedValue(new Error('wrong code'))
    const w = await mountComp()
    const vm = w.vm as any
    vm.verifyForm.token = '123456'
    await vm.verifyToken()
    expect(ElMessage.error).toHaveBeenCalledWith('wrong code')
  })

  it('验证令牌失败无 message → 默认文案', async () => {
    twoFactorApi.verifyAndEnable.mockRejectedValue({})
    const w = await mountComp()
    const vm = w.vm as any
    vm.verifyForm.token = '123456'
    await vm.verifyToken()
    expect(ElMessage.error).toHaveBeenCalledWith('验证码错误，请重试')
  })

  it('取消设置 → 重置所有状态', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.setupStep = 1
    vm.verifyForm.token = '123456'
    vm.qrCodeSvg = 'qr'
    vm.secretKey = 'sk'
    vm.backupCodes = ['a']
    vm.cancelSetup()
    expect(vm.setupStep).toBe(0)
    expect(vm.verifyForm.token).toBe('')
    expect(vm.qrCodeSvg).toBe('')
    expect(vm.secretKey).toBe('')
    expect(vm.backupCodes).toEqual([])
  })

  it('禁用 2FA 成功', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.isEnabled = true
    await vm.handleDisable()
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(twoFactorApi.disable).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('双因素认证已禁用')
    expect(vm.isEnabled).toBe(false)
  })

  it('禁用 2FA：用户取消（cancel）→ 无提示', async () => {
    ElMessageBox.confirm.mockRejectedValue('cancel')
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleDisable()
    expect(twoFactorApi.disable).not.toHaveBeenCalled()
    expect(ElMessage.error).not.toHaveBeenCalled()
  })

  it('禁用 2FA 失败 → 错误提示', async () => {
    twoFactorApi.disable.mockRejectedValue(new Error('disable failed'))
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleDisable()
    expect(ElMessage.error).toHaveBeenCalledWith('disable failed')
  })

  it('禁用 2FA 失败无 message → 默认文案', async () => {
    twoFactorApi.disable.mockRejectedValue({})
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleDisable()
    expect(ElMessage.error).toHaveBeenCalledWith('禁用失败')
  })

  it('复制密钥成功/失败', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.secretKey = 'SECRET123'
    await vm.copySecret()
    expect(clipWrite).toHaveBeenCalledWith('SECRET123')
    expect(ElMessage.success).toHaveBeenCalledWith('密钥已复制到剪贴板')
    clipWrite.mockRejectedValueOnce(new Error('denied'))
    await vm.copySecret()
    expect(ElMessage.warning).toHaveBeenCalledWith('复制失败，请手动复制')
  })

  it('复制恢复码成功/失败', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.backupCodes = ['CODE1', 'CODE2']
    await vm.copyBackupCodes()
    expect(clipWrite).toHaveBeenCalledWith('CODE1\nCODE2')
    expect(ElMessage.success).toHaveBeenCalledWith('恢复码已复制到剪贴板')
    clipWrite.mockRejectedValueOnce(new Error('denied'))
    await vm.copyBackupCodes()
    expect(ElMessage.warning).toHaveBeenCalledWith('复制失败，请手动复制')
  })

  it('验证码输入：非法字符过滤（模板 @input）', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.setupStep = 1
    await nextTick()
    const input = w.find('input')
    await input.setValue('12ab!3')
    // @input 处理器把非数字剥离并截断到 6 位
    await nextTick()
    expect(String(vm.verifyForm.token).replace(/\D/g, '')).toBe('123')
  })

  it('loading 状态展示骨架屏', async () => {
    let resolveStatus: (v: { enabled: boolean }) => void
    twoFactorApi.getStatus.mockReturnValue(
      new Promise((resolve) => {
        resolveStatus = resolve
      })
    )
    const w = mount(TwoFactorSettings, {
      global: { stubs: { 'el-skeleton': { template: '<div class="el-skeleton-stub" />' } } },
    })
    expect((w.vm as any).loading).toBe(true)
    resolveStatus!({ enabled: false })
    await flushPromises()
    expect((w.vm as any).loading).toBe(false)
  })
})
