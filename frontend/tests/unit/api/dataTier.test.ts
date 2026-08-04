import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockDel } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDel: vi.fn(),
}))

// src/api/dataTier.ts 实际 import：import { get, post, del } from '@/api/request'
vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  del: mockDel,
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))

import {
  getStorageStats,
  getStorageSummary,
  getTierInfo,
  archiveModel,
  listArchives,
  restoreFromArchive,
  cleanupArchives,
  getTierForRecord,
} from '@/api/dataTier'

describe('api/dataTier', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getStorageStats 调用 GET /data-tier/stats 并透传返回值', async () => {
    const body = { hot: 10 }
    mockGet.mockResolvedValue(body)
    const result = await getStorageStats()
    expect(mockGet).toHaveBeenCalledWith('/data-tier/stats')
    expect(result).toBe(body)
  })

  it('getStorageSummary 调用 GET /data-tier/summary', async () => {
    const body = { summary: true }
    mockGet.mockResolvedValue(body)
    const result = await getStorageSummary()
    expect(mockGet).toHaveBeenCalledWith('/data-tier/summary')
    expect(result).toBe(body)
  })

  it('getTierInfo 调用 GET /data-tier/tier/{tier}', async () => {
    const body = { tier: 'warm' }
    mockGet.mockResolvedValue(body)
    const result = await getTierInfo('warm')
    expect(mockGet).toHaveBeenCalledWith('/data-tier/tier/warm')
    expect(result).toBe(body)
  })

  it('archiveModel 默认 before_days=365、batch_size=1000', async () => {
    mockPost.mockResolvedValue({ archived_count: 0 })
    await archiveModel('records')
    expect(mockPost).toHaveBeenCalledWith(
      '/data-tier/archive/records?before_days=365&batch_size=1000'
    )
  })

  it('archiveModel 自定义参数拼进 URL', async () => {
    const body = { archived_count: 5, model: 'records' }
    mockPost.mockResolvedValue(body)
    const result = await archiveModel('records', 30, 500)
    expect(mockPost).toHaveBeenCalledWith(
      '/data-tier/archive/records?before_days=30&batch_size=500'
    )
    expect(result).toBe(body)
  })

  it('listArchives 带 tier 时透传参数', async () => {
    const body = { cold_archives: [], warm_archives: [] }
    mockGet.mockResolvedValue(body)
    const result = await listArchives('cold')
    expect(mockGet).toHaveBeenCalledWith('/data-tier/archives', { tier: 'cold' })
    expect(result).toBe(body)
  })

  it('listArchives 不带 tier 时参数为 undefined', async () => {
    mockGet.mockResolvedValue({})
    await listArchives()
    expect(mockGet).toHaveBeenCalledWith('/data-tier/archives', undefined)
  })

  it('restoreFromArchive 对参数做 encodeURIComponent 后拼进 POST URL', async () => {
    const body = { restored_count: 3 }
    mockPost.mockResolvedValue(body)
    const result = await restoreFromArchive('归档 2024.tar.gz', 'records')
    expect(mockPost).toHaveBeenCalledWith(
      `/data-tier/restore?archive_file=${encodeURIComponent('归档 2024.tar.gz')}&model_name=${encodeURIComponent('records')}`
    )
    expect(result).toBe(body)
  })

  it('cleanupArchives 默认 max_age_days=365', async () => {
    mockDel.mockResolvedValue({ deleted_count: 0 })
    await cleanupArchives()
    expect(mockDel).toHaveBeenCalledWith('/data-tier/cleanup?max_age_days=365')
  })

  it('cleanupArchives 自定义 max_age_days', async () => {
    const body = { deleted_count: 2 }
    mockDel.mockResolvedValue(body)
    const result = await cleanupArchives(90)
    expect(mockDel).toHaveBeenCalledWith('/data-tier/cleanup?max_age_days=90')
    expect(result).toBe(body)
  })

  it('getTierForRecord 对日期做 encodeURIComponent 后调用 GET', async () => {
    const body = { record_date: '2024-01-01', tier: 'hot', age_days: 1 }
    mockGet.mockResolvedValue(body)
    const result = await getTierForRecord('2024-01-01')
    expect(mockGet).toHaveBeenCalledWith(
      `/data-tier/tier-for-record/${encodeURIComponent('2024-01-01')}`
    )
    expect(result).toBe(body)
  })
})
