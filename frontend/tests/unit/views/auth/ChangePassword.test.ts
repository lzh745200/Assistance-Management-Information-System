/**
 * views/auth/ChangePassword.vue 覆盖率攻坚
 * 覆盖：密码强度校验、提交成功/失败/取消、强制改密模式、取消编辑
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import { nextTick, defineComponent, h } from 'vue'

enableAutoUnmount(afterEach)

const { ElMessage, ElMessageBox, mockRouterBack, userStore, authStore, freezeReq, cancelReq } =
  vi.hoisted(() => {
    return {
      ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
      ElMessageBox: { confirm: vi.fn(), alert: vi.fn() },
      mockRouterBack: vi.fn(),
      userStore: {
        changePassword: vi.fn(),
        logout: vi.fn(),
      },
      authStore: { mustChangePassword: false, logout: vi.fn() },
      freezeReq: vi.fn(),
      cancelReq: vi.fn(),
    }
  })

const formState = vi.hoisted(() => ({
  validateFn: (cb: (valid: boolean) => void) => cb(true),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(() => Promise.resolve()),
    back: mockRouterBack,
    resolve: vi.fn(() => ({ name: 'x', matched: [{ path: '/x' }] })),
  }),
  useRoute: () => ({ params: {}, query: {} }),
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => userStore,
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => authStore,
}))

vi.mock('@/api/request', () => ({
  freezeRequests: freezeReq,
  cancelAllRequests: cancelReq,
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
  apiRequest: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox,
  ElForm: { name: 'ElForm' },
  ElNotification: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
}))

import ChangePassword from '@/views/auth/ChangePassword.vue'

const ElFormStub = defineComponent({
  name: 'ElForm',
  props: ['model', 'rules'],
  emits: ['update:modelValue'],
  setup(_props, { expose, slots }) {
    const validate = (cb: (valid: boolean) => void) => formState.validateFn(cb)
    expose({ validate, validateField: vi.fn(), clearValidate: vi.fn() })
    return () => h('form', { class: 'el-form-stub' }, [slots.default?.()])
  },
})

const ElInputStub = defineComponent({
  name: 'ElInput',
  props: ['modelValue'],
  emits: ['update:modelValue'],
  setup(props, { emit, attrs }) {
    return () =>
      h('input', {
        value: props.modelValue,
        onInput: (e: Event) => {
          const v = (e.target as HTMLInputElement).value
          emit('update:modelValue', v)
          ;(attrs as any).onInput?.(e)
        },
      })
  },
})

async function mountComp() {
  const w = mount(ChangePassword, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-form': ElFormStub,
        'el-form-item': {
          name: 'ElFormItem',
          template: '<div class="el-form-item-stub"><slot /></div>',
        },
        'el-input': ElInputStub,
        'el-button': {
          name: 'ElButton',
          template: '<button @click="$emit(\'click\')"><slot /></button>',
          emits: ['click'],
        },
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot /><slot name="header" /></div>',
        },
        'el-icon': { name: 'ElIcon', template: '<span><slot /></span>' },
      },
    },
  })
  await flushPromises()
  await nextTick()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  formState.validateFn = (cb) => cb(true)
  ElMessageBox.confirm.mockResolvedValue('confirm')
  userStore.changePassword.mockResolvedValue({})
  userStore.logout.mockResolvedValue(undefined)
  authStore.logout.mockResolvedValue(undefined)
  authStore.mustChangePassword = false
})

describe('ChangePassword.vue', () => {
  it('渲染表单', async () => {
    const w = await mountComp()
    expect(w.find('.change-password-container').exists()).toBe(true)
    expect((w.vm as any).isForceChange).toBe(false)
  })

  it('强制改密模式：展示提示', async () => {
    authStore.mustChangePassword = true
    const w = await mountComp()
    expect((w.vm as any).isForceChange).toBe(true)
    expect(w.text()).toContain('首次登录或密码已过期')
  })

  it('validatePassword：空值隐藏提示', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.validatePassword('')
    expect(vm.showPasswordHint).toBe(false)
  })

  it('validatePassword：各强度等级', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    // 仅长度+小写达标（12位小写）→ 2 项 → level 1
    vm.validatePassword('aaaaaaaaaaaa')
    expect(vm.passwordStrengthData.level).toBe(1)
    expect(vm.passwordStrengthData.text).toBe('弱')
    expect(vm.passwordStrengthData.validCount).toBe(2)
    // 大小写+数字（无特殊）→ 3 项 → level 2，且清除错误提示
    vm.newPasswordError = '旧错误'
    vm.validatePassword('Ab1aaaaaaa')
    expect(vm.passwordStrengthData.level).toBe(2)
    expect(vm.passwordStrengthData.text).toBe('中')
    expect(vm.newPasswordError).toBe('')
    // 全部满足 → level 3
    vm.validatePassword('Ab1!abcdefghij')
    expect(vm.passwordStrengthData.level).toBe(3)
    expect(vm.passwordStrengthData.text).toBe('强')
    // 0 项 → level 1（小写字母计 1 项）
    vm.validatePassword('a')
    expect(vm.passwordStrengthData.level).toBe(1)
    expect(vm.passwordStrengthData.text).toBe('弱')
  })

  it('输入新密码触发 validatePassword（模板 @input）', async () => {
    const w = await mountComp()
    const inputs = w.findAll('input')
    const newPwdInput = inputs[1]
    const vm = w.vm as any
    // 覆盖 oldPassword / newPassword / confirmPassword 三个 v-model
    await inputs[0].setValue('oldpass1')
    expect(vm.passwordForm.oldPassword).toBe('oldpass1')
    await newPwdInput.setValue('abc')
    // 模板 @input="validatePassword" 直接传入事件对象（生产行为），提示展示即可
    expect(vm.showPasswordHint).toBe(true)
    vm.passwordStrengthData.length = 14
    await nextTick()
    expect(w.text()).toContain('密码长度至少12个字符')
    await inputs[2].setValue('abc')
    expect(vm.passwordForm.confirmPassword).toBe('abc')
    // 直接驱动 hint 渲染（含强度指示器文本）
    vm.showPasswordHint = true
    vm.passwordStrengthData.length = 14
    vm.passwordStrengthData.hasUppercase = true
    vm.passwordStrengthData.hasLowercase = true
    vm.passwordStrengthData.hasNumber = true
    vm.passwordStrengthData.hasSpecial = true
    vm.passwordStrengthData.level = 3
    vm.passwordStrengthData.text = '强'
    await nextTick()
    expect(w.text()).toContain('强')
    await nextTick()
  })

  it('handleChangePassword：表单引用为空 → 直接返回', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.passwordFormRef = null
    await vm.handleChangePassword()
    expect(ElMessage.warning).not.toHaveBeenCalled()
    expect(userStore.changePassword).not.toHaveBeenCalled()
  })

  it('handleChangePassword：校验失败 → 警告', async () => {
    formState.validateFn = (cb) => cb(false)
    const w = await mountComp()
    await (w.vm as any).handleChangePassword()
    expect(ElMessage.warning).toHaveBeenCalledWith('请检查输入信息')
    expect(userStore.changePassword).not.toHaveBeenCalled()
  })

  it('handleChangePassword：成功 → 冻结请求 + 登出 + 跳转', async () => {
    vi.useFakeTimers()
    const w = await mountComp()
    const vm = w.vm as any
    vm.passwordForm.oldPassword = 'oldpass1'
    vm.passwordForm.newPassword = 'Ab1!abcdefghij'
    vm.passwordForm.confirmPassword = 'Ab1!abcdefghij'
    await vm.handleChangePassword()
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(userStore.changePassword).toHaveBeenCalledWith('oldpass1', 'Ab1!abcdefghij')
    expect(freezeReq).toHaveBeenCalled()
    expect(cancelReq).toHaveBeenCalled()
    expect(authStore.logout).toHaveBeenCalled()
    expect(userStore.logout).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('密码修改成功，请使用新密码重新登录')
    expect(vm.loading).toBe(false)
    await vi.advanceTimersByTimeAsync(150)
    vi.useRealTimers()
  })

  it('handleChangePassword：确认取消（Cancel）→ 直接返回', async () => {
    ElMessageBox.confirm.mockRejectedValue({ name: 'Cancel' })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleChangePassword()
    expect(userStore.changePassword).not.toHaveBeenCalled()
    expect(vm.loading).toBe(false)
  })

  it('handleChangePassword：当前密码错误（field=old_password）', async () => {
    userStore.changePassword.mockRejectedValue({
      response: { data: { field: 'old_password', message: '当前密码错误' } },
    })
    const w = await mountComp()
    const vm = w.vm as any
    vm.newPasswordError = 'x'
    await vm.handleChangePassword()
    expect(ElMessage.error).toHaveBeenCalledWith({
      message: '当前密码错误，请重新输入',
      duration: 5000,
    })
  })

  it('handleChangePassword：新密码策略错误（field=new_password）', async () => {
    userStore.changePassword.mockRejectedValue({
      response: { data: { field: 'new_password', detail: '密码强度不足' } },
    })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleChangePassword()
    expect(vm.newPasswordError).toBe('密码强度不足')
    expect(ElMessage.error).toHaveBeenCalledWith({ message: '密码强度不足', duration: 5000 })
  })

  it('handleChangePassword：无任何错误信息 → 默认提示', async () => {
    userStore.changePassword.mockRejectedValue({})
    const w = await mountComp()
    await (w.vm as any).handleChangePassword()
    expect(ElMessage.error).toHaveBeenCalledWith('密码修改失败，请检查网络连接或联系管理员')
  })

  it('handleChangePassword：其它错误带字符串 detail → 展示 detail', async () => {
    userStore.changePassword.mockRejectedValue({
      response: { data: { detail: '503 服务不可用' } },
    })
    const w = await mountComp()
    await (w.vm as any).handleChangePassword()
    expect(ElMessage.error).toHaveBeenCalledWith('503 服务不可用')
  })

  it('handleChangePassword：其它错误带非字符串 detail → 默认文案', async () => {
    userStore.changePassword.mockRejectedValue({
      response: { data: { detail: { code: 1 } } },
    })
    const w = await mountComp()
    await (w.vm as any).handleChangePassword()
    expect(ElMessage.error).toHaveBeenCalledWith('密码修改失败')
  })

  it('handleChangePassword：logout 抛错被吞掉仍成功', async () => {
    authStore.logout.mockImplementation(() => {
      throw new Error('logout failed')
    })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.handleChangePassword()
    expect(ElMessage.success).toHaveBeenCalledWith('密码修改成功，请使用新密码重新登录')
  })

  it('handleCancel：无输入 → 直接返回', async () => {
    const w = await mountComp()
    await (w.vm as any).handleCancel()
    expect(mockRouterBack).toHaveBeenCalled()
    expect(ElMessageBox.confirm).not.toHaveBeenCalled()
  })

  it('handleCancel：有输入 → 确认后返回', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.passwordForm.oldPassword = 'x'
    await vm.handleCancel()
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(mockRouterBack).toHaveBeenCalled()
  })

  it('handleCancel：有输入但取消确认 → 留在页面', async () => {
    ElMessageBox.confirm.mockRejectedValue(new Error('cancel'))
    const w = await mountComp()
    const vm = w.vm as any
    vm.passwordForm.newPassword = 'y'
    await vm.handleCancel()
    expect(mockRouterBack).not.toHaveBeenCalled()
  })

  it('watch：新密码变化且与确认密码不一致 → validateField', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.passwordForm.confirmPassword = 'Ab1!abcdefghij'
    vm.passwordForm.newPassword = 'Ab1!abcdefghik'
    await nextTick()
    expect(vm.passwordFormRef?.validateField).toHaveBeenCalledWith('confirmPassword')
  })

  it('watch：新密码变化与确认一致 → 不触发', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.passwordForm.confirmPassword = 'Ab1!abcdefghij'
    vm.passwordForm.newPassword = 'Ab1!abcdefghij'
    await nextTick()
    expect(vm.passwordFormRef?.validateField).not.toHaveBeenCalled()
  })

  it('表单规则：新旧密码相同校验器', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    const validator = vm.passwordRules.newPassword[1].validator
    const cb = vi.fn()
    validator(null, '', cb)
    expect(cb).toHaveBeenCalledWith(new Error('请输入新密码'))
    vm.passwordForm.oldPassword = 'same'
    validator(null, 'same', cb)
    expect(cb).toHaveBeenCalledWith(new Error('新密码不能与当前密码相同'))
    validator(null, 'weak', cb)
    expect(cb).toHaveBeenCalledWith(new Error('密码强度不足，需满足全部5项规则且长度≥12位'))
    vm.passwordStrengthData.validCount = 5
    vm.passwordStrengthData.length = 14
    validator(null, 'Ab1!abcdefghij', cb)
    expect(cb).toHaveBeenCalledWith()
  })

  it('表单规则：确认密码校验器', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    const validator = vm.passwordRules.confirmPassword[1].validator
    const cb = vi.fn()
    validator(null, '', cb)
    expect(cb).toHaveBeenCalledWith(new Error('请再次输入新密码'))
    vm.passwordForm.newPassword = 'A'
    validator(null, 'B', cb)
    expect(cb).toHaveBeenCalledWith(new Error('两次输入的密码不一致'))
    validator(null, 'A', cb)
    expect(cb).toHaveBeenCalledWith()
  })
})
