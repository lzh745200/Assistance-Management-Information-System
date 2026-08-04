import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import {
  useConfigStore,
  applyThemeToDom,
  DEFAULT_THEME,
  THEME_STORAGE_KEY,
  THEME_OPTIONS,
} from '@/stores/config'

describe('useConfigStore', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    setActivePinia(createPinia())
  })

  it('appName 和 version 是常量', () => {
    const store = useConfigStore()
    expect(store.appName).toBe('帮扶管理信息系统')
    expect(store.version).toBe('1.5.0')
  })

  it('无 localStorage 时 theme 默认 default（军绿）', () => {
    const store = useConfigStore()
    expect(store.theme).toBe('default')
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

  it('setTheme 非 default 主题设置 data-theme 属性', () => {
    const store = useConfigStore()
    store.setTheme('outdoor')
    expect(document.documentElement.getAttribute('data-theme')).toBe('outdoor')
  })

  it('setTheme default 移除 data-theme 属性（渲染 :root 军绿）', () => {
    const store = useConfigStore()
    store.setTheme('outdoor')
    store.setTheme('default')
    expect(document.documentElement.hasAttribute('data-theme')).toBe(false)
    expect(localStorage.getItem('theme')).toBe('default')
  })
})

describe('applyThemeToDom', () => {
  beforeEach(() => {
    document.documentElement.removeAttribute('data-theme')
  })

  it('default 移除属性', () => {
    document.documentElement.setAttribute('data-theme', 'dark')
    applyThemeToDom(DEFAULT_THEME)
    expect(document.documentElement.hasAttribute('data-theme')).toBe(false)
  })

  it('其他主题设置属性', () => {
    applyThemeToDom('high-contrast')
    expect(document.documentElement.getAttribute('data-theme')).toBe('high-contrast')
  })
})

describe('THEME_OPTIONS / THEME_STORAGE_KEY', () => {
  it('包含 default 军绿选项且值不重复', () => {
    const values = THEME_OPTIONS.map((t) => t.value)
    expect(values).toContain('default')
    expect(new Set(values).size).toBe(values.length)
    expect(THEME_OPTIONS.every((t) => t.label.length > 0)).toBe(true)
  })

  it('THEME_STORAGE_KEY 为 theme', () => {
    expect(THEME_STORAGE_KEY).toBe('theme')
  })
})
