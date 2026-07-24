import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockApiRequest } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockApiRequest: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  apiRequest: mockApiRequest,
}))

import {
  getStatus,
  analyze,
  getRecommendations,
  forecastIncome,
  forecastFunds,
  predictTrend,
  detectAnomalies,
  recommendProjects,
  recommendFundAllocation,
  nlpQuery,
} from '@/api/ai'

describe('api/ai', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getStatus GET /ai/status', async () => {
    const body = { status: 'ok' }
    mockGet.mockResolvedValueOnce(body)
    const r = await getStatus()
    expect(mockGet).toHaveBeenCalledWith('/ai/status')
    expect(r).toBe(body)
  })

  it('analyze POST /ai/analyze', async () => {
    const body = { result: 'done' }
    mockPost.mockResolvedValueOnce(body)
    const data = { analysis_type: 'trend', data: { year: 2026 } }
    const r = await analyze(data)
    expect(mockPost).toHaveBeenCalledWith('/ai/analyze', data)
    expect(r).toBe(body)
  })

  it('getRecommendations POST /ai/recommendations', async () => {
    const body = { items: [] }
    mockPost.mockResolvedValueOnce(body)
    const data = { context: { village_id: 1 }, category: 'project' }
    const r = await getRecommendations(data)
    expect(mockPost).toHaveBeenCalledWith('/ai/recommendations', data)
    expect(r).toBe(body)
  })

  it('forecastIncome 默认 forecast_years=2', async () => {
    const body = { forecast: [] }
    mockApiRequest.mockResolvedValueOnce(body)
    const r = await forecastIncome()
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/ai/forecast/income',
      params: { forecast_years: 2 },
    })
    expect(r).toBe(body)
  })

  it('forecastIncome 自定义年数', async () => {
    mockApiRequest.mockResolvedValueOnce({ forecast: [] })
    await forecastIncome(5)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/ai/forecast/income',
      params: { forecast_years: 5 },
    })
  })

  it('forecastFunds GET /ai/forecast/funds', async () => {
    const body = { completion_rate: 0.9 }
    mockGet.mockResolvedValueOnce(body)
    const r = await forecastFunds()
    expect(mockGet).toHaveBeenCalledWith('/ai/forecast/funds')
    expect(r).toBe(body)
  })

  it('predictTrend POST /ai-enhanced/predict', async () => {
    const body = { trend: [] }
    mockPost.mockResolvedValueOnce(body)
    const data = { historical_data: [{ year: 2025, value: 100 }], periods: 3 }
    const r = await predictTrend(data)
    expect(mockPost).toHaveBeenCalledWith('/ai-enhanced/predict', data)
    expect(r).toBe(body)
  })

  it('detectAnomalies POST /ai-enhanced/anomaly-detection', async () => {
    const body = { anomalies: [] }
    mockPost.mockResolvedValueOnce(body)
    const data = { data: [{ value: 1 }], value_field: 'value' }
    const r = await detectAnomalies(data)
    expect(mockPost).toHaveBeenCalledWith('/ai-enhanced/anomaly-detection', data)
    expect(r).toBe(body)
  })

  it('recommendProjects 默认 limit=5', async () => {
    const body = { projects: [] }
    mockApiRequest.mockResolvedValueOnce(body)
    const r = await recommendProjects(3)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/ai-enhanced/recommendations/projects',
      params: { village_id: 3, limit: 5 },
    })
    expect(r).toBe(body)
  })

  it('recommendProjects 自定义 limit', async () => {
    mockApiRequest.mockResolvedValueOnce({ projects: [] })
    await recommendProjects(3, 10)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/ai-enhanced/recommendations/projects',
      params: { village_id: 3, limit: 10 },
    })
  })

  it('recommendFundAllocation POST /ai-enhanced/recommendations/fund-allocation', async () => {
    const body = { allocation: [] }
    mockPost.mockResolvedValueOnce(body)
    const data = { total_budget: 100000, village_ids: [1, 2] }
    const r = await recommendFundAllocation(data)
    expect(mockPost).toHaveBeenCalledWith('/ai-enhanced/recommendations/fund-allocation', data)
    expect(r).toBe(body)
  })

  it('nlpQuery POST /ai-enhanced/nlp-query 带 query 参数', async () => {
    const body = { answer: 'ok' }
    mockPost.mockResolvedValueOnce(body)
    const r = await nlpQuery('今年收入多少')
    expect(mockPost).toHaveBeenCalledWith('/ai-enhanced/nlp-query', null, {
      params: { query: '今年收入多少' },
    })
    expect(r).toBe(body)
  })
})
