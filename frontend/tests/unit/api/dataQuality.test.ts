import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
}))

import { validate, clean, deduplicate, getReport, runFullCheck } from '@/api/dataQuality'

describe('api/dataQuality', () => {
  beforeEach(() => vi.clearAllMocks())

  it('validate POST /data-quality/validate', async () => {
    const body = { valid: true }
    mockPost.mockResolvedValueOnce(body)
    const data = { entity_type: 'village', data: { name: '幸福村' } }
    const r = await validate(data)
    expect(mockPost).toHaveBeenCalledWith('/data-quality/validate', data)
    expect(r).toBe(body)
  })

  it('clean POST /data-quality/clean', async () => {
    const body = { cleaned: 2 }
    mockPost.mockResolvedValueOnce(body)
    const data = { records: [{ name: ' A ' }], cleaning_rules: { trim: true } }
    const r = await clean(data)
    expect(mockPost).toHaveBeenCalledWith('/data-quality/clean', data)
    expect(r).toBe(body)
  })

  it('deduplicate 默认 similarity_threshold=0.9', async () => {
    const body = { duplicates: 1 }
    mockPost.mockResolvedValueOnce(body)
    const records = [{ id: 1 }, { id: 1 }]
    const r = await deduplicate(records, ['id'])
    expect(mockPost).toHaveBeenCalledWith('/data-quality/deduplicate', records, {
      params: { key_fields: ['id'], similarity_threshold: 0.9 },
    })
    expect(r).toBe(body)
  })

  it('deduplicate 自定义 similarity_threshold', async () => {
    mockPost.mockResolvedValueOnce({ duplicates: 0 })
    await deduplicate([{ id: 1 }], ['id', 'name'], 0.8)
    expect(mockPost).toHaveBeenCalledWith('/data-quality/deduplicate', [{ id: 1 }], {
      params: { key_fields: ['id', 'name'], similarity_threshold: 0.8 },
    })
  })

  it('getReport GET /data-quality/report', async () => {
    const body = { score: 95 }
    mockGet.mockResolvedValueOnce(body)
    const r = await getReport()
    expect(mockGet).toHaveBeenCalledWith('/data-quality/report')
    expect(r).toBe(body)
  })

  it('runFullCheck POST /data-quality/full-check', async () => {
    const body = { issues: 0 }
    mockPost.mockResolvedValueOnce(body)
    const r = await runFullCheck()
    expect(mockPost).toHaveBeenCalledWith('/data-quality/full-check')
    expect(r).toBe(body)
  })
})
