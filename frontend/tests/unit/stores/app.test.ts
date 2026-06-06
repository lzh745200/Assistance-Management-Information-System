import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '@/stores/app'

describe('useAppStore', () => {
  let store: ReturnType<typeof useAppStore>
  beforeEach(() => {
    setActivePinia(createPinia())
    store = useAppStore()
  })

  it('初始 sidebarCollapsed=false, theme=light', () => {
    expect(store.sidebarCollapsed).toBe(false)
    expect(store.theme).toBe('light')
  })

  it('toggleSidebar 翻转 sidebarCollapsed', () => {
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('setTheme 修改 theme', () => {
    store.setTheme('dark')
    expect(store.theme).toBe('dark')
  })

  it('支持自定义主题字符串', () => {
    store.setTheme('sepia')
    expect(store.theme).toBe('sepia')
  })
})
