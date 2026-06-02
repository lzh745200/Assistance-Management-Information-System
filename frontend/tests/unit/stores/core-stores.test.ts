import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useOrganizationStore } from '@/stores/organization'

describe('useOrganizationStore', () => {
  let store: ReturnType<typeof useOrganizationStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useOrganizationStore() })
  it('initializes with empty orgs', () => {
    expect(store.orgs).toEqual([])
    expect(store.current).toBeNull()
  })
})
