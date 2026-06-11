import { describe, it, expect, vi } from 'vitest'

const { mockPost, mockPut, mockDelete, mockPatch } = vi.hoisted(() => ({
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDelete: vi.fn(),
  mockPatch: vi.fn(),
}))
vi.mock('@/api/request', () => ({
  default: { post: mockPost, put: mockPut, delete: mockDelete, patch: mockPatch },
}))

import { createUser, updateUser, deleteUser, resetPassword, updateUserStatus } from '@/api/mutations/user'

describe('api/mutations/user', () => {
  it('createUser posts to /users', async () => {
    mockPost.mockResolvedValue({ data: { id: '1' } })
    const r = await createUser({ name: 'test' })
    expect(mockPost).toHaveBeenCalledWith('/users', { name: 'test' })
    expect(r).toEqual({ id: '1' })
  })

  it('updateUser puts to /users/:id', async () => {
    mockPut.mockResolvedValue({ data: { id: '1' } })
    const r = await updateUser('1', { name: 'new' })
    expect(mockPut).toHaveBeenCalledWith('/users/1', { name: 'new' })
    expect(r).toEqual({ id: '1' })
  })

  it('deleteUser deletes /users/:id', async () => {
    mockDelete.mockResolvedValue({ data: { success: true } })
    const r = await deleteUser('99')
    expect(mockDelete).toHaveBeenCalledWith('/users/99')
    expect(r).toEqual({ success: true })
  })

  it('resetPassword posts to /users/:id/reset-password', async () => {
    mockPost.mockResolvedValue({ data: { success: true } })
    const r = await resetPassword('2')
    expect(mockPost).toHaveBeenCalledWith('/users/2/reset-password')
    expect(r).toEqual({ success: true })
  })

  it('updateUserStatus patches /users/:id/status', async () => {
    mockPatch.mockResolvedValue({ data: { id: '1', status: 'active' } })
    const r = await updateUserStatus('1', 'active')
    expect(mockPatch).toHaveBeenCalledWith('/users/1/status', { status: 'active' })
    expect(r).toEqual({ id: '1', status: 'active' })
  })
})
