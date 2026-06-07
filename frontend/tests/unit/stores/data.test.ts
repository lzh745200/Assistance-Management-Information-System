import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDataStore } from '@/stores/data'

describe('useDataStore', () => {
  let store: ReturnType<typeof useDataStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useDataStore() })

  it('initializes with defaults', () => {
    expect(store.dataList).toEqual([])
    expect(store.currentData).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.total).toBe(0)
  })

  it('setCurrentData updates current', () => {
    store.setCurrentData({ id: 1, name: 'test' })
    expect(store.currentData).toEqual({ id: 1, name: 'test' })
  })

  it('fetchData sets loading state', async () => {
    await store.fetchData()
    expect(store.loading).toBe(false)
  })
})
