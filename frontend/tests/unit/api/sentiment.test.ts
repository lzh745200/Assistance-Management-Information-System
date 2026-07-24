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
  collectNews,
  analyzeNews,
  getNews,
  getStatistics,
  getHotKeywords,
  getAlerts,
} from '@/api/sentiment'

describe('api/sentiment', () => {
  beforeEach(() => vi.clearAllMocks())

  it('collectNews POST /sentiment/collect', async () => {
    const body = { collected: 3 }
    mockPost.mockResolvedValueOnce(body)
    const data = { keywords: ['乡村振兴'] }
    const r = await collectNews(data)
    expect(mockPost).toHaveBeenCalledWith('/sentiment/collect', data)
    expect(r).toBe(body)
  })

  it('analyzeNews 默认 limit=100', async () => {
    const body = { analyzed: 100 }
    mockPost.mockResolvedValueOnce(body)
    const r = await analyzeNews()
    expect(mockPost).toHaveBeenCalledWith('/sentiment/analyze', null, {
      params: { limit: 100 },
    })
    expect(r).toBe(body)
  })

  it('analyzeNews 自定义 limit', async () => {
    mockPost.mockResolvedValueOnce({ analyzed: 50 })
    await analyzeNews(50)
    expect(mockPost).toHaveBeenCalledWith('/sentiment/analyze', null, {
      params: { limit: 50 },
    })
  })

  it('getNews GET /sentiment/news 带筛选参数', async () => {
    const body = { items: [] }
    mockGet.mockResolvedValueOnce(body)
    const params = { sentiment_label: 'negative', is_alert: true, days: 3 }
    const r = await getNews(params)
    expect(mockGet).toHaveBeenCalledWith('/sentiment/news', params)
    expect(r).toBe(body)
  })

  it('getNews 无参', async () => {
    mockGet.mockResolvedValueOnce({ items: [] })
    await getNews()
    expect(mockGet).toHaveBeenCalledWith('/sentiment/news', undefined)
  })

  it('getStatistics 默认 days=7', async () => {
    const body = { total: 10 }
    mockApiRequest.mockResolvedValueOnce(body)
    const r = await getStatistics()
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/sentiment/statistics',
      params: { days: 7 },
    })
    expect(r).toBe(body)
  })

  it('getStatistics 自定义 days', async () => {
    mockApiRequest.mockResolvedValueOnce({ total: 1 })
    await getStatistics(30)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/sentiment/statistics',
      params: { days: 30 },
    })
  })

  it('getHotKeywords 默认 days=7 top_k=20', async () => {
    const body = { keywords: [] }
    mockApiRequest.mockResolvedValueOnce(body)
    const r = await getHotKeywords()
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/sentiment/hot-keywords',
      params: { days: 7, top_k: 20 },
    })
    expect(r).toBe(body)
  })

  it('getHotKeywords 自定义参数', async () => {
    mockApiRequest.mockResolvedValueOnce({ keywords: [] })
    await getHotKeywords(14, 50)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/sentiment/hot-keywords',
      params: { days: 14, top_k: 50 },
    })
  })

  it('getAlerts 默认 days=7 limit=50', async () => {
    const body = { alerts: [] }
    mockApiRequest.mockResolvedValueOnce(body)
    const r = await getAlerts()
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/sentiment/alerts',
      params: { days: 7, limit: 50 },
    })
    expect(r).toBe(body)
  })

  it('getAlerts 自定义参数', async () => {
    mockApiRequest.mockResolvedValueOnce({ alerts: [] })
    await getAlerts(3, 10)
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/sentiment/alerts',
      params: { days: 3, limit: 10 },
    })
  })
})
