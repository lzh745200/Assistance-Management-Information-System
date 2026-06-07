import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIndustryStore } from '@/stores/industry'

describe('useIndustryStore', () => {
  let store: ReturnType<typeof useIndustryStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useIndustryStore() })

  it('initializes with defaults', () => {
    expect(store.industryList).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchIndustries sets loading state', async () => {
    await store.fetchIndustries()
    expect(store.loading).toBe(false)
  })
})
