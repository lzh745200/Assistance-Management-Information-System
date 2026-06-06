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
})
