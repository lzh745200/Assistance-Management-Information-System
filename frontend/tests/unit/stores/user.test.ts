import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDel = vi.fn()

vi.mock('@/api/request', () => ({
  get: (...args: any[]) => mockGet(...args),
  post: (...args: any[]) => mockPost(...args),
  put: (...args: any[]) => mockPut(...args),
  del: (...args: any[]) => mockDel(...args),
}))

vi.mock('@/utils/authStorage', () => ({
  AuthStorage: {
    clear: vi.fn(),
    setAuthData: vi.fn(),
    getToken: vi.fn(() => ''),
    getUser: vi.fn(() => null),
  },
}))

import { useUserStore } from '@/stores/user'

describe('useUserStore', () => {
  let store: ReturnType<typeof useUserStore>
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    store = useUserStore()
  })

  it('初始状态: userList=[], currentUser=null, total=0', () => {
    expect(store.userList).toEqual([])
    expect(store.currentUser).toBeNull()
    expect(store.total).toBe(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchUsers 成功时填充 userList 和 total', async () => {
    mockGet.mockResolvedValueOnce({
      code: 200,
      data: {
        items: [
          { id: 1, username: 'alice' },
          { id: 2, username: 'bob' },
        ],
        total: 2,
      },
    })
    await store.fetchUsers({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/users', { page: 1 })
    expect(store.userList).toHaveLength(2)
    expect(store.total).toBe(2)
  })

  it('fetchUsers 失败时设置 error', async () => {
    mockGet.mockRejectedValueOnce(new Error('network'))
    await store.fetchUsers()
    expect(store.error).toBe('network')
  })

  it('fetchUser 成功时设置 currentUser 并返回', async () => {
    const user = { id: 1, username: 'alice' }
    mockGet.mockResolvedValueOnce({ code: 200, data: user })
    const result = await store.fetchUser(1)
    expect(result).toEqual(user)
    expect(store.currentUser).toEqual(user)
  })

  it('createUser 成功时插入 userList 头部', async () => {
    const newUser = { id: 99, username: 'charlie' }
    mockPost.mockResolvedValueOnce({ code: 200, data: newUser })
    const res = await store.createUser({ username: 'charlie' })
    expect(res.code).toBe(200)
    expect(store.userList[0]).toEqual(newUser)
    expect(store.total).toBe(1)
  })

  it('updateUser 成功时更新 userList 中对应条目', async () => {
    store.userList = [{ id: 1, username: 'alice' }]
    store.total = 1
    const updated = { id: 1, username: 'alice2' }
    mockPut.mockResolvedValueOnce({ code: 200, data: updated })
    await store.updateUser(1, { username: 'alice2' })
    expect(store.userList[0]).toEqual(updated)
  })

  it('updateUser 同时更新 currentUser 如果 ID 匹配', async () => {
    store.currentUser = { id: 1, username: 'alice' }
    const updated = { id: 1, username: 'alice2' }
    mockPut.mockResolvedValueOnce({ code: 200, data: updated })
    await store.updateUser(1, { username: 'alice2' })
    expect(store.currentUser).toEqual(updated)
  })

  it('deleteUser 成功时移除 userList 中条目', async () => {
    store.userList = [{ id: 1, username: 'a' }, { id: 2, username: 'b' }]
    store.total = 2
    mockDel.mockResolvedValueOnce({ code: 200 })
    await store.deleteUser(1)
    expect(store.userList).toHaveLength(1)
    expect(store.userList[0].id).toBe(2)
    expect(store.total).toBe(1)
  })

  it('deleteUser 清除 currentUser 如果 ID 匹配', async () => {
    store.currentUser = { id: 1, username: 'a' }
    store.userList = [{ id: 1, username: 'a' }]
    store.total = 1
    mockDel.mockResolvedValueOnce({ code: 200 })
    await store.deleteUser(1)
    expect(store.currentUser).toBeNull()
  })

  it('resetUserPassword 调用 POST /users/{id}/admin-reset-password', async () => {
    mockPost.mockResolvedValueOnce({ code: 200 })
    await store.resetUserPassword(5, 'newpass')
    expect(mockPost).toHaveBeenCalledWith(
      '/users/5/admin-reset-password',
      { new_password: 'newpass' },
    )
  })

  it('assignRole 调用 POST /user-management/{id}/assign-role', async () => {
    mockPost.mockResolvedValueOnce({ code: 200 })
    await store.assignRole(5, 3)
    expect(mockPost).toHaveBeenCalledWith(
      '/user-management/5/assign-role',
      { role_id: 3 },
    )
  })

  it('logout 清空 AuthStorage', async () => {
    await store.logout()
    const { AuthStorage } = await import('@/utils/authStorage')
    expect(AuthStorage.clear).toHaveBeenCalled()
  })

  it('getUserProfile 无 userId 且无 currentUser 时抛错', async () => {
    await expect(store.getUserProfile()).rejects.toThrow('No user ID available')
  })

  it('getUserProfile 使用 currentUser.id 当未传参', async () => {
    store.currentUser = { id: 7, username: 'me' }
    const profile = { id: 7, username: 'me' }
    mockGet.mockResolvedValueOnce({ code: 200, data: profile })
    const result = await store.getUserProfile()
    expect(result).toEqual(profile)
    expect(mockGet).toHaveBeenCalledWith('/users/7')
  })

  it('updateUserProfile 委托给 updateUser', async () => {
    store.userList = [{ id: 1, username: 'a' }]
    const updated = { id: 1, username: 'b' }
    mockPut.mockResolvedValueOnce({ code: 200, data: updated })
    await store.updateUserProfile(1, { username: 'b' })
    expect(mockPut).toHaveBeenCalledWith('/users/1', { username: 'b' })
  })

  it('uploadAvatar 返回占位 url', async () => {
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const result = await store.uploadAvatar(1, new File([], 'a.png'))
    expect(result).toEqual({ url: '' })
    expect(consoleWarn).toHaveBeenCalled()
    consoleWarn.mockRestore()
  })
})
