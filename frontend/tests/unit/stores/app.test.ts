import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '@/stores/app'

describe('useAppStore', () => {
  let store: ReturnType<typeof useAppStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useAppStore() })

  it('initializes with defaults', () => {
    expect(store.sidebarCollapsed).toBeDefined()
  })
})
