import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createDebounce, useDebounce } from '@/composables/useDebounce'

describe('createDebounce', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('在 delay 之后才调用 fn', () => {
    const fn = vi.fn()
    const debounced = createDebounce(fn, 300)
    debounced()
    expect(fn).not.toHaveBeenCalled()
    vi.advanceTimersByTime(300)
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('连续调用只触发最后一次', () => {
    const fn = vi.fn()
    const debounced = createDebounce(fn, 300)
    debounced('a')
    vi.advanceTimersByTime(100)
    debounced('b')
    vi.advanceTimersByTime(100)
    debounced('c')
    vi.advanceTimersByTime(300)
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn).toHaveBeenCalledWith('c')
  })

  it('使用默认 delay=300', () => {
    const fn = vi.fn()
    const debounced = createDebounce(fn)
    debounced()
    vi.advanceTimersByTime(299)
    expect(fn).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('传递多个参数', () => {
    const fn = vi.fn()
    const debounced = createDebounce(fn, 100)
    debounced(1, 2, 3)
    vi.advanceTimersByTime(100)
    expect(fn).toHaveBeenCalledWith(1, 2, 3)
  })

  it('cancel 清除待执行的定时器', () => {
    const fn = vi.fn()
    const debounced = createDebounce(fn, 300)
    debounced('a')
    debounced.cancel()
    vi.advanceTimersByTime(500)
    expect(fn).not.toHaveBeenCalled()
  })

  it('cancel 无待执行定时器时不抛错', () => {
    const fn = vi.fn()
    const debounced = createDebounce(fn, 300)
    expect(() => {
      debounced.cancel()
      debounced.cancel()
    }).not.toThrow()
  })

  it('flush 立即执行并清除定时器', () => {
    const fn = vi.fn()
    const debounced = createDebounce(fn, 300)
    debounced('a')
    debounced.flush('b')
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn).toHaveBeenCalledWith('b')
    vi.advanceTimersByTime(500)
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('flush 无待执行调用时也立即执行', () => {
    const fn = vi.fn()
    const debounced = createDebounce(fn, 300)
    debounced.flush('c')
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn).toHaveBeenCalledWith('c')
  })

  it('cancel 后再调用可重新触发', () => {
    const fn = vi.fn()
    const debounced = createDebounce(fn, 300)
    debounced()
    debounced.cancel()
    debounced()
    vi.advanceTimersByTime(300)
    expect(fn).toHaveBeenCalledTimes(1)
  })
})

describe('useDebounce', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('debounce 触发后延迟调用 fn', () => {
    const fn = vi.fn()
    const { debounce } = useDebounce(200)
    debounce(fn)
    vi.advanceTimersByTime(200)
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('cancel 取消未触发的 fn', () => {
    const fn = vi.fn()
    const { debounce, cancel } = useDebounce(200)
    debounce(fn)
    cancel()
    vi.advanceTimersByTime(500)
    expect(fn).not.toHaveBeenCalled()
  })

  it('使用默认 delay=300', () => {
    const fn = vi.fn()
    const { debounce } = useDebounce()
    debounce(fn)
    vi.advanceTimersByTime(300)
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('连续 debounce 重置定时器，只执行最后一次', () => {
    const fn = vi.fn()
    const { debounce } = useDebounce(200)
    debounce(fn)
    vi.advanceTimersByTime(100)
    debounce(fn)
    vi.advanceTimersByTime(199)
    expect(fn).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('cancel 后可重新 debounce', () => {
    const fn = vi.fn()
    const { debounce, cancel } = useDebounce(200)
    debounce(fn)
    cancel()
    debounce(fn)
    vi.advanceTimersByTime(200)
    expect(fn).toHaveBeenCalledTimes(1)
  })
})
