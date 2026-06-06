import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockDelete = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}))
vi.mock('@/api/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}))

import {
  getDataPackages,
  getDataPackage,
  exportDataPackage,
  importDataPackage,
  validateDataPackage,
  previewDataPackage,
  confirmImport,
  downloadDataPackage,
  deleteDataPackage,
  getPackageHistory,
  getDownloadUrl,
} from '@/api/dataPackage'

describe('api/dataPackage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getDataPackages GET /data-packages', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await getDataPackages({ page: 1, page_size: 10 })
    expect(mockGet).toHaveBeenCalledWith('/data-packages', { params: { page: 1, page_size: 10 } })
  })

  it('getDataPackage GET /data-packages/{id}', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 1 } })
    await getDataPackage(1)
    expect(mockGet).toHaveBeenCalledWith('/data-packages/1')
  })

  it('exportDataPackage POST /data-packages/export', async () => {
    mockPost.mockResolvedValueOnce({ data: { package_id: 1 } })
    await exportDataPackage({ data_types: ['village'] } as any)
    expect(mockPost).toHaveBeenCalledWith('/data-packages/export', { data_types: ['village'] })
  })

  it('importDataPackage POST FormData (no orgId)', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    const file = new File(['x'], 'a.zip')
    await importDataPackage(file)
    const [url, fd, config] = mockPost.mock.calls[0]
    expect(url).toBe('/data-packages/import')
    expect(fd).toBeInstanceOf(FormData)
    expect(fd.get('file')).toBe(file)
    expect(config.params).toEqual({})
    expect(config.headers['Content-Type']).toBe('multipart/form-data')
  })

  it('importDataPackage POST FormData (with orgId)', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    const file = new File(['x'], 'a.zip')
    await importDataPackage(file, 5)
    expect(mockPost.mock.calls[0][2].params).toEqual({ org_id: 5 })
  })

  it('validateDataPackage POST /data-packages/{id}/validate', async () => {
    mockPost.mockResolvedValueOnce({ data: { valid: true } })
    await validateDataPackage(3)
    expect(mockPost).toHaveBeenCalledWith('/data-packages/3/validate')
  })

  it('previewDataPackage GET /data-packages/{id}/preview', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await previewDataPackage(3)
    expect(mockGet).toHaveBeenCalledWith('/data-packages/3/preview')
  })

  it('confirmImport POST /data-packages/{id}/confirm', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await confirmImport(3, { strategy: 'merge' } as any)
    expect(mockPost).toHaveBeenCalledWith('/data-packages/3/confirm', { strategy: 'merge' })
  })

  it('confirmImport 无 data 时用 {}', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await confirmImport(3)
    expect(mockPost).toHaveBeenCalledWith('/data-packages/3/confirm', {})
  })

  it('downloadDataPackage GET blob', async () => {
    mockGet.mockResolvedValueOnce({ data: new Blob(['x']) })
    const result = await downloadDataPackage(3)
    expect(mockGet).toHaveBeenCalledWith('/data-packages/3/download', { responseType: 'blob' })
    expect(result).toBeInstanceOf(Blob)
  })

  it('deleteDataPackage DELETE (no reason)', async () => {
    mockDelete.mockResolvedValueOnce({ data: { message: 'ok' } })
    await deleteDataPackage(3)
    expect(mockDelete).toHaveBeenCalledWith('/data-packages/3', { params: undefined })
  })

  it('deleteDataPackage DELETE (with reason)', async () => {
    mockDelete.mockResolvedValueOnce({ data: { message: 'ok' } })
    await deleteDataPackage(3, 'cleanup')
    expect(mockDelete).toHaveBeenCalledWith('/data-packages/3', { params: { reason: 'cleanup' } })
  })

  it('getPackageHistory GET /data-packages/{id}/history', async () => {
    mockGet.mockResolvedValueOnce({ data: { package_id: 1, items: [] } })
    await getPackageHistory(1, { page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/data-packages/1/history', { params: { page: 1 } })
  })

  it('getDownloadUrl 返回 URL 字符串', () => {
    const url = getDownloadUrl(5)
    expect(url).toMatch(/\/api\/v1\/data-packages\/5\/download$/)
  })
})
