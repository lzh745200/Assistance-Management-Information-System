import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useConfigStore } from '@/stores/config'

describe('useConfigStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('appName 和 version 是常量', () => {
    const store = useConfigStore()
    expect(store.appName).toBe('帮扶管理信息系统')
    expect(store.version).toBe('1.2.0')
  })

  it('无 localStorage 时 theme 默认 light', () => {
    const store = useConfigStore()
    expect(store.theme).toBe('light')
  })

  it('localStorage 存在时 theme 从其中读取', () => {
    localStorage.setItem('theme', 'dark')
    setActivePinia(createPinia())
    const store = useConfigStore()
    expect(store.theme).toBe('dark')
  })

  it('setTheme 修改 theme 并持久化到 localStorage', () => {
    const store = useConfigStore()
    store.setTheme('dark')
    expect(store.theme).toBe('dark')
    expect(localStorage.getItem('theme')).toBe('dark')
  })

  it('setTheme 多次调用会覆盖', () => {
    const store = useConfigStore()
    store.setTheme('dark')
    store.setTheme('light')
    expect(store.theme).toBe('light')
    expect(localStorage.getItem('theme')).toBe('light')
  })
})
