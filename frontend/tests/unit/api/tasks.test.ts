import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockDel } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDel: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  del: mockDel,
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))

import {
  listTasks,
  getTaskStats,
  getTask,
  createTask,
  cancelTask,
  deleteTask,
  getRunningTaskCount,
  tasksApi,
} from '@/api/tasks'

describe('api/tasks', () => {
  beforeEach(() => vi.clearAllMocks())

  it('listTasks 无参 GET /system/tasks', async () => {
    const body = { success: true, data: { items: [], total: 0 } }
    mockGet.mockResolvedValueOnce(body)
    const r = await listTasks()
    expect(mockGet).toHaveBeenCalledWith('/system/tasks', undefined)
    expect(r).toBe(body)
  })

  it('listTasks 带状态筛选与分页', async () => {
    mockGet.mockResolvedValueOnce({ success: true })
    await listTasks({ status: 'running', page: 2, page_size: 10 })
    expect(mockGet).toHaveBeenCalledWith('/system/tasks', {
      status: 'running',
      page: 2,
      page_size: 10,
    })
  })

  it('getTaskStats GET /system/tasks/stats', async () => {
    const body = { success: true, data: { total: 5 } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getTaskStats()
    expect(mockGet).toHaveBeenCalledWith('/system/tasks/stats')
    expect(r).toBe(body)
  })

  it('getTask GET /system/tasks/:id', async () => {
    const body = { success: true, data: { task_id: 't1' } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getTask('t1')
    expect(mockGet).toHaveBeenCalledWith('/system/tasks/t1')
    expect(r).toBe(body)
  })

  it('createTask POST /system/tasks', async () => {
    const body = { success: true, message: 'created', data: { task_id: 't2' } }
    mockPost.mockResolvedValueOnce(body)
    const data = { task_name: '数据同步', task_type: 'sync' }
    const r = await createTask(data)
    expect(mockPost).toHaveBeenCalledWith('/system/tasks', data)
    expect(r).toBe(body)
  })

  it('cancelTask POST /system/tasks/:id/cancel', async () => {
    const body = { success: true, message: 'cancelled' }
    mockPost.mockResolvedValueOnce(body)
    const r = await cancelTask('t1')
    expect(mockPost).toHaveBeenCalledWith('/system/tasks/t1/cancel')
    expect(r).toBe(body)
  })

  it('deleteTask DELETE /system/tasks/:id', async () => {
    const body = { success: true, message: 'deleted' }
    mockDel.mockResolvedValueOnce(body)
    const r = await deleteTask('t1')
    expect(mockDel).toHaveBeenCalledWith('/system/tasks/t1')
    expect(r).toBe(body)
  })

  it('getRunningTaskCount GET /system/tasks/running/count', async () => {
    const body = { success: true, data: { running: 1, pending: 0, total_active: 1 } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getRunningTaskCount()
    expect(mockGet).toHaveBeenCalledWith('/system/tasks/running/count')
    expect(r).toBe(body)
  })

  it('tasksApi 分组导出引用同一批函数', () => {
    expect(tasksApi.listTasks).toBe(listTasks)
    expect(tasksApi.getStats).toBe(getTaskStats)
    expect(tasksApi.getTask).toBe(getTask)
    expect(tasksApi.createTask).toBe(createTask)
    expect(tasksApi.cancelTask).toBe(cancelTask)
    expect(tasksApi.deleteTask).toBe(deleteTask)
    expect(tasksApi.getRunningCount).toBe(getRunningTaskCount)
  })
})
