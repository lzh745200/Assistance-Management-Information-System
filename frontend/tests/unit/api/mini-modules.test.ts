import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()

vi.mock('@/api/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
  },
}))

import { rbacApi } from '@/api/rbac'
import { reportApi } from '@/api/report'
import { globalSearch } from '@/api/search'

describe('api/rbac', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getRoles 调用 GET /rbac/roles', () => {
    rbacApi.getRoles()
    expect(mockGet).toHaveBeenCalledWith('/rbac/roles')
  })

  it('getPermissions 调用 GET /rbac/permissions', () => {
    rbacApi.getPermissions()
    expect(mockGet).toHaveBeenCalledWith('/rbac/permissions')
  })

  it('assignRole 调用 POST /rbac/assign/role', () => {
    rbacApi.assignRole(1, 2)
    expect(mockPost).toHaveBeenCalledWith('/rbac/assign/role', { user_id: 1, role_id: 2 })
  })
})

describe('api/report', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('list 调用 GET /reports', () => {
    reportApi.list({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/reports', { params: { page: 1 } })
  })

  it('list 无参', () => {
    reportApi.list()
    expect(mockGet).toHaveBeenCalledWith('/reports', { params: undefined })
  })

  it('generate 调用 POST /reports/generate', () => {
    reportApi.generate({ type: 'monthly' })
    expect(mockPost).toHaveBeenCalledWith('/reports/generate', { type: 'monthly' })
  })

  it('download 调用 GET /reports/{id}/download with blob responseType', () => {
    reportApi.download(5)
    expect(mockGet).toHaveBeenCalledWith('/reports/5/download', { responseType: 'blob' })
  })
})

describe('api/search', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('globalSearch 调用 GET /search with q + limit', async () => {
    mockGet.mockResolvedValue({ data: { total: 1, items: [] } })
    await globalSearch('test', 10)
    expect(mockGet).toHaveBeenCalledWith('/search', { params: { q: 'test', limit: 10 } })
  })

  it('globalSearch 默认 limit=20', async () => {
    mockGet.mockResolvedValue({ data: { total: 0, items: [] } })
    await globalSearch('hello')
    expect(mockGet).toHaveBeenCalledWith('/search', { params: { q: 'hello', limit: 20 } })
  })

  it('globalSearch 返回 response.data', async () => {
    const response = { total: 2, items: [{ id: 1, type: 'village', title: 'test', link: '/v/1' }] }
    mockGet.mockResolvedValue({ data: response })
    const result = await globalSearch('test')
    expect(result).toEqual(response)
  })
})
