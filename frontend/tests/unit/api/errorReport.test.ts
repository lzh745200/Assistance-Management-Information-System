import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockPut } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
}))

// src/api/errorReport.ts 实际 import：import { get, post, put } from '@/api/request'
vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  put: mockPut,
}))

import {
  submitErrorReport,
  listErrorReports,
  getErrorStats,
  getErrorReport,
  updateErrorReport,
  reportException,
} from '@/api/errorReport'

describe('api/errorReport', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('submitErrorReport 调用 POST /system/error-reports 并透传载荷', async () => {
    const body = { success: true, message: 'ok', data: { report_id: 1 } }
    mockPost.mockResolvedValue(body)
    const data = { source: 'frontend', error_type: 'TypeError', message: 'boom', severity: 'error' }
    const result = await submitErrorReport(data)
    expect(mockPost).toHaveBeenCalledWith('/system/error-reports', data)
    expect(result).toBe(body)
  })

  it('listErrorReports 调用 GET /system/error-reports 并透传过滤参数', async () => {
    const body = { success: true, data: { items: [], total: 0 } }
    mockGet.mockResolvedValue(body)
    const params = { source: 'frontend', severity: 'critical', page: 1, page_size: 20 }
    const result = await listErrorReports(params)
    expect(mockGet).toHaveBeenCalledWith('/system/error-reports', params)
    expect(result).toBe(body)
  })

  it('getErrorStats 调用 GET /system/error-reports/stats', async () => {
    const body = { success: true, data: { total: 5, open: 2, critical: 1 } }
    mockGet.mockResolvedValue(body)
    const result = await getErrorStats()
    expect(mockGet).toHaveBeenCalledWith('/system/error-reports/stats')
    expect(result).toBe(body)
  })

  it('getErrorReport 调用 GET /system/error-reports/{id}', async () => {
    const body = { success: true, data: { id: 3 } }
    mockGet.mockResolvedValue(body)
    const result = await getErrorReport(3)
    expect(mockGet).toHaveBeenCalledWith('/system/error-reports/3')
    expect(result).toBe(body)
  })

  it('updateErrorReport 调用 PUT /system/error-reports/{id} 并透传状态', async () => {
    const body = { success: true, message: 'ok' }
    mockPut.mockResolvedValue(body)
    const data = { status: 'resolved', resolution_note: '已修复' }
    const result = await updateErrorReport(3, data)
    expect(mockPut).toHaveBeenCalledWith('/system/error-reports/3', data)
    expect(result).toBe(body)
  })

  it('reportException 对 source 与 message 做 encodeURIComponent 后拼进 POST URL', async () => {
    const body = { success: true, message: 'ok', data: { report_id: 9 } }
    mockPost.mockResolvedValue(body)
    const result = await reportException('前端 模块', '出错了!')
    expect(mockPost).toHaveBeenCalledWith(
      `/system/error-reports/report-exception?source=${encodeURIComponent('前端 模块')}&message=${encodeURIComponent('出错了!')}`
    )
    expect(result).toBe(body)
  })
})
