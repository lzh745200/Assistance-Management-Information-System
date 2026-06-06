import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRuralWorkStore } from '@/stores/ruralWork'

describe('useRuralWorkStore', () => {
  let store: ReturnType<typeof useRuralWorkStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useRuralWorkStore()
  })

  it('initializes with defaults', () => {
    expect(store.works).toEqual([])
    expect(store.currentWork).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchWorks sets loading state', async () => {
    await store.fetchWorks()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })
})
