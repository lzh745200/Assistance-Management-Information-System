import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { useAutoLock } from '@/composables/useAutoLock'

function mountHost(opts: any = {}) {
  let api: any
  const Comp = defineComponent({
    setup() {
      api = useAutoLock(opts)
      return () => h('div')
    },
  })
  const w = mount(Comp, { attachTo: document.body })
  return { w, getApi: () => api }
}

describe('useAutoLock（自动锁屏）', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    localStorage.clear()
  })
  afterEach(() => {
    vi.useRealTimers()
    document.body.innerHTML = ''
  })

  it('默认 15 分钟锁屏', () => {
    const onLock = vi.fn()
    const { w, getApi } = mountHost({ onLock })
    const api = getApi()
    expect(api.getMinutes()).toBe(15)
    vi.advanceTimersByTime(15 * 60 * 1000 + 100)
    expect(onLock).toHaveBeenCalledTimes(1)
    w.unmount()
  })

  it('自定义分钟数与 onLock', () => {
    const onLock = vi.fn()
    const { w, getApi } = mountHost({ getMinutes: () => 2, onLock })
    const api = getApi()
    expect(api.getMinutes()).toBe(2)
    vi.advanceTimersByTime(2 * 60 * 1000 + 100)
    expect(onLock).toHaveBeenCalledTimes(1)
    w.unmount()
  })

  it('用户操作重置计时器', () => {
    const onLock = vi.fn()
    const { w, getApi } = mountHost({ getMinutes: () => 2, onLock })
    const api = getApi()
    // 1 分钟后有操作 → 重置
    vi.advanceTimersByTime(60 * 1000)
    window.dispatchEvent(new Event('mousemove'))
    vi.advanceTimersByTime(60 * 1000 + 100)
    expect(onLock).not.toHaveBeenCalled()
    vi.advanceTimersByTime(2 * 60 * 1000)
    expect(onLock).toHaveBeenCalledTimes(1)
    w.unmount()
  })

  it('卸载时清理定时器', () => {
    const onLock = vi.fn()
    const { w, getApi } = mountHost({ getMinutes: () => 1, onLock })
    const api = getApi()
    api.unbind()
    vi.advanceTimersByTime(10 * 60 * 1000)
    expect(onLock).not.toHaveBeenCalled()
    w.unmount()
  })

  it('localStorage 配置读取', () => {
    localStorage.setItem('auto-lock-minutes', '30')
    const { w, getApi } = mountHost()
    expect(getApi().getMinutes()).toBe(30)
    w.unmount()
  })

  it('非法配置回退默认', () => {
    localStorage.setItem('auto-lock-minutes', 'abc')
    const { w, getApi } = mountHost()
    expect(getApi().getMinutes()).toBe(15)
    w.unmount()
  })
})
