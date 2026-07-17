import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockDelete } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDelete: vi.fn(),
}))

// src/api/audit.ts 使用命名导出 `import { get, post, del } from '@/api/request'`
vi.mock('@/api/request', () => ({
  get: (...args: any[]) => mockGet(...args),
  post: (...args: any[]) => mockPost(...args),
  del: (...args: any[]) => mockDelete(...args),
}))

import { auditApi } from '@/api/audit'

describe('api/audit', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getLogs GET /system/audit/logs with params', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await auditApi.getLogs({ action: 'login', page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/system/audit/logs', { action: 'login', page: 1 })
  })

  it('getLogs 无参', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await auditApi.getLogs()
    expect(mockGet).toHaveBeenCalledWith('/system/audit/logs', undefined)
  })

  it('getStats GET /system/audit/stats', async () => {
    mockGet.mockResolvedValueOnce({ data: { today_operations: 10 } })
    await auditApi.getStats({ start_date: '2026-01-01' })
    expect(mockGet).toHaveBeenCalledWith('/system/audit/stats', { start_date: '2026-01-01' })
  })

  it('getLoginAttempts GET /system/audit/login-attempts', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await auditApi.getLoginAttempts({ username: 'admin' })
    expect(mockGet).toHaveBeenCalledWith('/system/audit/login-attempts', { username: 'admin' })
  })

  it('getSecurityEvents GET /system/audit/security/events', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await auditApi.getSecurityEvents({ severity: 'high', resolved: false })
    expect(mockGet).toHaveBeenCalledWith('/system/audit/security/events', { severity: 'high', resolved: false })
  })

  it('getSecurityStats GET /system/audit/security/stats', async () => {
    mockGet.mockResolvedValueOnce({ data: { high: 0, medium: 0 } })
    await auditApi.getSecurityStats()
    expect(mockGet).toHaveBeenCalledWith('/system/audit/security/stats')
  })

  it('resolveSecurityEvent POST 含 resolution_notes 查询参数', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await auditApi.resolveSecurityEvent(7, 'fixed by patch')
    expect(mockPost).toHaveBeenCalledWith(
      '/system/audit/security/events/7/resolve',
      null,
      { params: { resolution_notes: 'fixed by patch' } },
    )
  })

  it('deleteLog DELETE /system/audit/logs/{id}', async () => {
    mockDelete.mockResolvedValueOnce({ data: { success: true } })
    await auditApi.deleteLog(99)
    expect(mockDelete).toHaveBeenCalledWith('/system/audit/logs/99')
  })
})
