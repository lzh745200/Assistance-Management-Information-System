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

import { fundApi } from '@/api/funds'

describe('api/funds', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('CRUD', () => {
    it('list 调用 GET /funds', async () => {
      mockGet.mockResolvedValue({ data: { items: [], total: 0 } })
      await fundApi.list({ page: 1 })
      expect(mockGet).toHaveBeenCalledWith('/funds', { params: { page: 1 } })
    })

    it('list 无参时 params=undefined', async () => {
      mockGet.mockResolvedValue({ data: { items: [], total: 0 } })
      await fundApi.list()
      expect(mockGet).toHaveBeenCalledWith('/funds', { params: undefined })
    })

    it('getById 调用 GET /funds/{id}', async () => {
      mockGet.mockResolvedValue({ data: { id: 1, amount: 100 } })
      const result = await fundApi.getById(1)
      expect(mockGet).toHaveBeenCalledWith('/funds/1')
      expect(result).toEqual({ id: 1, amount: 100 })
    })

    it('create 调用 POST /funds', async () => {
      mockPost.mockResolvedValue({ data: { id: 1 } })
      await fundApi.create({ amount: 100 })
      expect(mockPost).toHaveBeenCalledWith('/funds', { amount: 100 })
    })

    it('update 调用 PUT /funds/{id}', async () => {
      mockPut.mockResolvedValue({ data: { id: 1, amount: 200 } })
      await fundApi.update(1, { amount: 200 })
      expect(mockPut).toHaveBeenCalledWith('/funds/1', { amount: 200 })
    })

    it('delete 调用 DELETE /funds/{id}', async () => {
      mockDelete.mockResolvedValue({ data: { message: 'ok' } })
      await fundApi.delete(1)
      expect(mockDelete).toHaveBeenCalledWith('/funds/1')
    })
  })

  describe('工作流', () => {
    it('approve 调用 POST /funds/{id}/approve', async () => {
      mockPost.mockResolvedValue({ data: {} })
      await fundApi.approve(1, { opinion: 'ok' })
      expect(mockPost).toHaveBeenCalledWith('/funds/1/approve', { opinion: 'ok' })
    })

    it('approve 无 data 时传空对象', async () => {
      mockPost.mockResolvedValue({ data: {} })
      await fundApi.approve(1)
      expect(mockPost).toHaveBeenCalledWith('/funds/1/approve', {})
    })

    it('reject 调用 POST /funds/{id}/reject', async () => {
      mockPost.mockResolvedValue({ data: {} })
      await fundApi.reject(1, { opinion: 'no' })
      expect(mockPost).toHaveBeenCalledWith('/funds/1/reject', { opinion: 'no' })
    })

    it('allocate 调用 POST /funds/{id}/allocate', async () => {
      mockPost.mockResolvedValue({ data: {} })
      await fundApi.allocate(1, { allocated_amount: 5000 })
      expect(mockPost).toHaveBeenCalledWith('/funds/1/allocate', { allocated_amount: 5000 })
    })

    it('startUse 调用 POST /funds/{id}/start-use', async () => {
      mockPost.mockResolvedValue({ data: {} })
      await fundApi.startUse(1)
      expect(mockPost).toHaveBeenCalledWith('/funds/1/start-use', {})
    })

    it('complete 调用 POST /funds/{id}/complete', async () => {
      mockPost.mockResolvedValue({ data: {} })
      await fundApi.complete(1)
      expect(mockPost).toHaveBeenCalledWith('/funds/1/complete', {})
    })

    it('audit 调用 POST /funds/{id}/audit', async () => {
      mockPost.mockResolvedValue({ data: {} })
      await fundApi.audit(1, { audit_result: 'pass' })
      expect(mockPost).toHaveBeenCalledWith('/funds/1/audit', { audit_result: 'pass' })
    })
  })

  describe('统计', () => {
    it('statisticsOverview 调用 GET /funds/statistics/overview', async () => {
      mockGet.mockResolvedValue({ data: {} })
      await fundApi.statisticsOverview()
      expect(mockGet).toHaveBeenCalledWith('/funds/statistics/overview')
    })

    it('statisticsMultiDimension 带 params', async () => {
      mockGet.mockResolvedValue({ data: {} })
      await fundApi.statisticsMultiDimension({ year: 2024 })
      expect(mockGet).toHaveBeenCalledWith(
        '/funds/statistics/multi-dimension',
        { params: { year: 2024 } },
      )
    })
  })

  describe('附件', () => {
    it('listAttachments 调用 GET /funds/{id}/attachments', async () => {
      mockGet.mockResolvedValue({ data: { items: [], total: 0 } })
      await fundApi.listAttachments(1)
      expect(mockGet).toHaveBeenCalledWith('/funds/1/attachments')
    })

    it('deleteAttachment 调用 DELETE /funds/attachments/{id}', async () => {
      mockDelete.mockResolvedValue({ data: {} })
      await fundApi.deleteAttachment(5)
      expect(mockDelete).toHaveBeenCalledWith('/funds/attachments/5')
    })

    it('getPreviewUrl 返回 /api/v1/funds/attachments/{id}/preview', () => {
      expect(fundApi.getPreviewUrl(5)).toBe('/api/v1/funds/attachments/5/preview')
    })

    it('getDownloadUrl 返回 /api/v1/funds/attachments/{id}/download', () => {
      expect(fundApi.getDownloadUrl(5)).toBe('/api/v1/funds/attachments/5/download')
    })
  })

  describe('预算', () => {
    it('listBudgets 调用 GET /fund-budgets', async () => {
      mockGet.mockResolvedValue({ data: { items: [], total: 0 } })
      await fundApi.listBudgets(2024)
      expect(mockGet).toHaveBeenCalledWith('/fund-budgets', { params: { year: 2024 } })
    })

    it('createBudget 调用 POST /fund-budgets', async () => {
      mockPost.mockResolvedValue({ data: {} })
      await fundApi.createBudget({ year: 2024, category: 'project', budget_amount: 1000, used_amount: 200 })
      expect(mockPost).toHaveBeenCalled()
    })

    it('updateBudget 调用 PUT /fund-budgets/{id}', async () => {
      mockPut.mockResolvedValue({ data: {} })
      await fundApi.updateBudget(1, { year: 2024 })
      expect(mockPut).toHaveBeenCalledWith('/fund-budgets/1', { year: 2024 })
    })

    it('deleteBudget 调用 DELETE /fund-budgets/{id}', async () => {
      mockDelete.mockResolvedValue({ data: {} })
      await fundApi.deleteBudget(1)
      expect(mockDelete).toHaveBeenCalledWith('/fund-budgets/1')
    })
  })

  describe('exportList', () => {
    it('调用 GET /funds/export with blob responseType', async () => {
      mockGet.mockResolvedValue({ data: new Blob(['test']) })
      const createObjectURL = vi.fn(() => 'blob:fake')
      const revokeObjectURL = vi.fn()
      const click = vi.fn()
      const realCreate = URL.createObjectURL
      const realRevoke = URL.revokeObjectURL
      URL.createObjectURL = createObjectURL
      URL.revokeObjectURL = revokeObjectURL
      const a = document.createElement('a')
      a.click = click
      const realDocCreate = document.createElement.bind(document)
      vi.spyOn(document, 'createElement').mockImplementation((tag: any) => {
        if (tag === 'a') return a
        return realDocCreate(tag)
      })
      await fundApi.exportList({ type: 'project' })
      expect(mockGet).toHaveBeenCalledWith('/funds/export', {
        params: { type: 'project' },
        responseType: 'blob',
      })
      URL.createObjectURL = realCreate
      URL.revokeObjectURL = realRevoke
    })
  })
})
