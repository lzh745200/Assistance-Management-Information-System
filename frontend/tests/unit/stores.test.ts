import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'

describe('useAppStore', () => {
  let store: ReturnType<typeof useAppStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useAppStore() })
  it('initializes with defaults', () => {
    expect(store).toBeDefined()
  })
})

describe('useUserStore', () => {
  let store: ReturnType<typeof useUserStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useUserStore() })
  it('initializes with empty user list', () => {
    expect(store.userList).toEqual([])
  })
})
