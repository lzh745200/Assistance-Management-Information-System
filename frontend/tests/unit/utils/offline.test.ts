import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { isOfflineMode, setOfflineMode, onNetworkChange } from '@/utils/offline'

describe('utils/offline', () => {
  beforeEach(() => {
    localStorage.clear()
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true })
  })

  it('isOfflineMode: navigator.onLine=true, no flag -> false', () => {
    expect(isOfflineMode()).toBe(false)
  })

  it('isOfflineMode: navigator.onLine=false -> true', () => {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true })
    expect(isOfflineMode()).toBe(true)
  })

  it('isOfflineMode: offline_mode=true -> true', () => {
    localStorage.setItem('offline_mode', 'true')
    expect(isOfflineMode()).toBe(true)
  })

  it('isOfflineMode: offline_mode=false 但离线 -> true (navigator 优先)', () => {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true })
    localStorage.setItem('offline_mode', 'false')
    expect(isOfflineMode()).toBe(true)
  })

  it('setOfflineMode(true) 写入 "true"', () => {
    setOfflineMode(true)
    expect(localStorage.getItem('offline_mode')).toBe('true')
  })

  it('setOfflineMode(false) 写入 "false"', () => {
    setOfflineMode(false)
    expect(localStorage.getItem('offline_mode')).toBe('false')
  })

  it('onNetworkChange 调 callback + 返回 cleanup', () => {
    const cb = vi.fn()
    const cleanup = onNetworkChange(cb)
    expect(typeof cleanup).toBe('function')
    // Simulate online/offline events
    window.dispatchEvent(new Event('online'))
    window.dispatchEvent(new Event('offline'))
    expect(cb).toHaveBeenCalledWith(true)
    expect(cb).toHaveBeenCalledWith(false)
    // cleanup removes listeners
    cb.mockClear()
    cleanup()
    window.dispatchEvent(new Event('online'))
    expect(cb).not.toHaveBeenCalled()
  })
})
