import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockDel } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDel: vi.fn(),
}))

// src/api/updateLogs.ts 实际 import：import { get, post, del } from '@/api/request'
vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  del: mockDel,
}))

import {
  listUpdateLogs,
  getLatestUpdateLog,
  getUpdateLog,
  createUpdateLog,
  initializeVersionHistory,
  syncVersionHistory,
  deleteUpdateLog,
  checkVersionChange,
} from '@/api/updateLogs'

describe('api/updateLogs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('listUpdateLogs 调用 GET /system/update-logs 并透传分页参数', async () => {
    const body = { success: true, data: { items: [], total: 0 } }
    mockGet.mockResolvedValue(body)
    const params = { page: 1, page_size: 10, version: '1.0.0' }
    const result = await listUpdateLogs(params)
    expect(mockGet).toHaveBeenCalledWith('/system/update-logs', params)
    expect(result).toBe(body)
  })

  it('getLatestUpdateLog 调用 GET /system/update-logs/latest', async () => {
    const body = { success: true, data: { version: '1.2.0' } }
    mockGet.mockResolvedValue(body)
    const result = await getLatestUpdateLog()
    expect(mockGet).toHaveBeenCalledWith('/system/update-logs/latest')
    expect(result).toBe(body)
  })

  it('getUpdateLog 调用 GET /system/update-logs/{id}', async () => {
    const body = { success: true, data: { id: '5' } }
    mockGet.mockResolvedValue(body)
    const result = await getUpdateLog('5')
    expect(mockGet).toHaveBeenCalledWith('/system/update-logs/5')
    expect(result).toBe(body)
  })

  it('createUpdateLog 调用 POST /system/update-logs 并透传载荷', async () => {
    const body = { success: true, message: 'ok', data: { id: '6' } }
    mockPost.mockResolvedValue(body)
    const data = { version: '1.3.0', description: '新功能', updated_by: 'admin' }
    const result = await createUpdateLog(data)
    expect(mockPost).toHaveBeenCalledWith('/system/update-logs', data)
    expect(result).toBe(body)
  })

  it('initializeVersionHistory 带参数时透传', async () => {
    const body = { success: true, data: {} }
    mockPost.mockResolvedValue(body)
    const params = { updated_by: 'admin', force: true }
    const result = await initializeVersionHistory(params)
    expect(mockPost).toHaveBeenCalledWith('/system/update-logs/initialize', params)
    expect(result).toBe(body)
  })

  it('initializeVersionHistory 不带参数时发送空对象', async () => {
    mockPost.mockResolvedValue({ success: true })
    await initializeVersionHistory()
    expect(mockPost).toHaveBeenCalledWith('/system/update-logs/initialize', {})
  })

  it('syncVersionHistory 调用 POST /system/update-logs/sync 无载荷', async () => {
    const body = { success: true, message: 'ok' }
    mockPost.mockResolvedValue(body)
    const result = await syncVersionHistory()
    expect(mockPost).toHaveBeenCalledWith('/system/update-logs/sync')
    expect(result).toBe(body)
  })

  it('deleteUpdateLog 调用 DELETE /system/update-logs/{id}', async () => {
    mockDel.mockResolvedValue({ success: true })
    await deleteUpdateLog('5')
    expect(mockDel).toHaveBeenCalledWith('/system/update-logs/5')
  })

  it('checkVersionChange 调用 GET /system/update-logs/check/version', async () => {
    const body = { success: true, data: { current_version: '1.3.0' } }
    mockGet.mockResolvedValue(body)
    const result = await checkVersionChange()
    expect(mockGet).toHaveBeenCalledWith('/system/update-logs/check/version')
    expect(result).toBe(body)
  })
})
