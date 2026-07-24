import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockPost, mockApiRequest } = vi.hoisted(() => ({
  mockPost: vi.fn(),
  mockApiRequest: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  post: mockPost,
  apiRequest: mockApiRequest,
}))

import {
  evaluateVillage,
  getEvaluationReport,
  compareEvaluations,
  getRankings,
} from '@/api/effectiveness'

describe('api/effectiveness', () => {
  beforeEach(() => vi.clearAllMocks())

  it('evaluateVillage POST /effectiveness/evaluate', async () => {
    const body = { score: 88 }
    mockPost.mockResolvedValueOnce(body)
    const data = { village_id: 1, year: 2025 }
    const r = await evaluateVillage(data)
    expect(mockPost).toHaveBeenCalledWith('/effectiveness/evaluate', data)
    expect(r).toBe(body)
  })

  it('getEvaluationReport GET /effectiveness/report/:villageId', async () => {
    const body = { report: {} }
    mockApiRequest.mockResolvedValueOnce(body)
    const r = await getEvaluationReport(1, 2025)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/effectiveness/report/1',
      params: { year: 2025 },
    })
    expect(r).toBe(body)
  })

  it('compareEvaluations GET /effectiveness/compare/:villageId', async () => {
    const body = { diff: {} }
    mockApiRequest.mockResolvedValueOnce(body)
    const r = await compareEvaluations(1, 2024, 2025)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/effectiveness/compare/1',
      params: { year1: 2024, year2: 2025 },
    })
    expect(r).toBe(body)
  })

  it('getRankings 默认 limit=20', async () => {
    const body = { items: [] }
    mockApiRequest.mockResolvedValueOnce(body)
    const r = await getRankings(2025)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/effectiveness/rankings',
      params: { year: 2025, limit: 20 },
    })
    expect(r).toBe(body)
  })

  it('getRankings 自定义 limit', async () => {
    mockApiRequest.mockResolvedValueOnce({ items: [] })
    await getRankings(2025, 10)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/effectiveness/rankings',
      params: { year: 2025, limit: 10 },
    })
  })
})
