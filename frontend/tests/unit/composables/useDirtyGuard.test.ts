import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, ref, h } from 'vue'
import { ElMessageBox } from 'element-plus'

const mockConfirm = vi.fn()
vi.mock('element-plus', () => ({
  ElMessageBox: { confirm: (...args: any[]) => mockConfirm(...args) },
}))

const mockBeforeRouteLeave = vi.fn()
vi.mock('vue-router', () => ({
  onBeforeRouteLeave: (cb: any) => mockBeforeRouteLeave(cb),
}))

import { useDirtyGuard } from '@/composables/useDirtyGuard'

const TestGuard = defineComponent({
  name: 'TestGuard',
  props: { dirty: { type: Boolean, default: false } },
  setup(props) {
    const isDirty = ref(props.dirty)
    useDirtyGuard(isDirty)
    return { isDirty }
  },
  render() {
    return h('div')
  },
})

describe('useDirtyGuard', () => {
  let wrapper: ReturnType<typeof mount> | null = null

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    wrapper?.unmount()
    wrapper = null
  })

  function mountGuard(dirty: boolean) {
    wrapper = mount(TestGuard, { props: { dirty } })
    return wrapper
  }

  it('挂载时注册 beforeRouteLeave 守卫与 beforeunload 监听', () => {
    const addSpy = vi.spyOn(window, 'addEventListener')
    mountGuard(false)
    expect(mockBeforeRouteLeave).toHaveBeenCalledTimes(1)
    expect(addSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function))
    addSpy.mockRestore()
  })

  it('无未保存更改时 confirmLeave 直接返回 true', async () => {
    mountGuard(false)
    const guard = mockBeforeRouteLeave.mock.calls[0][0]
    await expect(guard()).resolves.toBe(true)
    expect(mockConfirm).not.toHaveBeenCalled()
  })

  it('有未保存更改且确认离开时返回 true', async () => {
    mockConfirm.mockResolvedValueOnce('confirm')
    mountGuard(true)
    const guard = mockBeforeRouteLeave.mock.calls[0][0]
    await expect(guard()).resolves.toBe(true)
    expect(mockConfirm).toHaveBeenCalledWith(
      '有未保存的更改，确定离开吗？',
      '提示',
      expect.objectContaining({ confirmButtonText: '离开', type: 'warning' })
    )
  })

  it('有未保存更改且取消时返回 false', async () => {
    mockConfirm.mockRejectedValueOnce('cancel')
    mountGuard(true)
    const guard = mockBeforeRouteLeave.mock.calls[0][0]
    await expect(guard()).resolves.toBe(false)
  })

  it('beforeunload 且无未保存更改时不拦截', () => {
    mountGuard(false)
    const e = new Event('beforeunload')
    const preventSpy = vi.spyOn(e, 'preventDefault')
    window.dispatchEvent(e)
    expect(preventSpy).not.toHaveBeenCalled()
  })

  it('beforeunload 且有未保存更改时 preventDefault 并设置 returnValue', () => {
    mountGuard(true)
    const e = new Event('beforeunload')
    const preventSpy = vi.spyOn(e, 'preventDefault')
    Object.defineProperty(e, 'returnValue', { value: '', writable: true })
    window.dispatchEvent(e)
    expect(preventSpy).toHaveBeenCalled()
    expect(e.returnValue).toBe('')
  })

  it('组件卸载时移除 beforeunload 监听', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener')
    mountGuard(false)
    wrapper!.unmount()
    expect(removeSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function))
    removeSpy.mockRestore()
  })
})
