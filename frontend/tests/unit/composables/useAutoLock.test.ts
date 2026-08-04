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

  it('配置 0/负数 回退默认', () => {
    localStorage.setItem('auto-lock-minutes', '0')
    let { w, getApi } = mountHost()
    expect(getApi().getMinutes()).toBe(15)
    w.unmount()
    localStorage.setItem('auto-lock-minutes', '-5')
    ;({ w, getApi } = mountHost())
    expect(getApi().getMinutes()).toBe(15)
    w.unmount()
  })

  it('click/keydown/touchstart 事件均重置计时器', () => {
    const onLock = vi.fn()
    const { w, getApi } = mountHost({ getMinutes: () => 1, onLock })
    const api = getApi()
    vi.advanceTimersByTime(50 * 1000)
    window.dispatchEvent(new Event('click'))
    window.dispatchEvent(new Event('keydown'))
    window.dispatchEvent(new Event('touchstart'))
    // 事件在 t=50s 重置计时器 → 下一次触发在 t=110s
    vi.advanceTimersByTime(59 * 1000 + 100)
    expect(onLock).not.toHaveBeenCalled()
    vi.advanceTimersByTime(60 * 1000)
    expect(onLock).toHaveBeenCalledTimes(1)
    w.unmount()
  })

  it('resetTimer 二次调用时清除旧定时器（timer 非空分支）', () => {
    const onLock = vi.fn()
    const { w, getApi } = mountHost({ getMinutes: () => 1, onLock })
    const api = getApi()
    const clearSpy = vi.spyOn(window, 'clearTimeout')
    api.resetTimer()
    expect(clearSpy).toHaveBeenCalledTimes(1)
    w.unmount()
  })

  it('默认 lockNow（未注入 onLock）静默执行（require 在 ESM 测试环境不可用走 catch）', () => {
    // vitest/vite-node 的模块级 require shim 无法解析 @/ 别名，
    // 且 vi.mock 不拦截 require 路径 → 必走 try 的 catch 分支（静默）
    const { w } = mountHost()
    expect(() => vi.advanceTimersByTime(15 * 60 * 1000 + 100)).not.toThrow()
    w.unmount()
  })

  it('unbind 幂等：二次调用不抛错', () => {
    const { w, getApi } = mountHost()
    const api = getApi()
    api.unbind()
    expect(() => api.unbind()).not.toThrow()
    w.unmount()
  })
})
