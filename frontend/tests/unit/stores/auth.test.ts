import { describe, it, expect, beforeEach, vi } from 'vitest'

const mockApiRequest = vi.fn()
const mockSetCachedToken = vi.fn()
const mockGetCurrentUser = vi.fn()
const mockAuthStorageGetToken = vi.fn()
const mockAuthStorageGetUser = vi.fn()
const mockAuthStorageSetAuthData = vi.fn()
const mockAuthStorageSetUser = vi.fn()
const mockAuthStorageClear = vi.fn()

vi.mock('@/api/request', () => ({
  apiRequest: (...args: any[]) => mockApiRequest(...args),
  _setCachedToken: (...args: any[]) => mockSetCachedToken(...args),
}))

vi.mock('@/api/queries/user', () => ({
  getCurrentUser: (...args: any[]) => mockGetCurrentUser(...args),
}))

vi.mock('@/utils/authStorage', () => ({
  AuthStorage: {
    getToken: () => mockAuthStorageGetToken(),
    getUser: () => mockAuthStorageGetUser(),
    setAuthData: (...args: any[]) => mockAuthStorageSetAuthData(...args),
    setUser: (...args: any[]) => mockAuthStorageSetUser(...args),
    clear: (...args: any[]) => mockAuthStorageClear(...args),
  },
}))

vi.mock('@/utils/roleAccess', () => ({
  ADMIN_ROLES: ['admin', 'superuser'],
}))

import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthStorageGetToken.mockReturnValue('')
    mockAuthStorageGetUser.mockReturnValue(null)
    setActivePinia(createPinia())
  })

  it('isAuthenticated=false 当 token 为空', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
  })

  it('isAuthenticated=true 当 token 非空', () => {
    mockAuthStorageGetToken.mockReturnValue('abc123')
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
  })

  it('isAdmin=true 当 user.is_superuser=true', () => {
    mockAuthStorageGetUser.mockReturnValue({ id: 1, is_superuser: true })
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.isAdmin).toBe(true)
  })

  it('isAdmin=true 当 user.role 在 ADMIN_ROLES', () => {
    mockAuthStorageGetUser.mockReturnValue({ id: 1, role: 'admin' })
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.isAdmin).toBe(true)
  })

  it('isAdmin=false 当 user.role 不在 ADMIN_ROLES 且非 superuser', () => {
    mockAuthStorageGetUser.mockReturnValue({ id: 1, role: 'user' })
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.isAdmin).toBe(false)
  })

  it('mustChangePassword 默认为 false', () => {
    const store = useAuthStore()
    expect(store.mustChangePassword).toBe(false)
  })

  it('mustChangePassword=true 当 user.must_change_password=true', () => {
    mockAuthStorageGetUser.mockReturnValue({ id: 1, must_change_password: true })
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.mustChangePassword).toBe(true)
  })

  it('login 成功时返回 true 并持久化 token', async () => {
    mockApiRequest.mockResolvedValueOnce({
      code: 200,
      data: {
        access_token: 'tok123',
        refresh_token: 'ref456',
        token_type: 'bearer',
        user: { id: 1, username: 'alice' },
      },
    })
    const store = useAuthStore()
    const result = await store.login('alice', 'pwd')
    expect(result).toBe(true)
    expect(store.token).toBe('tok123')
    expect(store.user?.username).toBe('alice')
    expect(mockSetCachedToken).toHaveBeenCalledWith('tok123')
    expect(mockAuthStorageSetAuthData).toHaveBeenCalled()
  })

  it('login 失败时返回 false 并设置 error', async () => {
    mockApiRequest.mockResolvedValueOnce({
      code: 401,
      message: 'invalid credentials',
    })
    const store = useAuthStore()
    const result = await store.login('alice', 'wrong')
    expect(result).toBe(false)
    expect(store.error).toBe('invalid credentials')
  })

  it('login 异常时捕获并设置 error', async () => {
    mockApiRequest.mockRejectedValueOnce(new Error('timeout'))
    const store = useAuthStore()
    const result = await store.login('alice', 'pwd')
    expect(result).toBe(false)
    expect(store.error).toBe('timeout')
  })

  it('logout 清空 token, user, error', async () => {
    mockAuthStorageGetToken.mockReturnValue('tok')
    mockAuthStorageGetUser.mockReturnValue({ id: 1 })
    setActivePinia(createPinia())
    const store = useAuthStore()
    await store.logout()
    expect(store.token).toBe('')
    expect(store.user).toBeNull()
    expect(store.error).toBe('')
    expect(mockSetCachedToken).toHaveBeenCalledWith(null)
    expect(mockAuthStorageClear).toHaveBeenCalled()
  })

  it('fetchUser 无 token 时立即返回', async () => {
    const store = useAuthStore()
    await store.fetchUser()
    expect(mockGetCurrentUser).not.toHaveBeenCalled()
  })

  it('fetchUser 有 user 时立即返回 (无需重新拉取)', async () => {
    mockAuthStorageGetToken.mockReturnValue('tok')
    mockAuthStorageGetUser.mockReturnValue({ id: 1, username: 'a' })
    setActivePinia(createPinia())
    const store = useAuthStore()
    await store.fetchUser()
    expect(mockGetCurrentUser).not.toHaveBeenCalled()
  })

  it('fetchUser 成功时更新 user', async () => {
    mockAuthStorageGetToken.mockReturnValue('tok')
    setActivePinia(createPinia())
    mockGetCurrentUser.mockResolvedValueOnce({
      code: 200,
      data: { id: 1, username: 'fetched' },
    })
    const store = useAuthStore()
    await store.fetchUser()
    expect(store.user?.username).toBe('fetched')
    expect(mockAuthStorageSetUser).toHaveBeenCalled()
  })

  it('fetchUser 异常时静默吞掉 (由 401 拦截器处理)', async () => {
    mockAuthStorageGetToken.mockReturnValue('tok')
    setActivePinia(createPinia())
    mockGetCurrentUser.mockRejectedValueOnce(new Error('401'))
    const store = useAuthStore()
    await expect(store.fetchUser()).resolves.toBeUndefined()
  })
})
