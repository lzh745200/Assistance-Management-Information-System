import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
}))

import {
  batchUpdate,
  batchDelete,
  batchExport,
  validateBatch,
  getBatchStatus,
} from '@/api/batchOperations'

describe('api/batchOperations', () => {
  beforeEach(() => vi.clearAllMocks())

  it('batchUpdate POST /batch/update', async () => {
    const body = { updated: 2 }
    mockPost.mockResolvedValueOnce(body)
    const data = { table_name: 'villages', ids: [1, 2], updates: { status: 'active' } }
    const r = await batchUpdate(data)
    expect(mockPost).toHaveBeenCalledWith('/batch/update', data)
    expect(r).toBe(body)
  })

  it('batchDelete POST /batch/delete', async () => {
    const body = { deleted: 2 }
    mockPost.mockResolvedValueOnce(body)
    const data = { table_name: 'villages', ids: [1, 2], soft_delete: true }
    const r = await batchDelete(data)
    expect(mockPost).toHaveBeenCalledWith('/batch/delete', data)
    expect(r).toBe(body)
  })

  it('batchExport POST /batch/export', async () => {
    const body = { file_url: '/files/x.xlsx' }
    mockPost.mockResolvedValueOnce(body)
    const data = { table_name: 'villages', ids: [1], format: 'xlsx' }
    const r = await batchExport(data)
    expect(mockPost).toHaveBeenCalledWith('/batch/export', data)
    expect(r).toBe(body)
  })

  it('validateBatch POST /batch/validate 带 query 参数', async () => {
    const body = { valid: true }
    mockPost.mockResolvedValueOnce(body)
    const r = await validateBatch('villages', [1, 2])
    expect(mockPost).toHaveBeenCalledWith('/batch/validate', null, {
      params: { table_name: 'villages', ids: [1, 2] },
    })
    expect(r).toBe(body)
  })

  it('getBatchStatus GET /batch/status', async () => {
    const body = { running: 0 }
    mockGet.mockResolvedValueOnce(body)
    const r = await getBatchStatus()
    expect(mockGet).toHaveBeenCalledWith('/batch/status')
    expect(r).toBe(body)
  })
})
