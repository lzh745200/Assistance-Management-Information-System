import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'

describe('useUserStore', () => {
  let store: ReturnType<typeof useUserStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useUserStore() })
  it('should initialize with empty userList', () => {
    expect(store.userList).toEqual([])
    expect(store.total).toBe(0)
  })
  it('should have fetchUsers method', () => {
    expect(typeof store.fetchUsers).toBe('function')
  })
})
