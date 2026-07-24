import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockPut, mockDel, mockPatch } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDel: vi.fn(),
  mockPatch: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  put: mockPut,
  del: mockDel,
  patch: mockPatch,
}))

import { listTodos, getTodo, createTodo, updateTodo, deleteTodo, toggleTodo } from '@/api/todos'

describe('api/todos', () => {
  beforeEach(() => vi.clearAllMocks())

  it('listTodos 无参 GET /todos', async () => {
    const body = { items: [] }
    mockGet.mockResolvedValueOnce(body)
    const r = await listTodos()
    expect(mockGet).toHaveBeenCalledWith('/todos', undefined)
    expect(r).toBe(body)
  })

  it('listTodos 带筛选参数', async () => {
    mockGet.mockResolvedValueOnce({ items: [] })
    await listTodos({ completed: false, priority: 'high', page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/todos', {
      completed: false,
      priority: 'high',
      page: 1,
    })
  })

  it('getTodo GET /todos/:id', async () => {
    const body = { id: 1, title: '写报告' }
    mockGet.mockResolvedValueOnce(body)
    const r = await getTodo(1)
    expect(mockGet).toHaveBeenCalledWith('/todos/1')
    expect(r).toBe(body)
  })

  it('createTodo POST /todos', async () => {
    const body = { id: 2 }
    mockPost.mockResolvedValueOnce(body)
    const data = { title: '新待办', priority: 'high' }
    const r = await createTodo(data)
    expect(mockPost).toHaveBeenCalledWith('/todos', data)
    expect(r).toBe(body)
  })

  it('updateTodo PUT /todos/:id', async () => {
    const body = { id: 1, completed: true }
    mockPut.mockResolvedValueOnce(body)
    const data = { completed: true }
    const r = await updateTodo(1, data)
    expect(mockPut).toHaveBeenCalledWith('/todos/1', data)
    expect(r).toBe(body)
  })

  it('deleteTodo DELETE /todos/:id', async () => {
    const body = { deleted: true }
    mockDel.mockResolvedValueOnce(body)
    const r = await deleteTodo(1)
    expect(mockDel).toHaveBeenCalledWith('/todos/1')
    expect(r).toBe(body)
  })

  it('toggleTodo PATCH /todos/:id/toggle', async () => {
    const body = { id: 1, completed: true }
    mockPatch.mockResolvedValueOnce(body)
    const r = await toggleTodo(1)
    expect(mockPatch).toHaveBeenCalledWith('/todos/1/toggle')
    expect(r).toBe(body)
  })
})
