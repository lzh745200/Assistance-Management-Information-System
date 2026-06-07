import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useVillagerStore } from '@/stores/villager'

describe('useVillagerStore', () => {
  let store: ReturnType<typeof useVillagerStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useVillagerStore() })

  it('initializes with defaults', () => {
    expect(store.villagerList).toEqual([])
    expect(store.current).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.total).toBe(0)
  })

  it('fetchVillagers does not throw', async () => {
    await expect(store.fetchVillagers()).resolves.toBeUndefined()
  })

  it('createVillager returns mock response', async () => {
    const res = await store.createVillager({})
    expect(res.code).toBe(200)
  })
})
