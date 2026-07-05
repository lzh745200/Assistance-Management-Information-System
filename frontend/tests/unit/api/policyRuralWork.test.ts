import { describe, it, expect, vi, beforeEach } from 'vitest'

// 源代码（ruralWork.ts 等）会对 api.get/post/put/delete 的返回值链式调用 .then(r => r.data)，
// 因此 mock 必须返回 Promise，否则会抛 "Cannot read properties of undefined (reading 'then')"。
const mockGet = vi.fn().mockResolvedValue({ data: {} })
const mockPost = vi.fn().mockResolvedValue({ data: {} })
const mockPut = vi.fn().mockResolvedValue({ data: {} })
const mockDelete = vi.fn().mockResolvedValue({ data: {} })

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
  parseContentDisposition: (_headers: any, fallback: string) => fallback,
  downloadBlob: vi.fn(),
}))

import {
  getLevelOptions,
  getPolicyTypes,
  searchPolicies,
  getPolicyCategories,
  getPolicyStats,
  getPolicies,
  getPolicy,
  createPolicy,
  updatePolicy,
  deletePolicy,
  importPolicies,
  exportPolicies,
  exportPoliciesPDF,
  exportPoliciesWPS,
  downloadImportTemplate,
  getCategoryLabel,
  getLevelLabel,
  getStatusLabel,
  getStatusColor,
} from '@/api/policy'

import {
  getRuralWorks,
  createRuralWork,
  updateRuralWork,
  deleteRuralWork,
  generateWorkReport,
  ruralWorkApi,
} from '@/api/ruralWork'

describe('api/policy', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getLevelOptions', () => {
    getLevelOptions()
    expect(mockGet).toHaveBeenCalledWith('/policies/options/levels')
  })
  it('getPolicyTypes', () => {
    getPolicyTypes()
    expect(mockGet).toHaveBeenCalledWith('/policies/options/levels')
  })
  it('searchPolicies GET /policies/search with q', () => {
    searchPolicies('农业')
    expect(mockGet).toHaveBeenCalledWith('/policies/search', { params: { q: '农业' } })
  })
  it('getPolicyCategories', () => {
    getPolicyCategories()
    expect(mockGet).toHaveBeenCalledWith('/policies/categories')
  })
  it('getPolicyStats', () => {
    getPolicyStats()
    expect(mockGet).toHaveBeenCalledWith('/policies/statistics')
  })
  it('getPolicies GET /policies', () => {
    getPolicies({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/policies', { params: { page: 1 } })
  })
  it('getPolicy GET /policies/{id}', () => {
    getPolicy(1)
    expect(mockGet).toHaveBeenCalledWith('/policies/1')
  })
  it('createPolicy POST /policies', () => {
    createPolicy({ title: 'X' })
    expect(mockPost).toHaveBeenCalledWith('/policies', { title: 'X' })
  })
  it('updatePolicy PUT /policies/{id}', () => {
    updatePolicy(1, { title: 'Y' })
    expect(mockPut).toHaveBeenCalledWith('/policies/1', { title: 'Y' })
  })
  it('deletePolicy DELETE /policies/{id}', () => {
    deletePolicy(1)
    expect(mockDelete).toHaveBeenCalledWith('/policies/1')
  })

  it('importPolicies POST FormData', () => {
    const file = new File(['x'], 'a.xlsx')
    importPolicies(file)
    const [url, fd, config] = mockPost.mock.calls[0]
    expect(url).toBe('/policies/import')
    expect(fd).toBeInstanceOf(FormData)
    expect(fd.get('file')).toBe(file)
    expect(config.headers['Content-Type']).toBe('multipart/form-data')
  })

  describe('export 系列触发下载', () => {
    beforeEach(() => {
      vi.clearAllMocks()
      mockGet.mockResolvedValue({ data: new Blob(['x']) })
      const realAnchor = (globalThis as any).document.createElement('a')
      realAnchor.click = vi.fn()
      const realCreate = (globalThis as any).document.createElement.bind((globalThis as any).document)
      ;(globalThis as any).document.createElement = (tag: any) => {
        if (tag === 'a') return realAnchor
        return realCreate(tag)
      }
    })

    it('exportPolicies -> xlsx', async () => {
      await exportPolicies({ page: 1 })
      expect(mockGet).toHaveBeenCalledWith('/policies/export/excel', { params: { page: 1 }, responseType: 'blob' })
    })
    it('exportPoliciesPDF -> pdf', async () => {
      await exportPoliciesPDF()
      expect(mockGet).toHaveBeenCalledWith('/policies/export/pdf', { params: undefined, responseType: 'blob' })
    })
    it('exportPoliciesWPS -> wps', async () => {
      await exportPoliciesWPS()
      expect(mockGet).toHaveBeenCalledWith('/policies/export/wps', { params: undefined, responseType: 'blob' })
    })
    it('downloadImportTemplate', async () => {
      await downloadImportTemplate()
      expect(mockGet).toHaveBeenCalledWith('/import/template', { params: { entity_type: 'policy' }, responseType: 'blob' })
    })
  })

  describe('label helpers', () => {
    it('getCategoryLabel 未知 cat 回退', () => {
      expect(getCategoryLabel('xxx')).toBe('xxx')
    })
    it('getLevelLabel 未知 level 回退', () => {
      expect(getLevelLabel('xxx')).toBe('xxx')
    })
    it('getStatusLabel 未知 status 回退', () => {
      expect(getStatusLabel('xxx')).toBe('xxx')
    })
    it('getStatusColor 未知 status 默认 info', () => {
      expect(getStatusColor('xxx')).toBe('info')
    })
  })
})

describe('api/ruralWork', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getRuralWorks GET', () => {
    getRuralWorks({ status: 'pending' })
    expect(mockGet).toHaveBeenCalledWith('/rural-works', { params: { status: 'pending' } })
  })
  it('createRuralWork POST', () => {
    createRuralWork({ title: 'W' })
    expect(mockPost).toHaveBeenCalledWith('/rural-works', { title: 'W' })
  })
  it('updateRuralWork PUT', () => {
    updateRuralWork(1, { title: 'W2' })
    expect(mockPut).toHaveBeenCalledWith('/rural-works/1', { title: 'W2' })
  })
  it('deleteRuralWork DELETE', () => {
    deleteRuralWork(1)
    expect(mockDelete).toHaveBeenCalledWith('/rural-works/1')
  })
  it('generateWorkReport GET /rural-works/report/generate', () => {
    generateWorkReport({ year: 2026 })
    expect(mockGet).toHaveBeenCalledWith('/rural-works/report/generate', { params: { year: 2026 } })
  })

  it('ruralWorkApi.list / get / create / update / delete / generateWorkReport 转发', () => {
    ruralWorkApi.list({ p: 1 })
    ruralWorkApi.get(1)
    ruralWorkApi.create({ x: 1 })
    ruralWorkApi.update(1, { y: 2 })
    ruralWorkApi.delete(1)
    ruralWorkApi.generateWorkReport({ q: 9 })
    expect(mockGet).toHaveBeenCalledTimes(3)
    expect(mockPost).toHaveBeenCalledTimes(1)
    expect(mockPut).toHaveBeenCalledTimes(1)
    expect(mockDelete).toHaveBeenCalledTimes(1)
  })
})
