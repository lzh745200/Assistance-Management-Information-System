import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDelete = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    put: (...args: any[]) => mockPut(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}))
vi.mock('@/api/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    put: (...args: any[]) => mockPut(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}))

import { villageApi } from '@/api/villages'
import { workLogApi } from '@/api/workLogs'

describe('api/villages', () => {
  beforeEach(() => vi.clearAllMocks())

  it('list GET /supported-villages', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await villageApi.list({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/supported-villages', { params: { page: 1 } })
  })

  it('getById GET /{id}', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 1 } })
    await villageApi.getById(1)
    expect(mockGet).toHaveBeenCalledWith('/supported-villages/1')
  })

  it('create POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1, name: 'V' } })
    await villageApi.create({ name: 'V', code: '001' } as any)
    expect(mockPost).toHaveBeenCalledWith('/supported-villages', { name: 'V', code: '001' })
  })

  it('update PUT', async () => {
    mockPut.mockResolvedValueOnce({ data: { message: 'ok' } })
    await villageApi.update(1, { name: 'V2' } as any)
    expect(mockPut).toHaveBeenCalledWith('/supported-villages/1', { name: 'V2' })
  })

  it('delete DELETE', async () => {
    mockDelete.mockResolvedValueOnce({ data: { message: 'ok' } })
    await villageApi.delete(1)
    expect(mockDelete).toHaveBeenCalledWith('/supported-villages/1')
  })

})


describe('api/workLogs', () => {
  beforeEach(() => vi.clearAllMocks())

  it('list GET /work-logs', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0, page: 1, page_size: 20 } })
    await workLogApi.list({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/work-logs', { params: { page: 1 } })
  })

  it('getById GET /{id}', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 1 } })
    await workLogApi.getById(1)
    expect(mockGet).toHaveBeenCalledWith('/work-logs/1')
  })

  it('create POST 优先 log_date', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await workLogApi.create({ log_date: '2026-06-01', title: 'L' } as any)
    expect(mockPost).toHaveBeenCalledWith('/work-logs', {
      log_date: '2026-06-01',
      title: 'L',
    })
  })

  it('create 兼容 work_date', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await workLogApi.create({ work_date: '2026-06-01', title: 'L' } as any)
    expect(mockPost).toHaveBeenCalledWith('/work-logs', {
      work_date: '2026-06-01',
      title: 'L',
      log_date: '2026-06-01',
    })
  })

  it('create 无日期默认 today', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await workLogApi.create({ title: 'L' } as any)
    const payload = mockPost.mock.calls[0][1]
    expect(payload.log_date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(payload.title).toBe('L')
  })

  it('update PUT /{id}', async () => {
    mockPut.mockResolvedValueOnce({ data: { id: 1 } })
    await workLogApi.update(1, { title: 'L2' } as any)
    expect(mockPut).toHaveBeenCalledWith('/work-logs/1', { title: 'L2' })
  })

  it('delete DELETE /{id}', async () => {
    mockDelete.mockResolvedValueOnce({ data: { success: true } })
    await workLogApi.delete(1)
    expect(mockDelete).toHaveBeenCalledWith('/work-logs/1')
  })

  it('getCalendarView GET /work-logs/calendar with year+month+source', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], year: 2026, month: 6 } })
    await workLogApi.getCalendarView(2026, 6, 'auto')
    expect(mockGet).toHaveBeenCalledWith('/work-logs/calendar', {
      params: { year: 2026, month: 6, source: 'auto' },
    })
  })

  it('getCalendarView 无 source', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], year: 2026, month: 6 } })
    await workLogApi.getCalendarView(2026, 6)
    expect(mockGet).toHaveBeenCalledWith('/work-logs/calendar', {
      params: { year: 2026, month: 6 },
    })
  })
})
