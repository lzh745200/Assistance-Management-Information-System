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

import { reportApi } from '@/api/report'

describe('api/report', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('subscriptions', () => {
    it('list 调用 GET /reports/subscriptions', async () => {
      mockGet.mockResolvedValue({ data: { items: [], total: 0 } })
      await reportApi.list({ page: 1 })
      expect(mockGet).toHaveBeenCalledWith('/reports/subscriptions', { params: { page: 1 } })
    })

    it('list 无参时调用', async () => {
      mockGet.mockResolvedValue({ data: { items: [], total: 0 } })
      await reportApi.list()
      expect(mockGet).toHaveBeenCalledWith('/reports/subscriptions', { params: undefined })
    })

    it('getById 调用 GET /reports/subscriptions/{id}', async () => {
      mockGet.mockResolvedValue({ data: { id: 1, name: '月度报表' } })
      const result = await reportApi.getById(1)
      expect(mockGet).toHaveBeenCalledWith('/reports/subscriptions/1')
      expect(result).toEqual({ data: { id: 1, name: '月度报表' } })
    })

    it('create 调用 POST /reports/subscriptions', async () => {
      mockPost.mockResolvedValue({ data: { id: 1 } })
      const payload = { name: '新报表', config: {} }
      await reportApi.create(payload)
      expect(mockPost).toHaveBeenCalledWith('/reports/subscriptions', payload)
    })

    it('update 调用 PUT /reports/subscriptions/{id}', async () => {
      mockPut.mockResolvedValue({ data: { id: 1 } })
      await reportApi.update(1, { name: '更新' })
      expect(mockPut).toHaveBeenCalledWith('/reports/subscriptions/1', { name: '更新' })
    })

    it('delete 调用 DELETE /reports/subscriptions/{id}', async () => {
      mockDelete.mockResolvedValue({})
      await reportApi.delete(1)
      expect(mockDelete).toHaveBeenCalledWith('/reports/subscriptions/1')
    })

    it('toggle 调用 POST /reports/subscriptions/{id}/toggle', async () => {
      mockPost.mockResolvedValue({ data: { enabled: true } })
      await reportApi.toggle(1)
      expect(mockPost).toHaveBeenCalledWith('/reports/subscriptions/1/toggle')
    })
  })

  describe('generate & download', () => {
    it('generate 调用 POST /reports/generate', async () => {
      mockPost.mockResolvedValue({ data: { url: '/download/1' } })
      await reportApi.generate({ type: 'monthly', year: 2025 })
      expect(mockPost).toHaveBeenCalledWith('/reports/generate', { type: 'monthly', year: 2025 })
    })

    it('download 调用 GET /reports/{id}/download', async () => {
      mockGet.mockResolvedValue(new Blob(['test']))
      await reportApi.download(1)
      expect(mockGet).toHaveBeenCalledWith('/reports/1/download', { responseType: 'blob' })
    })
  })
})
