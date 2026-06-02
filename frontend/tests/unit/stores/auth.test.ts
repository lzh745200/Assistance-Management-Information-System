import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

describe('useAuthStore', () => {
  let store: ReturnType<typeof useAuthStore>
  beforeEach(() => {
    setActivePinia(createPinia())
    store = useAuthStore()
    localStorage.clear()
    sessionStorage.clear()
  })
  it('starts unauthenticated', () => {
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(store.token).toBe('')
  })
  it('logout clears state', () => {
    store.logout()
    expect(store.token).toBe('')
    expect(store.user).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })
})
