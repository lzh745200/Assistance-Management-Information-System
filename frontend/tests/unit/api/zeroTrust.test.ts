import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))

// src/api/zeroTrust.ts 实际 import：import { get, post } from '@/api/request'
vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))

import {
  getTrustAssessment,
  listSecurityPolicies,
  getSecurityPolicy,
  evaluateAccessRequest,
  listSecurityEvents,
  reportSecurityEvent,
  getSecurityEventStats,
} from '@/api/zeroTrust'

describe('api/zeroTrust', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getTrustAssessment 调用 GET /system/zero-trust/assessment', async () => {
    const body = { success: true, data: { level: 'high', score: 90 } }
    mockGet.mockResolvedValue(body)
    const result = await getTrustAssessment()
    expect(mockGet).toHaveBeenCalledWith('/system/zero-trust/assessment')
    expect(result).toBe(body)
  })

  it('listSecurityPolicies 调用 GET /system/zero-trust/policies 并透传过滤参数', async () => {
    const body = { success: true, data: { policies: [], total: 0, enabled_count: 0 } }
    mockGet.mockResolvedValue(body)
    const params = { category: 'network', enabled_only: true }
    const result = await listSecurityPolicies(params)
    expect(mockGet).toHaveBeenCalledWith('/system/zero-trust/policies', params)
    expect(result).toBe(body)
  })

  it('getSecurityPolicy 调用 GET /system/zero-trust/policies/{policyId}', async () => {
    const body = { success: true, data: { id: 'p1' } }
    mockGet.mockResolvedValue(body)
    const result = await getSecurityPolicy('p1')
    expect(mockGet).toHaveBeenCalledWith('/system/zero-trust/policies/p1')
    expect(result).toBe(body)
  })

  it('evaluateAccessRequest 调用 POST /system/zero-trust/evaluate 并透传载荷', async () => {
    const body = { success: true, data: { result: 'allowed' } }
    mockPost.mockResolvedValue(body)
    const data = { resource: '/api/data', action: 'read', context: { ip: '127.0.0.1' } }
    const result = await evaluateAccessRequest(data)
    expect(mockPost).toHaveBeenCalledWith('/system/zero-trust/evaluate', data)
    expect(result).toBe(body)
  })

  it('listSecurityEvents 调用 GET /system/zero-trust/events 并透传分页参数', async () => {
    const body = { success: true, data: { items: [], total: 0 } }
    mockGet.mockResolvedValue(body)
    const params = { severity: 'high', page: 1, page_size: 20 }
    const result = await listSecurityEvents(params)
    expect(mockGet).toHaveBeenCalledWith('/system/zero-trust/events', params)
    expect(result).toBe(body)
  })

  it('reportSecurityEvent 调用 POST /system/zero-trust/events 并透传载荷', async () => {
    const body = { success: true, message: 'ok', data: { event_id: 1 } }
    mockPost.mockResolvedValue(body)
    const data = {
      event_type: 'login_failed',
      source: 'auth',
      message: '多次登录失败',
      severity: 'high',
    }
    const result = await reportSecurityEvent(data)
    expect(mockPost).toHaveBeenCalledWith('/system/zero-trust/events', data)
    expect(result).toBe(body)
  })

  it('getSecurityEventStats 调用 GET /system/zero-trust/events/stats', async () => {
    const body = {
      success: true,
      data: { total_events: 4, high_severity_count: 1, security_posture: 'normal' },
    }
    mockGet.mockResolvedValue(body)
    const result = await getSecurityEventStats()
    expect(mockGet).toHaveBeenCalledWith('/system/zero-trust/events/stats')
    expect(result).toBe(body)
  })
})
