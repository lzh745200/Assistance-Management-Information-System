import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '@/stores/app'

describe('useAppStore', () => {
  let store: ReturnType<typeof useAppStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useAppStore() })
  it('initializes', () => { expect(store).toBeDefined() })
  it('toggles sidebar', () => {
    const before = store.sidebarCollapsed
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(!before)
  })
})
