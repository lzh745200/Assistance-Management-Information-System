import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockPut, mockDel, mockApiRequest } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDel: vi.fn(),
  mockApiRequest: vi.fn(),
}))

// src/api/report.ts 使用命名导出 get/post/put/del/apiRequest（返回已解包的 body）
vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  put: mockPut,
  del: mockDel,
  apiRequest: mockApiRequest,
}))

import { reportApi } from '@/api/report'

describe('api/report', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('subscriptions', () => {
    it('list 调用 GET /reports/subscriptions', async () => {
      mockGet.mockResolvedValue({ items: [], total: 0 })
      await reportApi.list({ page: 1 })
      expect(mockGet).toHaveBeenCalledWith('/reports/subscriptions', { page: 1 })
    })

    it('list 无参时调用', async () => {
      mockGet.mockResolvedValue({ items: [], total: 0 })
      await reportApi.list()
      expect(mockGet).toHaveBeenCalledWith('/reports/subscriptions', undefined)
    })

    it('getById 调用 GET /reports/subscriptions/{id}', async () => {
      mockGet.mockResolvedValue({ id: 1, name: '月度报表' })
      const result = await reportApi.getById(1)
      expect(mockGet).toHaveBeenCalledWith('/reports/subscriptions/1')
      expect(result).toEqual({ id: 1, name: '月度报表' })
    })

    it('create 调用 POST /reports/subscriptions', async () => {
      mockPost.mockResolvedValue({ id: 1 })
      const payload = { name: '新报表', config: {} }
      await reportApi.create(payload)
      expect(mockPost).toHaveBeenCalledWith('/reports/subscriptions', payload)
    })

    it('update 调用 PUT /reports/subscriptions/{id}', async () => {
      mockPut.mockResolvedValue({ id: 1 })
      await reportApi.update(1, { name: '更新' })
      expect(mockPut).toHaveBeenCalledWith('/reports/subscriptions/1', { name: '更新' })
    })

    it('delete 调用 DELETE /reports/subscriptions/{id}', async () => {
      mockDel.mockResolvedValue({})
      await reportApi.delete(1)
      expect(mockDel).toHaveBeenCalledWith('/reports/subscriptions/1')
    })

    it('toggle 调用 POST /reports/subscriptions/{id}/toggle', async () => {
      mockPost.mockResolvedValue({ enabled: true })
      await reportApi.toggle(1)
      expect(mockPost).toHaveBeenCalledWith('/reports/subscriptions/1/toggle')
    })
  })

  describe('generate & download', () => {
    it('generate 调用 POST /reports/generate', async () => {
      mockPost.mockResolvedValue({ url: '/download/1' })
      await reportApi.generate({ type: 'monthly', year: 2025 })
      expect(mockPost).toHaveBeenCalledWith('/reports/generate', { type: 'monthly', year: 2025 })
    })

    it('download 调用 GET /reports/{id}/download', async () => {
      mockApiRequest.mockResolvedValue(new Blob(['test']))
      await reportApi.download(1)
      expect(mockApiRequest).toHaveBeenCalledWith({
        method: 'GET',
        url: '/reports/1/download',
        responseType: 'blob',
      })
    })
  })
})
