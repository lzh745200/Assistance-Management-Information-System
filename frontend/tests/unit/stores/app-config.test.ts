import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '@/stores/app'
import { useConfigStore } from '@/stores/config'

describe('stores/app + stores/config', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  describe('useAppStore', () => {
    it('初始状态', () => {
      const a = useAppStore()
      expect(a.sidebarCollapsed).toBe(false)
      expect(a.theme).toBe('light')
    })

    it('toggleSidebar 翻转', () => {
      const a = useAppStore()
      a.toggleSidebar()
      expect(a.sidebarCollapsed).toBe(true)
      a.toggleSidebar()
      expect(a.sidebarCollapsed).toBe(false)
    })

    it('setTheme', () => {
      const a = useAppStore()
      a.setTheme('dark')
      expect(a.theme).toBe('dark')
    })
  })

  describe('useConfigStore', () => {
    it('默认值', () => {
      const c = useConfigStore()
      expect(c.appName).toBe('帮扶管理信息系统')
      expect(c.version).toBe('1.2.0')
      expect(c.theme).toBe('light')  // localStorage empty
    })

    it('从 localStorage 读取 theme', () => {
      localStorage.setItem('theme', 'dark')
      const c = useConfigStore()
      expect(c.theme).toBe('dark')
    })

    it('setTheme 更新 ref + localStorage', () => {
      const c = useConfigStore()
      c.setTheme('sepia')
      expect(c.theme).toBe('sepia')
      expect(localStorage.getItem('theme')).toBe('sepia')
    })
  })
})
