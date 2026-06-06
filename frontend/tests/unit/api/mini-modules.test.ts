import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockRequest = vi.fn()

vi.mock('@/utils/request', () => ({
  default: mockRequest,
}))

import { rbacApi } from '@/api/rbac'
import { reportApi } from '@/api/report'
import { globalSearch } from '@/api/search'

describe('api/rbac', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getRoles 调用 GET /rbac/roles', () => {
    mockRequest.get = vi.fn()
    rbacApi.getRoles()
    expect(mockRequest.get).toHaveBeenCalledWith('/rbac/roles')
  })

  it('getPermissions 调用 GET /rbac/permissions', () => {
    mockRequest.get = vi.fn()
    rbacApi.getPermissions()
    expect(mockRequest.get).toHaveBeenCalledWith('/rbac/permissions')
  })

  it('assignRole 调用 POST /rbac/assign', () => {
    mockRequest.post = vi.fn()
    rbacApi.assignRole(1, 2)
    expect(mockRequest.post).toHaveBeenCalledWith('/rbac/assign', { userId: 1, roleId: 2 })
  })
})

describe('api/report', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('list 调用 GET /reports', () => {
    mockRequest.get = vi.fn()
    reportApi.list({ page: 1 })
    expect(mockRequest.get).toHaveBeenCalledWith('/reports', { params: { page: 1 } })
  })

  it('list 无参', () => {
    mockRequest.get = vi.fn()
    reportApi.list()
    expect(mockRequest.get).toHaveBeenCalledWith('/reports', { params: undefined })
  })

  it('generate 调用 POST /reports/generate', () => {
    mockRequest.post = vi.fn()
    reportApi.generate({ type: 'monthly' })
    expect(mockRequest.post).toHaveBeenCalledWith('/reports/generate', { type: 'monthly' })
  })

  it('download 调用 GET /reports/{id}/download with blob responseType', () => {
    mockRequest.get = vi.fn()
    reportApi.download(5)
    expect(mockRequest.get).toHaveBeenCalledWith('/reports/5/download', { responseType: 'blob' })
  })
})

describe('api/search', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('globalSearch 调用 GET /search with q + limit', async () => {
    mockRequest.get = vi.fn().mockResolvedValue({ data: { total: 1, items: [] } })
    await globalSearch('test', 10)
    expect(mockRequest.get).toHaveBeenCalledWith('/search', { params: { q: 'test', limit: 10 } })
  })

  it('globalSearch 默认 limit=20', async () => {
    mockRequest.get = vi.fn().mockResolvedValue({ data: { total: 0, items: [] } })
    await globalSearch('hello')
    expect(mockRequest.get).toHaveBeenCalledWith('/search', { params: { q: 'hello', limit: 20 } })
  })

  it('globalSearch 返回 response.data', async () => {
    const response = { total: 2, items: [{ id: 1, type: 'village', title: 'test', link: '/v/1' }] }
    mockRequest.get = vi.fn().mockResolvedValue({ data: response })
    const result = await globalSearch('test')
    expect(result).toEqual(response)
  })
})
