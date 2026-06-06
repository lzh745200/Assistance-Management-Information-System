import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/request', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
}))

vi.mock('@/utils/unwrapList', () => ({
  unwrapList: (res: any) => ({ items: res?.data ?? [], total: res?.total ?? 0 }),
}))

import { useVillageStore } from '@/stores/village'

describe('useVillageStore', () => {
  let store: ReturnType<typeof useVillageStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useVillageStore()
    vi.clearAllMocks()
  })

  it('initializes with defaults', () => {
    expect(store.villages).toEqual([])
    expect(store.current).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.total).toBe(0)
  })

  it('sets loading state', () => {
    store.loading = true
    expect(store.loading).toBe(true)
  })
})
