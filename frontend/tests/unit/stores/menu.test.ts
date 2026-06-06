import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock vue-router
vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/dashboard' }),
}))

// Mock auth store
vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({ user: { id: 1, role: 'admin' } }),
}))

import { useMenuStore } from '@/stores/menu'

describe('useMenuStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initial state: modules 存在, activeMenu 取自 route.path', () => {
    const store = useMenuStore()
    expect(store.modules).toBeDefined()
    expect(store.activeMenu).toBe('/dashboard')
  })

  it('openedModule 根据 route.path 计算', () => {
    const store = useMenuStore()
    expect(store.openedModule).toBeDefined()
  })
})
