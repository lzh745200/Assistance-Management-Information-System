import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockPut, mockDel, mockApiRequest } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDel: vi.fn(),
  mockApiRequest: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  put: mockPut,
  del: mockDel,
  apiRequest: mockApiRequest,
}))

import {
  getDashboardStats,
  getDashboardSummary,
  getRecentActivities,
  createActivity,
  updateActivity,
  deleteActivity,
  getKpiTrends,
  getYearlyTrends,
} from '@/api/dashboard'

describe('api/dashboard', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getDashboardStats 默认 refresh=false', async () => {
    const body = { total_villages: 10 }
    mockApiRequest.mockResolvedValueOnce(body)
    const r = await getDashboardStats()
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/dashboard/stats',
      params: { refresh: false },
    })
    expect(r).toBe(body)
  })

  it('getDashboardStats refresh=true', async () => {
    mockApiRequest.mockResolvedValueOnce({ total_villages: 10 })
    await getDashboardStats(true)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/dashboard/stats',
      params: { refresh: true },
    })
  })

  it('getDashboardSummary GET /dashboard/summary', async () => {
    const body = { stats: {}, activities: [] }
    mockGet.mockResolvedValueOnce(body)
    const r = await getDashboardSummary()
    expect(mockGet).toHaveBeenCalledWith('/dashboard/summary')
    expect(r).toBe(body)
  })

  it('getRecentActivities GET /dashboard/recent-activities', async () => {
    const body = { items: [] }
    mockGet.mockResolvedValueOnce(body)
    const r = await getRecentActivities()
    expect(mockGet).toHaveBeenCalledWith('/dashboard/recent-activities')
    expect(r).toBe(body)
  })

  it('createActivity POST /dashboard/recent-activities', async () => {
    const body = { id: 'a1' }
    mockPost.mockResolvedValueOnce(body)
    const data = { action: '创建', target: '项目' }
    const r = await createActivity(data)
    expect(mockPost).toHaveBeenCalledWith('/dashboard/recent-activities', data)
    expect(r).toBe(body)
  })

  it('updateActivity PUT /dashboard/recent-activities/:id', async () => {
    const body = { id: 'a1' }
    mockPut.mockResolvedValueOnce(body)
    const data = { action: '更新' }
    const r = await updateActivity('a1', data)
    expect(mockPut).toHaveBeenCalledWith('/dashboard/recent-activities/a1', data)
    expect(r).toBe(body)
  })

  it('deleteActivity DELETE /dashboard/recent-activities/:id', async () => {
    const body = { deleted: true }
    mockDel.mockResolvedValueOnce(body)
    const r = await deleteActivity('a1')
    expect(mockDel).toHaveBeenCalledWith('/dashboard/recent-activities/a1')
    expect(r).toBe(body)
  })

  it('getKpiTrends GET /dashboard/kpi-trends', async () => {
    const body = { trends: [] }
    mockGet.mockResolvedValueOnce(body)
    const r = await getKpiTrends()
    expect(mockGet).toHaveBeenCalledWith('/dashboard/kpi-trends')
    expect(r).toBe(body)
  })

  it('getYearlyTrends 默认 years=5', async () => {
    const body = { years: [] }
    mockGet.mockResolvedValueOnce(body)
    const r = await getYearlyTrends()
    expect(mockGet).toHaveBeenCalledWith('/dashboard/yearly-trends', { years: 5 })
    expect(r).toBe(body)
  })

  it('getYearlyTrends 自定义 years', async () => {
    mockGet.mockResolvedValueOnce({ years: [] })
    await getYearlyTrends(3)
    expect(mockGet).toHaveBeenCalledWith('/dashboard/yearly-trends', { years: 3 })
  })
})
