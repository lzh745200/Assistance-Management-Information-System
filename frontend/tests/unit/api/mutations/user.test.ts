import { describe, it, expect, vi } from 'vitest'

const { mockPost, mockPut, mockDel } = vi.hoisted(() => ({
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDel: vi.fn(),
}))
vi.mock('@/api/request', () => ({
  post: mockPost,
  put: mockPut,
  del: mockDel,
}))

import { createUser, updateUser, deleteUser, resetPassword } from '@/api/mutations/user'

describe('api/mutations/user', () => {
  it('createUser posts to /users', async () => {
    mockPost.mockResolvedValue({ id: '1' })
    const r = await createUser({ name: 'test' })
    expect(mockPost).toHaveBeenCalledWith('/users', { name: 'test' })
    expect(r).toEqual({ id: '1' })
  })

  it('updateUser puts to /users/:id', async () => {
    mockPut.mockResolvedValue({ id: '1' })
    const r = await updateUser('1', { name: 'new' })
    expect(mockPut).toHaveBeenCalledWith('/users/1', { name: 'new' })
    expect(r).toEqual({ id: '1' })
  })

  it('deleteUser deletes /users/:id', async () => {
    mockDel.mockResolvedValue({ success: true })
    const r = await deleteUser('99')
    expect(mockDel).toHaveBeenCalledWith('/users/99')
    expect(r).toEqual({ success: true })
  })

  it('resetPassword posts to /users/:id/admin-reset-password', async () => {
    mockPost.mockResolvedValue({ success: true })
    const r = await resetPassword('2')
    expect(mockPost).toHaveBeenCalledWith('/users/2/admin-reset-password', { new_password: undefined })
    expect(r).toEqual({ success: true })
  })

})
